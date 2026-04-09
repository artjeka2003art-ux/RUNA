"""Investment signal fusion: cross-interpret market data + sentiment + news signals.

Pure functions — no API calls, no side effects.
Takes existing ExternalSignal list, produces structured fusion insights
that help synthesis build stronger investment reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.osint.models import ExternalSignal


# ── Fusion result ────────────────────────────────────────────────────

@dataclass
class InvestmentFusion:
    """Derived investment insights from cross-referencing signals."""

    market_regime: str = ""          # e.g. "risk-off", "risk-on", "uncertain"
    regime_confidence: str = ""      # "high" | "medium" | "low"
    signal_alignment: str = ""       # "aligned_bullish", "aligned_bearish", "conflicting", "insufficient"
    alignment_detail: str = ""       # human explanation
    conditions_supporting_entry: list[str] = field(default_factory=list)
    conditions_to_wait: list[str] = field(default_factory=list)
    key_risk: str = ""
    key_opportunity: str = ""
    timing_note: str = ""

    def to_synthesis_block(self) -> str:
        """Format fusion for LLM synthesis prompt."""
        lines = [
            "## Совместная интерпретация investment сигналов (fusion)",
            "",
            f"**Market regime:** {self.market_regime} (уверенность: {self.regime_confidence})",
            f"**Согласованность сигналов:** {self.alignment_detail}",
        ]

        if self.key_opportunity:
            lines.append(f"**Возможность:** {self.key_opportunity}")
        if self.key_risk:
            lines.append(f"**Ключевой риск:** {self.key_risk}")
        if self.timing_note:
            lines.append(f"**Timing:** {self.timing_note}")

        if self.conditions_supporting_entry:
            lines.append("\n**Условия, поддерживающие вход:**")
            for c in self.conditions_supporting_entry:
                lines.append(f"  + {c}")

        if self.conditions_to_wait:
            lines.append("\n**Условия для ожидания:**")
            for c in self.conditions_to_wait:
                lines.append(f"  − {c}")

        lines.append("")
        lines.append(
            "ВАЖНО ДЛЯ SYNTHESIS: используй эту интерпретацию в most_likely_outcome, "
            "main_risks, leverage_factors и confidence_reason. "
            "Не игнорируй signal conflicts — отрази их как uncertainty."
        )

        return "\n".join(lines)


# ── Signal extraction helpers ────────────────────────────────────────

def _find_signal(signals: list[ExternalSignal], signal_type: str) -> ExternalSignal | None:
    for s in signals:
        if s.signal_type == signal_type:
            return s
    return None


def _find_all(signals: list[ExternalSignal], signal_type: str) -> list[ExternalSignal]:
    return [s for s in signals if s.signal_type == signal_type]


def _extract_price_change(market_sig: ExternalSignal) -> tuple[float | None, float | None]:
    """Extract 24h and 7d percentage changes from market signal snippet."""
    change_24h = None
    change_7d = None
    for line in market_sig.snippet.splitlines():
        line_lower = line.lower()
        if "24ч" in line_lower or "24h" in line_lower:
            change_24h = _extract_pct(line)
        elif "7д" in line_lower or "7d" in line_lower:
            change_7d = _extract_pct(line)
    return change_24h, change_7d


def _extract_pct(text: str) -> float | None:
    """Extract first percentage value from text like '+3.0%' or '-5.2%'."""
    import re
    m = re.search(r"([+-]?\d+\.?\d*)%", text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _extract_fng_value(sentiment_sig: ExternalSignal) -> int | None:
    """Extract Fear & Greed numeric value from sentiment signal."""
    import re
    m = re.search(r"(\d+)/100", sentiment_sig.title)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


# ── Fusion logic ─────────────────────────────────────────────────────

def fuse_investment_signals(signals: list[ExternalSignal]) -> InvestmentFusion | None:
    """Cross-interpret investment signals and produce derived insights.

    Returns None if there are no structured signals to fuse.
    """
    market_signals = _find_all(signals, "market_movement")
    sentiment_sig = _find_signal(signals, "market_sentiment")

    # Need at least one structured signal
    if not market_signals and not sentiment_sig:
        return None

    fusion = InvestmentFusion()

    # ── Extract raw values ──
    # Use first market signal for primary asset
    price_changes: list[tuple[str, float | None, float | None]] = []
    for ms in market_signals:
        c24, c7d = _extract_price_change(ms)
        # Extract asset name from title
        name = ms.title.replace("Market snapshot: ", "")
        price_changes.append((name, c24, c7d))

    fng_value = _extract_fng_value(sentiment_sig) if sentiment_sig else None

    # Primary asset changes (first one)
    primary_24h = price_changes[0][1] if price_changes else None
    primary_7d = price_changes[0][2] if price_changes else None

    # ── Determine market regime ──
    fusion.market_regime, fusion.regime_confidence = _determine_regime(
        primary_24h, primary_7d, fng_value,
    )

    # ── Determine signal alignment ──
    fusion.signal_alignment, fusion.alignment_detail = _determine_alignment(
        primary_24h, primary_7d, fng_value, price_changes,
    )

    # ── Derive conditions ──
    fusion.conditions_supporting_entry, fusion.conditions_to_wait = _derive_conditions(
        primary_24h, primary_7d, fng_value, fusion.market_regime,
    )

    # ── Key risk & opportunity ──
    fusion.key_risk, fusion.key_opportunity = _derive_risk_opportunity(
        primary_24h, primary_7d, fng_value, fusion.market_regime,
    )

    # ── Timing note ──
    fusion.timing_note = _derive_timing(
        primary_24h, primary_7d, fng_value, fusion.signal_alignment,
    )

    return fusion


def _determine_regime(
    change_24h: float | None,
    change_7d: float | None,
    fng: int | None,
) -> tuple[str, str]:
    """Determine market regime from price action + sentiment."""

    # Score approach: accumulate bullish/bearish signals
    bull = 0
    bear = 0
    data_points = 0

    if change_24h is not None:
        data_points += 1
        if change_24h > 2:
            bull += 2
        elif change_24h > 0:
            bull += 1
        elif change_24h < -2:
            bear += 2
        elif change_24h < 0:
            bear += 1

    if change_7d is not None:
        data_points += 1
        if change_7d > 5:
            bull += 2
        elif change_7d > 0:
            bull += 1
        elif change_7d < -5:
            bear += 2
        elif change_7d < 0:
            bear += 1

    if fng is not None:
        data_points += 1
        if fng >= 70:
            bull += 2
        elif fng >= 55:
            bull += 1
        elif fng <= 25:
            bear += 2
        elif fng <= 40:
            bear += 1

    if data_points == 0:
        return "неопределён", "low"

    diff = bull - bear
    confidence = "high" if data_points >= 3 and abs(diff) >= 3 else (
        "medium" if data_points >= 2 and abs(diff) >= 2 else "low"
    )

    if diff >= 3:
        return "risk-on (бычий)", confidence
    if diff >= 1:
        return "умеренно бычий", confidence
    if diff <= -3:
        return "risk-off (медвежий)", confidence
    if diff <= -1:
        return "умеренно медвежий", confidence
    return "боковой / неопределённый", confidence


def _determine_alignment(
    change_24h: float | None,
    change_7d: float | None,
    fng: int | None,
    price_changes: list[tuple[str, float | None, float | None]],
) -> tuple[str, str]:
    """Check if price action and sentiment point same direction."""

    price_bullish = (change_24h is not None and change_24h > 1) or (change_7d is not None and change_7d > 3)
    price_bearish = (change_24h is not None and change_24h < -1) or (change_7d is not None and change_7d < -3)
    sent_bullish = fng is not None and fng >= 55
    sent_bearish = fng is not None and fng <= 40

    if price_bullish and sent_bullish:
        detail = "Цена растёт и sentiment позитивный — сигналы согласованы на рост"
        return "aligned_bullish", detail
    if price_bearish and sent_bearish:
        detail = "Цена падает и sentiment негативный — сигналы согласованы на снижение"
        return "aligned_bearish", detail
    if price_bullish and sent_bearish:
        detail = "Цена растёт, но sentiment негативный — потенциальный разворот или ловушка быков"
        return "conflicting", detail
    if price_bearish and sent_bullish:
        detail = "Цена падает, но sentiment позитивный — возможен отскок или дальнейшее падение"
        return "conflicting", detail

    # Check multi-asset divergence
    if len(price_changes) >= 2:
        dirs = []
        for name, c24, _ in price_changes:
            if c24 is not None:
                dirs.append((name, c24 > 0))
        if len(dirs) >= 2 and dirs[0][1] != dirs[1][1]:
            detail = f"{dirs[0][0]} и {dirs[1][0]} движутся в разных направлениях — рынок неоднороден"
            return "conflicting", detail

    if change_24h is None and fng is None:
        return "insufficient", "Недостаточно данных для оценки согласованности"

    return "neutral", "Нет выраженного направления — сигналы нейтральны"


def _derive_conditions(
    change_24h: float | None,
    change_7d: float | None,
    fng: int | None,
    regime: str,
) -> tuple[list[str], list[str]]:
    """Derive entry-supporting and wait conditions."""
    entry: list[str] = []
    wait: list[str] = []

    if fng is not None:
        if fng <= 25:
            entry.append(f"Extreme Fear (FnG={fng}) — исторически зона возможностей для долгосрочного входа")
        elif fng >= 75:
            wait.append(f"Extreme Greed (FnG={fng}) — исторически зона повышенного риска коррекции")

    if change_7d is not None:
        if change_7d < -15:
            entry.append(f"Значительная коррекция за неделю ({change_7d:+.1f}%) — цена ниже недавних уровней")
        elif change_7d > 20:
            wait.append(f"Резкий рост за неделю ({change_7d:+.1f}%) — риск фиксации прибыли")

    if change_24h is not None:
        if change_24h > 5:
            wait.append(f"Резкий дневной рост ({change_24h:+.1f}%) — вход на пике дня рискованнее")
        elif change_24h < -5:
            entry.append(f"Резкое дневное падение ({change_24h:+.1f}%) — возможность входа на просадке")

    if "risk-off" in regime:
        wait.append("Общий market regime медвежий — рынок не благоприятствует агрессивному входу")
    elif "risk-on" in regime:
        entry.append("Общий market regime бычий — рыночные условия благоприятны")

    return entry, wait


def _derive_risk_opportunity(
    change_24h: float | None,
    change_7d: float | None,
    fng: int | None,
    regime: str,
) -> tuple[str, str]:
    """Derive key risk and key opportunity."""
    risk = ""
    opportunity = ""

    if fng is not None and fng >= 75:
        risk = "Рынок в зоне крайней жадности — высокая вероятность коррекции в ближайшие недели"
    elif fng is not None and fng <= 20:
        opportunity = "Рынок в зоне крайнего страха — исторически выгодная точка для среднесрочного входа"

    if change_7d is not None and change_7d > 25 and not risk:
        risk = f"Актив вырос на {change_7d:+.1f}% за неделю — вход на таком росте значительно повышает риск просадки"
    if change_7d is not None and change_7d < -20 and not opportunity:
        opportunity = f"Актив упал на {change_7d:.1f}% за неделю — при фундаментальной силе актива это потенциальная точка входа"

    if not risk:
        if "risk-off" in regime:
            risk = "Медвежий режим рынка — давление продавцов может продолжиться"
        else:
            risk = "Волатильность крипторынка: значительные движения возможны в обе стороны"

    if not opportunity:
        if "risk-on" in regime:
            opportunity = "Бычий режим рынка — momentum на стороне покупателей"
        elif fng is not None and fng <= 40:
            opportunity = "Умеренный страх на рынке — цена может быть ниже справедливой"

    return risk, opportunity


def _derive_timing(
    change_24h: float | None,
    change_7d: float | None,
    fng: int | None,
    alignment: str,
) -> str:
    """Derive timing note."""
    if alignment == "conflicting":
        return ("Сигналы конфликтуют — moment uncertainty высокий. "
                "Если нет срочности, имеет смысл подождать более ясного сигнала "
                "или входить частями (DCA).")

    if fng is not None and fng <= 20:
        return ("Extreme Fear обычно длится 1-3 недели. "
                "Историческая закономерность: вход в зоне Fear при фундаментально сильном активе "
                "давал лучшие результаты на горизонте 6-12 месяцев.")

    if fng is not None and fng >= 80:
        return ("Extreme Greed часто предшествует коррекции на 10-30%. "
                "Если решение о входе принято, имеет смысл зафиксировать размер позиции "
                "и не добавлять на росте.")

    if change_24h is not None and abs(change_24h) > 5:
        return "Высокая внутридневная волатильность — рассмотри лимитный ордер вместо рыночного."

    return ""
