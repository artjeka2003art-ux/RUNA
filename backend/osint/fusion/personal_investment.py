"""Personal investment constraint fusion: connect market signals with user's personal situation.

Extracts investment-relevant constraints from personal context,
then evaluates suitability of investment action for THIS user.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .investment import InvestmentFusion


# ── Personal investment constraints ──────────────────────────────────

@dataclass
class PersonalInvestmentConstraints:
    """Investment-relevant personal parameters extracted from user context."""

    investment_horizon: str = ""          # "short" (<1y), "medium" (1-3y), "long" (3y+), "" = unknown
    runway_months: float | None = None    # emergency fund in months of expenses
    risk_tolerance: str = ""              # "low", "medium", "high", "" = unknown
    max_acceptable_drawdown: str = ""     # "10%", "30%", "50%+", "" = unknown
    experience_level: str = ""            # "novice", "some", "experienced", "" = unknown
    allocation_posture: str = ""          # "aggressive", "cautious", "minimal", "" = unknown
    emotional_stability: str = ""         # "low", "medium", "high", "" = unknown
    has_dependents: bool | None = None
    has_debt: bool | None = None
    monthly_free_cash: str = ""           # qualitative: "tight", "moderate", "comfortable", "" = unknown

    @property
    def missing_fields(self) -> list[str]:
        """Return list of critical missing fields (human-readable, for synthesis)."""
        missing = []
        if not self.investment_horizon:
            missing.append("горизонт инвестирования (на какой срок)")
        if self.runway_months is None:
            missing.append("финансовая подушка (сколько месяцев)")
        if not self.risk_tolerance:
            missing.append("толерантность к риску")
        if not self.experience_level:
            missing.append("опыт инвестирования")
        return missing

    @property
    def missing_field_keys(self) -> list[str]:
        """Return stable field keys for missing fields (for structured contract)."""
        keys = []
        if not self.investment_horizon:
            keys.append("investment_horizon")
        if self.runway_months is None:
            keys.append("runway_months")
        if not self.risk_tolerance:
            keys.append("risk_tolerance")
        if not self.experience_level:
            keys.append("experience_level")
        if not self.max_acceptable_drawdown:
            keys.append("max_acceptable_drawdown")
        if self.has_debt is None:
            keys.append("has_debt")
        if self.has_dependents is None:
            keys.append("has_dependents")
        return keys

    @property
    def completeness(self) -> Literal["low", "medium", "high"]:
        n_missing = len(self.missing_fields)
        if n_missing >= 3:
            return "low"
        if n_missing >= 1:
            return "medium"
        return "high"

    def to_summary(self) -> str:
        """Human-readable summary for synthesis."""
        lines = []
        if self.investment_horizon:
            labels = {"short": "краткосрочный (<1 года)", "medium": "среднесрочный (1-3 года)", "long": "долгосрочный (3+ лет)"}
            lines.append(f"Горизонт: {labels.get(self.investment_horizon, self.investment_horizon)}")
        if self.runway_months is not None:
            lines.append(f"Финансовая подушка: ~{self.runway_months:.0f} мес.")
        if self.risk_tolerance:
            labels = {"low": "низкая", "medium": "умеренная", "high": "высокая"}
            lines.append(f"Толерантность к риску: {labels.get(self.risk_tolerance, self.risk_tolerance)}")
        if self.max_acceptable_drawdown:
            lines.append(f"Допустимая просадка: {self.max_acceptable_drawdown}")
        if self.experience_level:
            labels = {"novice": "новичок", "some": "базовый опыт", "experienced": "опытный"}
            lines.append(f"Опыт: {labels.get(self.experience_level, self.experience_level)}")
        if self.allocation_posture:
            labels = {"aggressive": "агрессивная", "cautious": "осторожная", "minimal": "минимальная"}
            lines.append(f"Позиция по вложениям: {labels.get(self.allocation_posture, self.allocation_posture)}")
        if self.emotional_stability:
            labels = {"low": "низкая (стресс/выгорание)", "medium": "нормальная", "high": "высокая"}
            lines.append(f"Эмоц. устойчивость: {labels.get(self.emotional_stability, self.emotional_stability)}")
        if self.has_dependents is True:
            lines.append("Есть зависимые (семья/дети)")
        if self.has_debt is True:
            lines.append("Есть долги/кредиты")
        return "\n".join(lines) if lines else "Личный инвестиционный контекст не определён"


# ── Typed field registry (structured contract for frontend) ──────────

TYPED_FIELD_REGISTRY: dict[str, dict] = {
    "investment_horizon": {
        "field_key": "investment_horizon",
        "label": "Горизонт инвестирования",
        "why": "Влияет на то, считать ли просадку критичной",
        "capture_type": "select",
        "mode": "investment",
        "options": [
            {"value": "short", "label": "Краткосрочный (< 1 года)"},
            {"value": "medium", "label": "Среднесрочный (1–3 года)"},
            {"value": "long", "label": "Долгосрочный (3+ лет)"},
        ],
    },
    "risk_tolerance": {
        "field_key": "risk_tolerance",
        "label": "Толерантность к риску",
        "why": "Влияет на допустимый тип входа и размер позиции",
        "capture_type": "select",
        "mode": "investment",
        "options": [
            {"value": "low", "label": "Низкая — не готов терять"},
            {"value": "medium", "label": "Умеренная"},
            {"value": "high", "label": "Высокая — готов к просадкам"},
        ],
    },
    "experience_level": {
        "field_key": "experience_level",
        "label": "Опыт инвестирования",
        "why": "Новичкам нужны более осторожные рекомендации",
        "capture_type": "select",
        "mode": "investment",
        "options": [
            {"value": "novice", "label": "Новичок"},
            {"value": "some", "label": "Базовый опыт"},
            {"value": "experienced", "label": "Опытный инвестор"},
        ],
    },
    "runway_months": {
        "field_key": "runway_months",
        "label": "Финансовая подушка (месяцев)",
        "why": "Без подушки инвестировать в волатильные активы опасно",
        "capture_type": "number",
        "mode": "investment",
        "min": 0,
        "max": 120,
        "placeholder": "Например: 6",
    },
    "max_acceptable_drawdown": {
        "field_key": "max_acceptable_drawdown",
        "label": "Допустимая просадка",
        "why": "Определяет acceptable volatility",
        "capture_type": "select",
        "mode": "investment",
        "options": [
            {"value": "10%", "label": "До 10%"},
            {"value": "30%", "label": "До 30%"},
            {"value": "50%+", "label": "50% и больше"},
        ],
    },
    "has_debt": {
        "field_key": "has_debt",
        "label": "Есть долги / кредиты",
        "why": "Инвестирование при долгах увеличивает суммарный риск",
        "capture_type": "boolean",
        "mode": "investment",
    },
    "has_dependents": {
        "field_key": "has_dependents",
        "label": "Есть зависимые (семья, дети)",
        "why": "Потеря капитала затрагивает не только вас",
        "capture_type": "boolean",
        "mode": "investment",
    },
}


# ── Extraction from personal context ─────────────────────────────────

def _norm(s: str) -> str:
    return s.lower().replace("ё", "е")


_HORIZON_LONG = ["долгосрочн", "long term", "на годы", "3 года", "5 лет", "10 лет", "надолго", "горизонт больш"]
_HORIZON_MEDIUM = ["среднесрочн", "1-3 года", "пару лет", "на год", "medium term"]
_HORIZON_SHORT = ["краткосрочн", "быстр", "на месяц", "short term", "спекуля"]

_RISK_HIGH = ["готов к риск", "high risk", "агрессивн", "не боюсь потер"]
_RISK_LOW = ["не готов к риск", "low risk", "консерватив", "боюсь потер", "не хочу терять", "осторожн"]

_NOVICE = ["новичок", "первый раз", "не инвестировал", "не разбираюсь", "начинающ", "ничего не знаю", "novice"]
_EXPERIENCED = ["опыт инвест", "давно инвестирую", "experienced", "трейд", "портфел"]

_BURNOUT = ["выгоран", "burnout", "стресс", "тревог", "депресс", "устал", "нет сил"]
_DEBT = ["кредит", "ипотек", "долг", "задолженност"]
_DEPENDENTS = ["ребенок", "ребёнок", "дети", "семья", "жена", "муж", "содержу"]

_RUNWAY_PATTERN = re.compile(r"подушк\w*\s*(?:на\s*)?(\d+)\s*мес", re.I)
_RUNWAY_PATTERN2 = re.compile(r"(\d+)\s*мес\w*\s*(?:подушк|расход|runway)", re.I)


def extract_constraints(personal_context: str) -> PersonalInvestmentConstraints:
    """Extract investment constraints from personal context text.

    Uses keyword heuristics — not perfect, but better than nothing.
    """
    ctx = _norm(personal_context)
    c = PersonalInvestmentConstraints()

    # Horizon
    if any(kw in ctx for kw in _HORIZON_LONG):
        c.investment_horizon = "long"
    elif any(kw in ctx for kw in _HORIZON_MEDIUM):
        c.investment_horizon = "medium"
    elif any(kw in ctx for kw in _HORIZON_SHORT):
        c.investment_horizon = "short"

    # Risk tolerance
    if any(kw in ctx for kw in _RISK_LOW):
        c.risk_tolerance = "low"
    elif any(kw in ctx for kw in _RISK_HIGH):
        c.risk_tolerance = "high"

    # Experience
    if any(kw in ctx for kw in _NOVICE):
        c.experience_level = "novice"
    elif any(kw in ctx for kw in _EXPERIENCED):
        c.experience_level = "experienced"

    # Emotional stability (from burnout/stress signals)
    if any(kw in ctx for kw in _BURNOUT):
        c.emotional_stability = "low"

    # Dependents
    if any(kw in ctx for kw in _DEPENDENTS):
        c.has_dependents = True

    # Debt
    if any(kw in ctx for kw in _DEBT):
        c.has_debt = True

    # Runway
    m = _RUNWAY_PATTERN.search(personal_context) or _RUNWAY_PATTERN2.search(personal_context)
    if m:
        try:
            c.runway_months = float(m.group(1))
        except ValueError:
            pass

    return c


def build_constraints(
    structured_profile: dict | None,
    personal_context: str,
) -> tuple[PersonalInvestmentConstraints, list[str]]:
    """Build constraints from structured profile (priority) + text fallback.

    Returns (constraints, source_notes) where source_notes explains data provenance.
    """
    sources: list[str] = []

    # Start with structured profile if available
    if structured_profile:
        c = PersonalInvestmentConstraints(
            investment_horizon=structured_profile.get("investment_horizon", ""),
            risk_tolerance=structured_profile.get("risk_tolerance", ""),
            experience_level=structured_profile.get("experience_level", ""),
            max_acceptable_drawdown=structured_profile.get("max_acceptable_drawdown", ""),
            allocation_posture=structured_profile.get("allocation_posture", ""),
            has_debt=structured_profile.get("has_debt"),
            has_dependents=structured_profile.get("has_dependents"),
            monthly_free_cash=structured_profile.get("monthly_investable_amount", ""),
        )
        runway = structured_profile.get("runway_months")
        if runway is not None:
            try:
                c.runway_months = float(runway)
            except (ValueError, TypeError):
                pass
        sources.append("structured profile")
    else:
        c = PersonalInvestmentConstraints()

    # Fill gaps from text extraction
    text_c = extract_constraints(personal_context)
    filled_from_text: list[str] = []

    if not c.investment_horizon and text_c.investment_horizon:
        c.investment_horizon = text_c.investment_horizon
        filled_from_text.append("горизонт")
    if not c.risk_tolerance and text_c.risk_tolerance:
        c.risk_tolerance = text_c.risk_tolerance
        filled_from_text.append("толерантность к риску")
    if not c.experience_level and text_c.experience_level:
        c.experience_level = text_c.experience_level
        filled_from_text.append("опыт")
    if c.runway_months is None and text_c.runway_months is not None:
        c.runway_months = text_c.runway_months
        filled_from_text.append("подушка")
    if not c.emotional_stability and text_c.emotional_stability:
        c.emotional_stability = text_c.emotional_stability
        filled_from_text.append("эмоц. состояние")
    if c.has_dependents is None and text_c.has_dependents is not None:
        c.has_dependents = text_c.has_dependents
        filled_from_text.append("зависимые")
    if c.has_debt is None and text_c.has_debt is not None:
        c.has_debt = text_c.has_debt
        filled_from_text.append("долги")

    if filled_from_text:
        sources.append(f"text fallback ({', '.join(filled_from_text)})")

    if not sources:
        sources.append("данные отсутствуют")

    return c, sources


# ── Personal suitability fusion ──────────────────────────────────────

@dataclass
class PersonalSuitability:
    """Decision suitability assessment combining market state + personal constraints."""

    recommended_action: str = ""       # "wait", "dca", "tiny_position", "measured_entry", "avoid"
    action_reason: str = ""
    suitability_level: str = ""        # "suitable", "conditionally_suitable", "not_suitable", "unknown"
    personal_limiters: list[str] = field(default_factory=list)
    personal_enablers: list[str] = field(default_factory=list)
    mismatch_warnings: list[str] = field(default_factory=list)
    missing_for_confidence: list[str] = field(default_factory=list)
    conditions_that_change_answer: list[str] = field(default_factory=list)

    def to_synthesis_block(self) -> str:
        lines = [
            "## Персональная пригодность инвестиционного решения",
            "",
            f"**Рекомендуемое действие:** {self.recommended_action}",
            f"**Причина:** {self.action_reason}",
            f"**Пригодность:** {self.suitability_level}",
        ]

        if self.mismatch_warnings:
            lines.append("\n**Несоответствия (market opportunity vs personal readiness):**")
            for w in self.mismatch_warnings:
                lines.append(f"  ⚠ {w}")

        if self.personal_limiters:
            lines.append("\n**Личные ограничения:**")
            for l in self.personal_limiters:
                lines.append(f"  − {l}")

        if self.personal_enablers:
            lines.append("\n**Личные факторы в пользу:**")
            for e in self.personal_enablers:
                lines.append(f"  + {e}")

        if self.missing_for_confidence:
            lines.append("\n**Не хватает для уверенной рекомендации (personal):**")
            for m in self.missing_for_confidence:
                lines.append(f"  ? {m}")

        if self.conditions_that_change_answer:
            lines.append("\n**При каких личных условиях ответ меняется:**")
            for c in self.conditions_that_change_answer:
                lines.append(f"  → {c}")

        lines.append("")
        lines.append(
            "ВАЖНО ДЛЯ SYNTHESIS: используй эту персональную оценку в decision_signal, "
            "confidence_reason и next_step. Не давай агрессивных рекомендаций, "
            "если personal suitability говорит 'not_suitable' или есть mismatch warnings."
        )
        return "\n".join(lines)


def assess_suitability(
    constraints: PersonalInvestmentConstraints,
    fusion: InvestmentFusion | None,
) -> PersonalSuitability:
    """Combine personal constraints with market fusion to assess action suitability."""
    s = PersonalSuitability()
    s.missing_for_confidence = constraints.missing_fields[:]

    regime = fusion.market_regime if fusion else ""
    alignment = fusion.signal_alignment if fusion else ""

    # ── Collect limiters and enablers ──

    # Runway
    if constraints.runway_months is not None:
        if constraints.runway_months < 3:
            s.personal_limiters.append(f"Подушка ~{constraints.runway_months:.0f} мес. — критически мала для инвестиций в волатильные активы")
        elif constraints.runway_months < 6:
            s.personal_limiters.append(f"Подушка ~{constraints.runway_months:.0f} мес. — ниже рекомендуемых 6 мес., ограничивает размер позиции")
        else:
            s.personal_enablers.append(f"Подушка ~{constraints.runway_months:.0f} мес. — достаточна для инвестиционного риска")

    # Experience
    if constraints.experience_level == "novice":
        s.personal_limiters.append("Новичок — повышенный риск эмоциональных решений при просадке")
    elif constraints.experience_level == "experienced":
        s.personal_enablers.append("Опытный инвестор — может выдержать волатильность")

    # Risk tolerance
    if constraints.risk_tolerance == "low":
        s.personal_limiters.append("Низкая толерантность к риску — криптоактивы могут не подходить")
    elif constraints.risk_tolerance == "high":
        s.personal_enablers.append("Высокая толерантность к риску")

    # Emotional stability
    if constraints.emotional_stability == "low":
        s.personal_limiters.append("Выгорание/стресс — инвестиционные решения под давлением менее рациональны")

    # Debt
    if constraints.has_debt:
        s.personal_limiters.append("Есть долги/кредиты — инвестирование до погашения увеличивает суммарный риск")

    # Dependents
    if constraints.has_dependents:
        s.personal_limiters.append("Есть зависимые — потеря капитала затрагивает не только вас")

    # Horizon
    if constraints.investment_horizon == "long":
        s.personal_enablers.append("Долгосрочный горизонт — волатильность менее критична")
    elif constraints.investment_horizon == "short":
        s.personal_limiters.append("Краткосрочный горизонт — высокий риск попасть в просадку без времени на восстановление")

    # ── Mismatch detection ──

    if alignment == "conflicting":
        if constraints.experience_level == "novice":
            s.mismatch_warnings.append("Сигналы конфликтуют, а вы новичок — сложно правильно интерпретировать рынок")
        if constraints.emotional_stability == "low":
            s.mismatch_warnings.append("Конфликтующие сигналы + стресс/выгорание — решение может быть импульсивным")

    if "risk-off" in regime or "медвеж" in regime:
        if constraints.risk_tolerance == "low":
            s.mismatch_warnings.append("Медвежий рынок + низкая толерантность к риску — вход сейчас противоречит вашему профилю")
        if constraints.runway_months is not None and constraints.runway_months < 6:
            s.mismatch_warnings.append("Медвежий рынок + слабая подушка — нет запаса прочности при дальнейшем падении")

    if "risk-on" in regime or "бычий" in regime:
        if constraints.investment_horizon == "short":
            s.mismatch_warnings.append("Бычий рынок, но краткосрочный горизонт — можете войти на пике перед коррекцией")

    # ── Determine recommended action ──

    hard_blockers = len([l for l in s.personal_limiters if "критически" in l or "не подходят" in l])
    soft_limiters = len(s.personal_limiters)
    enablers = len(s.personal_enablers)
    mismatches = len(s.mismatch_warnings)
    missing = len(s.missing_for_confidence)

    if hard_blockers > 0:
        s.recommended_action = "Воздержаться от входа"
        s.action_reason = "Есть критические личные ограничения: " + "; ".join(s.personal_limiters[:2])
        s.suitability_level = "not_suitable"
    elif mismatches >= 2 or (soft_limiters >= 3 and enablers == 0):
        s.recommended_action = "Подождать / пересмотреть позже"
        s.action_reason = "Слишком много несоответствий между рыночной ситуацией и вашей готовностью"
        s.suitability_level = "not_suitable"
    elif missing >= 3:
        s.recommended_action = "Сначала уточнить личный контекст"
        s.action_reason = f"Не хватает ключевых данных ({', '.join(s.missing_for_confidence[:2])}). Невозможно дать уверенную рекомендацию."
        s.suitability_level = "unknown"
    elif soft_limiters > enablers and soft_limiters >= 2:
        s.recommended_action = "Минимальная позиция / DCA малыми суммами"
        s.action_reason = "Есть ограничения, но не критические. Допустим осторожный вход."
        s.suitability_level = "conditionally_suitable"
    elif enablers > soft_limiters:
        if alignment == "conflicting" or "неопределён" in regime:
            s.recommended_action = "DCA / постепенный вход"
            s.action_reason = "Личный профиль позволяет вход, но рыночные сигналы неоднозначны — лучше входить частями"
            s.suitability_level = "conditionally_suitable"
        else:
            s.recommended_action = "Взвешенный вход допустим"
            s.action_reason = "Личный профиль и рыночная ситуация позволяют"
            s.suitability_level = "suitable"
    else:
        s.recommended_action = "DCA / осторожный вход"
        s.action_reason = "Недостаточно данных для агрессивной рекомендации, но явных блокеров нет"
        s.suitability_level = "conditionally_suitable"

    # ── Conditions that change answer ──

    if constraints.runway_months is None:
        s.conditions_that_change_answer.append("Если подушка < 3 мес. — рекомендация сменится на 'воздержаться'")
    if not constraints.risk_tolerance:
        s.conditions_that_change_answer.append("Если толерантность к риску низкая — агрессивный вход не рекомендован")
    if constraints.investment_horizon == "short":
        s.conditions_that_change_answer.append("Если горизонт увеличится до 3+ лет — DCA становится значительно безопаснее")
    if constraints.has_debt:
        s.conditions_that_change_answer.append("Если долги погашены — инвестиционный риск становится допустимее")

    return s
