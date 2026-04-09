"""Investment allocation / exposure policy layer.

Takes InvestmentFusion + PersonalInvestmentConstraints + PersonalSuitability
and produces operational policy recommendation: action posture, exposure,
hard guards, and conditions for stronger entry.

Pure functions, no API calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .investment import InvestmentFusion
from .personal_investment import PersonalInvestmentConstraints, PersonalSuitability


ActionPosture = Literal[
    "avoid_now",
    "wait_for_clarity",
    "exploratory_entry",
    "small_dca",
    "normal_dca",
]

ExposurePosture = Literal[
    "no_exposure",
    "tiny",
    "small",
    "moderate",
]

ACTION_LABELS: dict[str, str] = {
    "avoid_now": "Воздержаться от входа",
    "wait_for_clarity": "Подождать более ясного сигнала",
    "exploratory_entry": "Пробный вход минимальной суммой",
    "small_dca": "Небольшой DCA (регулярные малые покупки)",
    "normal_dca": "Стандартный DCA",
}

EXPOSURE_LABELS: dict[str, str] = {
    "no_exposure": "Без вложений",
    "tiny": "Минимальная (сумма, которую не жалко потерять)",
    "small": "Небольшая (до 5% свободных средств)",
    "moderate": "Умеренная (5-15% свободных средств)",
}


@dataclass
class InvestmentPolicy:
    """Operational investment policy recommendation."""

    action_posture: ActionPosture = "wait_for_clarity"
    exposure_posture: ExposurePosture = "no_exposure"
    hard_guards: list[str] = field(default_factory=list)
    soft_limiters: list[str] = field(default_factory=list)
    why_this_posture: str = ""
    what_must_improve: list[str] = field(default_factory=list)
    policy_confidence: Literal["low", "medium", "high"] = "low"

    def to_synthesis_block(self) -> str:
        lines = [
            "## Инвестиционная политика (operational recommendation)",
            "",
            f"**Действие:** {ACTION_LABELS.get(self.action_posture, self.action_posture)}",
            f"**Допустимый размер:** {EXPOSURE_LABELS.get(self.exposure_posture, self.exposure_posture)}",
            f"**Уверенность в рекомендации:** {self.policy_confidence}",
            f"**Почему:** {self.why_this_posture}",
        ]

        if self.hard_guards:
            lines.append("\n**Жёсткие ограничения (блокируют вход):**")
            for g in self.hard_guards:
                lines.append(f"  🛑 {g}")

        if self.soft_limiters:
            lines.append("\n**Мягкие ограничения (снижают размер):**")
            for s in self.soft_limiters:
                lines.append(f"  ⚠ {s}")

        if self.what_must_improve:
            lines.append("\n**Что должно измениться для более уверенного входа:**")
            for w in self.what_must_improve:
                lines.append(f"  → {w}")

        lines.append("")
        lines.append(
            "ВАЖНО ДЛЯ SYNTHESIS: используй эту политику как основу для decision_signal и next_step. "
            "Если есть hard guards — НЕ рекомендуй вход. "
            "Exposure posture определяет максимальный допустимый размер. "
            "Назови конкретное действие, а не generic 'будь осторожен'."
        )
        return "\n".join(lines)


# ── Hard guard detection ─────────────────────────────────────────────

def _detect_hard_guards(
    c: PersonalInvestmentConstraints,
    fusion: InvestmentFusion | None,
) -> list[str]:
    guards = []

    if c.runway_months is not None and c.runway_months < 2:
        guards.append("insufficient_runway: подушка < 2 мес. — нет запаса на непредвиденные расходы")

    if c.has_debt and c.runway_months is not None and c.runway_months < 4:
        guards.append("debt_priority_first: есть долги + слабая подушка — сначала погасить долг")

    if c.emotional_stability == "low" and c.experience_level == "novice":
        guards.append("stability_too_low: стресс/выгорание + отсутствие опыта — решения под давлением опасны")

    missing = c.missing_field_keys
    if len(missing) >= 4:
        guards.append("insufficient_profile: слишком мало данных о личной ситуации для любой рекомендации")

    regime = fusion.market_regime if fusion else ""
    alignment = fusion.signal_alignment if fusion else ""
    if c.experience_level == "novice" and ("risk-off" in regime or "медвеж" in regime):
        guards.append("hostile_market_for_novice: медвежий рынок + новичок — высокий риск паники при просадке")

    if c.has_dependents and c.runway_months is not None and c.runway_months < 3:
        guards.append("dependents_at_risk: зависимые + подушка < 3 мес. — вложения ставят под удар семью")

    return guards


# ── Soft limiter detection ───────────────────────────────────────────

def _detect_soft_limiters(
    c: PersonalInvestmentConstraints,
    fusion: InvestmentFusion | None,
) -> list[str]:
    limiters = []
    alignment = fusion.signal_alignment if fusion else ""
    regime = fusion.market_regime if fusion else ""

    if c.runway_months is not None and 2 <= c.runway_months < 6:
        limiters.append("Подушка ниже рекомендуемых 6 мес. — ограничивает размер позиции")

    if c.risk_tolerance == "low":
        limiters.append("Низкая толерантность к риску — только минимальная экспозиция")

    if c.experience_level == "novice":
        limiters.append("Новичок — размер позиции должен быть ниже")

    if alignment == "conflicting":
        limiters.append("Сигналы конфликтуют — размер снижен из-за неопределённости")

    if c.has_debt and (c.runway_months is None or c.runway_months >= 4):
        limiters.append("Есть долги — часть свободных средств лучше направить на погашение")

    if c.has_dependents:
        limiters.append("Есть зависимые — снижает допустимый риск")

    if "неопределён" in regime or "боковой" in regime:
        limiters.append("Рынок в боковике — нет ясного направления")

    return limiters


# ── Main policy logic ────────────────────────────────────────────────

def compute_investment_policy(
    constraints: PersonalInvestmentConstraints,
    fusion: InvestmentFusion | None,
    suitability: PersonalSuitability,
) -> InvestmentPolicy:
    """Compute operational investment policy from all available data."""

    p = InvestmentPolicy()
    p.hard_guards = _detect_hard_guards(constraints, fusion)
    p.soft_limiters = _detect_soft_limiters(constraints, fusion)

    regime = fusion.market_regime if fusion else ""
    alignment = fusion.signal_alignment if fusion else ""
    missing_count = len(constraints.missing_field_keys)

    # ── Hard guards → block entry ──
    if p.hard_guards:
        p.action_posture = "avoid_now"
        p.exposure_posture = "no_exposure"
        p.why_this_posture = f"Заблокировано: {p.hard_guards[0].split(': ', 1)[-1]}"
        p.policy_confidence = "high" if len(p.hard_guards) >= 2 else "medium"
        p.what_must_improve = _derive_improvements(constraints, fusion, p.hard_guards)
        return p

    # ── Insufficient data → low confidence wait ──
    if missing_count >= 3:
        p.action_posture = "wait_for_clarity"
        p.exposure_posture = "no_exposure"
        p.why_this_posture = "Недостаточно данных о личной ситуации. Заполни профиль."
        p.policy_confidence = "low"
        p.what_must_improve = [f"Заполнить: {', '.join(constraints.missing_fields[:3])}"]
        return p

    # ── Score approach: enablers vs limiters ──
    enabler_score = 0
    limiter_score = len(p.soft_limiters)

    if constraints.investment_horizon == "long":
        enabler_score += 2
    elif constraints.investment_horizon == "medium":
        enabler_score += 1

    if constraints.runway_months is not None and constraints.runway_months >= 6:
        enabler_score += 2
    elif constraints.runway_months is not None and constraints.runway_months >= 3:
        enabler_score += 1

    if constraints.risk_tolerance == "high":
        enabler_score += 2
    elif constraints.risk_tolerance == "medium":
        enabler_score += 1

    if constraints.experience_level == "experienced":
        enabler_score += 1

    if not constraints.has_debt:
        enabler_score += 1

    # Market conditions
    if "risk-on" in regime or "бычий" in regime:
        enabler_score += 1
    if "risk-off" in regime or "медвеж" in regime:
        limiter_score += 1
    if alignment == "aligned_bullish":
        enabler_score += 1
    if alignment == "aligned_bearish":
        limiter_score += 1

    # ── Determine posture ──
    net = enabler_score - limiter_score

    if net >= 5:
        p.action_posture = "normal_dca"
        p.exposure_posture = "moderate"
        p.why_this_posture = "Личный профиль и рыночная ситуация позволяют стандартный вход"
    elif net >= 3:
        p.action_posture = "small_dca"
        p.exposure_posture = "small"
        p.why_this_posture = "Личный профиль позволяет вход, но есть ограничивающие факторы"
    elif net >= 1:
        p.action_posture = "exploratory_entry"
        p.exposure_posture = "tiny"
        p.why_this_posture = "Ограничения перевешивают — допустим только пробный вход"
    elif net >= -1:
        p.action_posture = "wait_for_clarity"
        p.exposure_posture = "no_exposure"
        p.why_this_posture = "Слишком много ограничений для входа прямо сейчас"
    else:
        p.action_posture = "avoid_now"
        p.exposure_posture = "no_exposure"
        p.why_this_posture = "Личная ситуация и рыночные условия не благоприятствуют входу"

    # ── Confidence ──
    if missing_count == 0 and enabler_score >= 3:
        p.policy_confidence = "high"
    elif missing_count <= 1:
        p.policy_confidence = "medium"
    else:
        p.policy_confidence = "low"

    # ── What must improve ──
    p.what_must_improve = _derive_improvements(constraints, fusion, p.hard_guards)

    return p


def _derive_improvements(
    c: PersonalInvestmentConstraints,
    fusion: InvestmentFusion | None,
    guards: list[str],
) -> list[str]:
    improvements = []

    if c.runway_months is not None and c.runway_months < 6:
        improvements.append(f"Увеличить подушку до 6+ мес. (сейчас ~{c.runway_months:.0f})")
    elif c.runway_months is None:
        improvements.append("Определить размер финансовой подушки")

    if c.has_debt:
        improvements.append("Погасить или существенно снизить долговую нагрузку")

    if c.emotional_stability == "low":
        improvements.append("Восстановить эмоциональную стабильность (снизить стресс/выгорание)")

    alignment = fusion.signal_alignment if fusion else ""
    if alignment == "conflicting":
        improvements.append("Дождаться более согласованных рыночных сигналов")

    missing = c.missing_fields
    if missing:
        improvements.append(f"Заполнить недостающие данные: {', '.join(missing[:2])}")

    return improvements[:4]
