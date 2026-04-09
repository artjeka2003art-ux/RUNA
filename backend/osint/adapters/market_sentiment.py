"""Investment sentiment adapter: Fear & Greed Index via alternative.me.

Provides a single structured sentiment signal for crypto market state.
Free API, no auth required.

Endpoint: https://api.alternative.me/fng/?limit=2
Returns current + previous day's Fear & Greed value (0-100) and classification.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from backend.osint.models import ExternalSignal, FreshnessLabel

logger = logging.getLogger(__name__)

_FNG_URL = "https://api.alternative.me/fng/?limit=2"
_TIMEOUT = 6.0
_CACHE_TTL = 3600  # 1 hour — FnG updates once per day

# Simple in-memory TTL cache
_fng_cache: tuple[float, dict | None] | None = None


# ── Classification labels ────────────────────────────────────────────

_SENTIMENT_RU: dict[str, str] = {
    "Extreme Fear": "Крайний страх",
    "Fear": "Страх",
    "Neutral": "Нейтрально",
    "Greed": "Жадность",
    "Extreme Greed": "Крайняя жадность",
}


def _direction_label(current: int, previous: int | None) -> str:
    """Describe sentiment trajectory."""
    if previous is None:
        return ""
    delta = current - previous
    if abs(delta) < 3:
        return "без изменений"
    if delta > 10:
        return "резкий сдвиг к жадности"
    if delta > 0:
        return "сдвиг к жадности"
    if delta < -10:
        return "резкий сдвиг к страху"
    return "сдвиг к страху"


def _risk_interpretation(value: int) -> str:
    """Decision-relevant interpretation of FnG value."""
    if value <= 20:
        return ("Рынок в состоянии крайнего страха. "
                "Исторически это часто совпадает с локальными минимумами — "
                "потенциальная возможность для покупки при наличии горизонта 1+ год. "
                "Но также может сигнализировать о дальнейшем падении.")
    if value <= 35:
        return ("Рынок в состоянии страха. "
                "Участники рынка настроены пессимистично. "
                "Повышенная волатильность вероятна.")
    if value <= 55:
        return ("Рынок в нейтральном состоянии. "
                "Нет выраженного перекоса — решение зависит от личных факторов больше, чем от timing.")
    if value <= 75:
        return ("Рынок в состоянии жадности. "
                "Участники рынка оптимистичны, но исторически зона повышенного риска коррекции.")
    return ("Рынок в состоянии крайней жадности. "
            "Исторически это часто совпадает с локальными максимумами — "
            "высокий риск коррекции. Входить на пике жадности — повышенный риск.")


# ── Fetch + convert ──────────────────────────────────────────────────

async def fetch_fear_greed() -> dict | None:
    """Fetch Fear & Greed Index. Uses 1h TTL cache since FnG updates daily."""
    global _fng_cache
    now = time.monotonic()

    if _fng_cache and now - _fng_cache[0] < _CACHE_TTL:
        logger.debug("FnG cache hit")
        return _fng_cache[1]

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_FNG_URL, headers={"Accept": "application/json"})
            if resp.status_code != 200:
                logger.warning("Fear & Greed API returned %d", resp.status_code)
                return _fng_cache[1] if _fng_cache else None
            data = resp.json()
            entries = data.get("data", [])
            if not entries:
                return _fng_cache[1] if _fng_cache else None
            current = entries[0]
            previous = entries[1] if len(entries) > 1 else None
            result = {"current": current, "previous": previous}
            _fng_cache = (now, result)
            return result
    except Exception:
        logger.warning("Fear & Greed fetch failed", exc_info=True)
        return _fng_cache[1] if _fng_cache else None


def fng_to_signal(data: dict) -> ExternalSignal:
    """Convert Fear & Greed API response to ExternalSignal."""
    current = data["current"]
    previous = data.get("previous")

    value = int(current.get("value", 50))
    classification = current.get("value_classification", "Neutral")
    classification_ru = _SENTIMENT_RU.get(classification, classification)

    prev_value = int(previous["value"]) if previous else None
    direction = _direction_label(value, prev_value)
    risk_note = _risk_interpretation(value)

    # Build snippet
    lines = [
        f"Crypto Fear & Greed Index: {value}/100 — {classification_ru}",
    ]
    if prev_value is not None:
        delta = value - prev_value
        sign = "+" if delta > 0 else ""
        lines.append(f"Вчера: {prev_value}/100 ({sign}{delta}, {direction})")
    lines.append(f"Интерпретация: {risk_note}")

    snippet = "\n".join(lines)

    # Timestamp
    ts = None
    try:
        ts = datetime.fromtimestamp(int(current.get("timestamp", 0)), tz=timezone.utc)
    except Exception:
        pass

    # Why it matters — decision-specific
    why = (
        f"Индекс Fear & Greed = {value} ({classification_ru}) показывает общее настроение крипторынка. "
        f"Это влияет на timing входа/выхода: {_risk_interpretation(value)[:100]}"
    )

    return ExternalSignal(
        signal_type="market_sentiment",
        source_type="api_data",
        source_name="Alternative.me Fear & Greed Index",
        title=f"Crypto Fear & Greed: {value}/100 — {classification_ru}",
        url="https://alternative.me/crypto/fear-and-greed-index/",
        snippet=snippet,
        timestamp=ts,
        freshness_label=FreshnessLabel.fresh,
        relevance_score=0.90,
        quality_score=0.85,
        why_it_matters=why,
    )


# ── Public interface ─────────────────────────────────────────────────

async def get_sentiment_signals() -> list[ExternalSignal]:
    """Fetch crypto market sentiment signal. Returns empty list on failure."""
    data = await fetch_fear_greed()
    if data is None:
        return []
    try:
        signal = fng_to_signal(data)
        logger.info("Sentiment adapter: FnG=%s", signal.title)
        return [signal]
    except Exception:
        logger.warning("Sentiment signal construction failed", exc_info=True)
        return []
