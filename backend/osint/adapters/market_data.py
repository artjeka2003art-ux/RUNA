"""Investment market data adapter: structured crypto/asset signals via CoinGecko.

Provides real-time price, 24h change, 7d change, market cap, and volume
for recognized crypto assets (BTC, ETH, and a handful of common ones).

Uses CoinGecko free API — no auth required, rate-limited to ~30 req/min.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone

import httpx

from backend.osint.models import ExternalSignal, FreshnessLabel

logger = logging.getLogger(__name__)

_COINGECKO_BASE = "https://api.coingecko.com/api/v3"
_TIMEOUT = 8.0
_CACHE_TTL = 60  # seconds — CoinGecko data refreshes ~every minute

# Simple in-memory TTL cache: key (sorted asset ids) → (timestamp, data)
_market_cache: dict[str, tuple[float, list[dict]]] = {}

# ── Asset recognition ────────────────────────────────────────────────

# Maps user-facing mentions → CoinGecko IDs
_ASSET_ALIASES: dict[str, str] = {
    # Bitcoin
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "биткоин": "bitcoin",
    "биткойн": "bitcoin",
    "битка": "bitcoin",
    # Ethereum
    "eth": "bitcoin",  # will fix below
    "ethereum": "ethereum",
    "эфир": "ethereum",
    "эфириум": "ethereum",
    # Solana
    "sol": "solana",
    "solana": "solana",
    "солана": "solana",
    # BNB
    "bnb": "binancecoin",
    # XRP
    "xrp": "ripple",
    "рипл": "ripple",
    # Dogecoin
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
    # Generic crypto
    "крипт": "_crypto_generic",
    "crypto": "_crypto_generic",
}

# Fix the ETH alias (was wrong above)
_ASSET_ALIASES["eth"] = "ethereum"

# Display names for synthesis
_DISPLAY_NAMES: dict[str, str] = {
    "bitcoin": "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)",
    "solana": "Solana (SOL)",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "dogecoin": "Dogecoin (DOGE)",
}


def detect_assets(question: str) -> list[str]:
    """Detect crypto asset CoinGecko IDs mentioned in a question.

    Returns list of CoinGecko IDs (e.g. ["bitcoin", "ethereum"]).
    For generic crypto mentions, defaults to ["bitcoin"].
    """
    q = question.lower().replace("ё", "е")
    found: list[str] = []
    seen: set[str] = set()

    for alias, cg_id in _ASSET_ALIASES.items():
        if alias in q and cg_id not in seen:
            if cg_id == "_crypto_generic":
                # Generic crypto mention — add BTC as default if nothing else found
                continue
            seen.add(cg_id)
            found.append(cg_id)

    # If nothing specific found but crypto is mentioned, default to bitcoin
    if not found:
        for generic in ["крипт", "crypto", "крипто", "монет", "coin"]:
            if generic in q:
                found.append("bitcoin")
                break

    return found


# ── CoinGecko API ────────────────────────────────────────────────────

async def fetch_market_data(asset_ids: list[str]) -> list[dict]:
    """Fetch market data from CoinGecko for given asset IDs.

    Uses in-memory TTL cache (60s) to reduce API calls and avoid rate limits.
    """
    if not asset_ids:
        return []

    cache_key = ",".join(sorted(asset_ids[:5]))
    now = time.monotonic()

    # Check cache
    cached = _market_cache.get(cache_key)
    if cached and now - cached[0] < _CACHE_TTL:
        logger.debug("CoinGecko cache hit for %s", cache_key)
        return cached[1]

    ids_str = ",".join(asset_ids[:5])
    url = (
        f"{_COINGECKO_BASE}/coins/markets"
        f"?vs_currency=usd"
        f"&ids={ids_str}"
        f"&order=market_cap_desc"
        f"&sparkline=false"
        f"&price_change_percentage=7d"
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers={"Accept": "application/json"})
            if resp.status_code == 429:
                logger.warning("CoinGecko rate limited")
                # Return stale cache if available
                return cached[1] if cached else []
            if resp.status_code != 200:
                logger.warning("CoinGecko returned %d", resp.status_code)
                return cached[1] if cached else []
            data = resp.json()
            _market_cache[cache_key] = (now, data)
            return data
    except Exception:
        logger.warning("CoinGecko fetch failed", exc_info=True)
        return cached[1] if cached else []


# ── Signal construction ──────────────────────────────────────────────

def _format_price(price: float) -> str:
    """Format price for display."""
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:.4f}"


def _format_change(pct: float | None) -> str:
    """Format percentage change."""
    if pct is None:
        return "н/д"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.1f}%"


def _direction_label(change_24h: float | None, change_7d: float | None) -> str:
    """Determine market direction label."""
    if change_24h is None:
        return "направление неизвестно"

    if change_7d is not None:
        # Use both for richer signal
        if change_24h > 3 and change_7d > 10:
            return "сильный рост"
        elif change_24h > 1 and change_7d > 3:
            return "умеренный рост"
        elif change_24h < -3 and change_7d < -10:
            return "сильное падение"
        elif change_24h < -1 and change_7d < -3:
            return "умеренное снижение"
        elif abs(change_24h) < 1 and abs(change_7d) < 3:
            return "боковое движение"
        elif change_24h > 0:
            return "лёгкий рост"
        else:
            return "лёгкое снижение"

    # Only 24h data
    if change_24h > 5:
        return "резкий рост"
    elif change_24h > 1:
        return "рост"
    elif change_24h < -5:
        return "резкое падение"
    elif change_24h < -1:
        return "снижение"
    return "стабильно"


def market_data_to_signals(market_data: list[dict]) -> list[ExternalSignal]:
    """Convert CoinGecko market data to ExternalSignal objects."""
    signals: list[ExternalSignal] = []

    for coin in market_data:
        cg_id = coin.get("id", "")
        name = _DISPLAY_NAMES.get(cg_id, coin.get("name", cg_id))
        price = coin.get("current_price")
        change_24h = coin.get("price_change_percentage_24h")
        change_7d = coin.get("price_change_percentage_7d_in_currency")
        market_cap = coin.get("market_cap")
        volume = coin.get("total_volume")
        last_updated = coin.get("last_updated", "")

        if price is None:
            continue

        direction = _direction_label(change_24h, change_7d)

        # Build structured snippet
        lines = [
            f"Текущая цена {name}: {_format_price(price)}",
            f"Изменение за 24ч: {_format_change(change_24h)} ({direction})",
        ]
        if change_7d is not None:
            lines.append(f"Изменение за 7д: {_format_change(change_7d)}")
        if market_cap:
            lines.append(f"Капитализация: ${market_cap / 1e9:.1f}B")
        if volume:
            lines.append(f"Объём торгов (24ч): ${volume / 1e9:.1f}B")

        snippet = "\n".join(lines)

        # Timestamp
        ts = None
        if last_updated:
            try:
                ts = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            except Exception:
                pass

        # Build why_it_matters
        why_parts = []
        if change_24h is not None and abs(change_24h) > 3:
            why_parts.append(f"значительное движение ({_format_change(change_24h)} за сутки)")
        if change_7d is not None and abs(change_7d) > 10:
            why_parts.append(f"выраженный недельный тренд ({_format_change(change_7d)})")
        if not why_parts:
            why_parts.append(f"актуальный market snapshot для оценки момента входа/выхода")
        why = f"Реальные рыночные данные {name}: {'; '.join(why_parts)}"

        signals.append(ExternalSignal(
            signal_type="market_movement",
            source_type="api_data",
            source_name="CoinGecko API",
            title=f"Market snapshot: {name}",
            url=f"https://www.coingecko.com/en/coins/{cg_id}",
            snippet=snippet,
            timestamp=ts,
            freshness_label=FreshnessLabel.fresh,
            relevance_score=0.95,  # Structured market data is highly relevant for investment
            quality_score=0.90,    # API data > web snippets
            why_it_matters=why,
        ))

    return signals


# ── Public interface ─────────────────────────────────────────────────

async def get_investment_signals(question: str) -> list[ExternalSignal]:
    """Detect assets in question, fetch market data, return signals.

    Returns empty list on any failure (graceful fallback).
    """
    assets = detect_assets(question)
    if not assets:
        return []

    logger.info("Market adapter: detected assets %s", assets)
    data = await fetch_market_data(assets)
    if not data:
        logger.info("Market adapter: no data returned for %s", assets)
        return []

    signals = market_data_to_signals(data)
    logger.info("Market adapter: produced %d signals", len(signals))
    return signals
