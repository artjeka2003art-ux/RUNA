"""Affordability / expense reasoning layer.

Narrow v1: for questions about large purchases, rent increases, or general
"can I afford this" decisions, build a structured signal from persistent
promoted facts (salary, savings, debt, employment constraints) and inject
it into the prediction synthesis pipeline.

All internal contracts are canonical English (multilingual-safe). Keyword
heuristics for detection are isolated here and clearly marked as LANG-FALLBACK.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal


# ── Canonical affordability contract ─────────────────────────────

# Question sub-type (detected from user question). Canonical English.
AFFORDABILITY_NONE = "none"  # not an affordability question
AFFORDABILITY_LARGE_PURCHASE = "large_purchase"  # one-off big spend
AFFORDABILITY_RECURRING_COST = "recurring_cost"  # rent / subscription increase
AFFORDABILITY_GENERAL = "general_affordability"  # "can I afford this lifestyle"


# Affordability posture — the structured output that drives synthesis
AffordabilityPosture = Literal[
    "insufficient_data",  # we can't form a view yet
    "clearly_affordable",
    "likely_affordable_with_caveats",
    "borderline",
    "likely_stretched",
    "clearly_risky",
]


@dataclass
class AffordabilityContext:
    """Canonical affordability context built from persistent facts."""

    # Question classification
    question_subtype: str = AFFORDABILITY_NONE  # one of AFFORDABILITY_* constants
    amount_hint: str = ""  # raw extracted amount phrase if any, e.g. "200,000"
    currency_hint: str = ""  # raw extracted currency if any, e.g. "RUB" / "EUR"

    # Known financial facts (from promoted_facts)
    has_salary: bool = False
    salary_value: str = ""  # exact_value as stored
    salary_source: str = ""  # source_document_name

    has_bonus: bool = False
    bonus_value: str = ""
    bonus_source: str = ""

    has_savings: bool = False
    savings_value: str = ""
    savings_source: str = ""

    has_debt: bool = False
    debt_value: str = ""
    debt_source: str = ""

    has_budget: bool = False
    budget_value: str = ""
    budget_source: str = ""

    # Employment-related risk modifiers
    in_probation: bool = False
    probation_value: str = ""
    has_non_compete: bool = False
    non_compete_value: str = ""
    has_notice_period: bool = False
    notice_period_value: str = ""

    # Computed signal
    posture: AffordabilityPosture = "insufficient_data"
    main_limiters: list[str] = field(default_factory=list)
    what_makes_affordable: list[str] = field(default_factory=list)
    what_makes_risky: list[str] = field(default_factory=list)
    missing_financial_facts: list[str] = field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "low"

    def to_dict(self) -> dict:
        return {
            "question_subtype": self.question_subtype,
            "amount_hint": self.amount_hint,
            "currency_hint": self.currency_hint,
            "known_facts": {
                "salary": {"present": self.has_salary, "value": self.salary_value, "source": self.salary_source},
                "bonus": {"present": self.has_bonus, "value": self.bonus_value, "source": self.bonus_source},
                "savings": {"present": self.has_savings, "value": self.savings_value, "source": self.savings_source},
                "debt": {"present": self.has_debt, "value": self.debt_value, "source": self.debt_source},
                "budget": {"present": self.has_budget, "value": self.budget_value, "source": self.budget_source},
            },
            "employment_risk": {
                "in_probation": self.in_probation,
                "probation_value": self.probation_value,
                "has_non_compete": self.has_non_compete,
                "non_compete_value": self.non_compete_value,
                "has_notice_period": self.has_notice_period,
                "notice_period_value": self.notice_period_value,
            },
            "posture": self.posture,
            "main_limiters": self.main_limiters,
            "what_makes_affordable": self.what_makes_affordable,
            "what_makes_risky": self.what_makes_risky,
            "missing_financial_facts": self.missing_financial_facts,
            "confidence": self.confidence,
        }

    def to_synthesis_block(self) -> str:
        """Render canonical block for injection into personal_context.

        User-facing phrasing (Russian) is isolated here as temporary i18n
        fallback — labels should eventually move to a translation layer.
        """
        if self.question_subtype == AFFORDABILITY_NONE:
            return ""

        # LANG-FALLBACK: user-facing labels below are Russian for current tests.
        # Internal keys (posture, main_limiters etc.) stay canonical English.
        POSTURE_LABELS_RU = {
            "insufficient_data": "Недостаточно данных для оценки",
            "clearly_affordable": "Явно позволительно",
            "likely_affordable_with_caveats": "Вероятно позволительно, с оговорками",
            "borderline": "Пограничный случай",
            "likely_stretched": "Вероятно на пределе",
            "clearly_risky": "Явно рискованно",
        }

        lines = ["\n## Affordability / expense analysis (persistent-fact-based)"]
        lines.append(f"  question_subtype: {self.question_subtype}")
        if self.amount_hint:
            hint_line = f"{self.amount_hint} {self.currency_hint}".strip()
            lines.append(f"  amount_hint: {hint_line}")
        lines.append(f"  posture: {self.posture} ({POSTURE_LABELS_RU.get(self.posture, self.posture)})")
        lines.append(f"  confidence: {self.confidence}")

        if self.has_salary:
            lines.append(f"  known salary: {self.salary_value} (source: {self.salary_source})")
        if self.has_savings:
            lines.append(f"  known savings: {self.savings_value}")
        if self.has_debt:
            lines.append(f"  known debt: {self.debt_value}")
        if self.has_budget:
            lines.append(f"  known budget: {self.budget_value}")

        if self.in_probation:
            lines.append(f"  employment risk: currently in probation ({self.probation_value})")
        if self.has_non_compete:
            lines.append(f"  employment risk: non-compete in effect ({self.non_compete_value})")

        if self.what_makes_affordable:
            lines.append("  what makes it affordable:")
            for it in self.what_makes_affordable:
                lines.append(f"    + {it}")
        if self.what_makes_risky:
            lines.append("  what makes it risky:")
            for it in self.what_makes_risky:
                lines.append(f"    - {it}")
        if self.main_limiters:
            lines.append("  main limiters:")
            for it in self.main_limiters:
                lines.append(f"    * {it}")
        if self.missing_financial_facts:
            lines.append("  missing financial facts for precision:")
            for it in self.missing_financial_facts:
                lines.append(f"    ? {it}")

        lines.append(
            "  SYNTHESIS RULES: use only these facts. Do NOT invent monthly net from annual gross. "
            "Do NOT convert currency without explicit evidence. If key facts are missing, state so honestly."
        )
        return "\n".join(lines)


# ── Detection: is this an affordability question? ────────────────

# LANG-FALLBACK: multilingual keyword heuristics.
# Internal contract: output is one of canonical AFFORDABILITY_* constants.
# TODO: replace keyword match with canonical LLM classifier later.

_LARGE_PURCHASE_KEYWORDS = [
    # English
    "buy", "purchase", "can i get", "should i spend", "worth buying",
    # Russian
    "купить", "покупка", "потяну", "могу ли я купить", "приобрести",
    # Spanish
    "comprar",
]

_RECURRING_COST_KEYWORDS = [
    # English
    "rent", "subscription", "monthly cost", "monthly expense", "increase my spending",
    "upgrade apartment", "more expensive apartment",
    # Russian
    "аренда", "снимать", "ежемесячн", "повысить расход", "увеличить расход", "дороже квартир",
    # Spanish
    "alquiler", "gasto mensual",
]

_GENERAL_AFFORDABILITY_KEYWORDS = [
    # English
    "can i afford", "is it safe to spend", "big expense", "large expense",
    "major expense", "financial safety", "afford",
    # Russian
    "могу ли я себе позволить", "могу себе позволить", "себе позволить", "позволить себе",
    "безопасно ли тратить", "крупная трата", "крупный расход",
    "крупная покупка", "большая трата",
    # Spanish
    "puedo permitirme", "permitirme",
]


def _has_any(text: str, keywords: list[str]) -> bool:
    low = text.lower()
    return any(k in low for k in keywords)


def detect_affordability_subtype(question: str, variants: list[str] | None = None) -> str:
    """Detect affordability question subtype.

    Returns one of: AFFORDABILITY_NONE, AFFORDABILITY_LARGE_PURCHASE,
    AFFORDABILITY_RECURRING_COST, AFFORDABILITY_GENERAL.

    v1: keyword-based across RU/EN/ES. LLM fallback not needed for this narrow
    detection; if noisy, upgrade later to canonical classifier.
    """
    full = question + " " + " ".join(variants or [])

    # Order: recurring cost (most specific) → general affordability phrases
    # ("can I afford", "могу себе позволить") → one-off large purchase (broad verbs).
    if _has_any(full, _RECURRING_COST_KEYWORDS):
        return AFFORDABILITY_RECURRING_COST
    if _has_any(full, _GENERAL_AFFORDABILITY_KEYWORDS):
        return AFFORDABILITY_GENERAL
    if _has_any(full, _LARGE_PURCHASE_KEYWORDS):
        return AFFORDABILITY_LARGE_PURCHASE
    return AFFORDABILITY_NONE


# ── Amount / currency extraction (best-effort, language-agnostic) ──

_AMOUNT_RE = re.compile(
    r"(?P<num>\d[\d\s.,]*\d|\d+)\s*(?P<cur>eur|€|usd|\$|rub|руб|gbp|£)?",
    re.IGNORECASE,
)

_CURRENCY_NORMALIZE = {
    "eur": "EUR", "€": "EUR",
    "usd": "USD", "$": "USD",
    "rub": "RUB", "руб": "RUB",
    "gbp": "GBP", "£": "GBP",
}


def extract_amount_hint(text: str) -> tuple[str, str]:
    """Best-effort extraction of (amount, currency) from free text.

    Returns ("", "") if nothing found. Language-agnostic regex.
    """
    best_amount = ""
    best_currency = ""
    for m in _AMOUNT_RE.finditer(text):
        num = m.group("num") or ""
        cur = (m.group("cur") or "").lower()
        # Skip tiny numbers (likely year parts or noise)
        digits = re.sub(r"\D", "", num)
        if len(digits) < 4:
            continue
        if len(digits) > len(re.sub(r"\D", "", best_amount)):
            best_amount = num.strip()
            best_currency = _CURRENCY_NORMALIZE.get(cur, "")
    return best_amount, best_currency


# ── Signal builder: promoted facts → AffordabilityContext ─────────

# Canonical keys we care about (from CANONICAL_FACT_KEYS in prediction_query_agent)
_SALARY_KEY = "financial.base_salary"
_BONUS_KEY = "financial.bonus"
_SAVINGS_KEY = "financial_state.savings"
_DEBT_KEY = "financial_state.debt"
_BUDGET_KEY = "financial_state.budget"
_PROBATION_KEY = "constraint.probation_period"
_NON_COMPETE_KEY = "constraint.non_compete"
_NOTICE_KEY = "constraint.notice_period"

_ACTIVE_STATES = {"active", "user_confirmed"}


def _find_fact(promoted_facts: list[dict], fact_key: str) -> dict | None:
    """Find a usable promoted fact by canonical key, respecting state."""
    for f in promoted_facts:
        if f.get("fact_key") == fact_key and f.get("state") in _ACTIVE_STATES:
            return f
    return None


def build_affordability_context(
    question: str,
    variants: list[str] | None,
    promoted_facts: list[dict],
) -> AffordabilityContext:
    """Build a canonical AffordabilityContext from the question and persistent facts.

    Pure function. No LLM calls. Safe to run in parallel with other signals.
    """
    subtype = detect_affordability_subtype(question, variants)
    ctx = AffordabilityContext(question_subtype=subtype)

    if subtype == AFFORDABILITY_NONE:
        return ctx

    amount, currency = extract_amount_hint(question)
    ctx.amount_hint = amount
    ctx.currency_hint = currency

    # Pull canonical facts
    salary = _find_fact(promoted_facts, _SALARY_KEY)
    if salary:
        ctx.has_salary = True
        ctx.salary_value = salary.get("fact_value", "")
        ctx.salary_source = salary.get("source_document_name", "")

    bonus = _find_fact(promoted_facts, _BONUS_KEY)
    if bonus:
        ctx.has_bonus = True
        ctx.bonus_value = bonus.get("fact_value", "")
        ctx.bonus_source = bonus.get("source_document_name", "")

    savings = _find_fact(promoted_facts, _SAVINGS_KEY)
    if savings:
        ctx.has_savings = True
        ctx.savings_value = savings.get("fact_value", "")
        ctx.savings_source = savings.get("source_document_name", "")

    debt = _find_fact(promoted_facts, _DEBT_KEY)
    if debt:
        ctx.has_debt = True
        ctx.debt_value = debt.get("fact_value", "")
        ctx.debt_source = debt.get("source_document_name", "")

    budget = _find_fact(promoted_facts, _BUDGET_KEY)
    if budget:
        ctx.has_budget = True
        ctx.budget_value = budget.get("fact_value", "")
        ctx.budget_source = budget.get("source_document_name", "")

    # Employment risk modifiers
    probation = _find_fact(promoted_facts, _PROBATION_KEY)
    if probation:
        ctx.in_probation = True  # naive — v1 assumes active if promoted recently
        ctx.probation_value = probation.get("fact_value", "")

    non_compete = _find_fact(promoted_facts, _NON_COMPETE_KEY)
    if non_compete:
        ctx.has_non_compete = True
        ctx.non_compete_value = non_compete.get("fact_value", "")

    notice = _find_fact(promoted_facts, _NOTICE_KEY)
    if notice:
        ctx.has_notice_period = True
        ctx.notice_period_value = notice.get("fact_value", "")

    # Compute posture + confidence (heuristic, grounded in present facts only)
    _compute_posture(ctx)
    return ctx


def _compute_posture(ctx: AffordabilityContext) -> None:
    """Apply grounded heuristic to choose posture + confidence.

    v1: simple, honest, explicit about what's missing. No fake precision.
    """
    # Nothing useful known → insufficient_data
    if not (ctx.has_salary or ctx.has_savings or ctx.has_budget):
        ctx.posture = "insufficient_data"
        ctx.confidence = "low"
        ctx.missing_financial_facts = [
            "base_salary", "savings", "budget_or_monthly_expenses",
        ]
        return

    affordable_reasons: list[str] = []
    risky_reasons: list[str] = []
    limiters: list[str] = []
    missing: list[str] = []

    if ctx.has_salary:
        affordable_reasons.append(f"known income: {ctx.salary_value}")
    else:
        missing.append("base_salary")

    if ctx.has_savings:
        affordable_reasons.append(f"known savings: {ctx.savings_value}")
    else:
        missing.append("savings / emergency_fund")

    if ctx.has_budget:
        affordable_reasons.append(f"known baseline budget: {ctx.budget_value}")
    else:
        missing.append("monthly_budget / recurring_expenses")

    if ctx.has_debt:
        risky_reasons.append(f"existing debt obligation: {ctx.debt_value}")
        limiters.append("debt_service")

    if ctx.in_probation:
        risky_reasons.append(f"currently on probation: {ctx.probation_value}")
        limiters.append("employment_uncertainty_probation")

    if ctx.has_non_compete:
        # non-compete is not directly an affordability factor, but it limits job mobility
        # → reduced flexibility if job is lost.
        limiters.append("reduced_job_mobility_due_to_non_compete")

    ctx.main_limiters = limiters
    ctx.what_makes_affordable = affordable_reasons
    ctx.what_makes_risky = risky_reasons
    ctx.missing_financial_facts = missing

    # Posture heuristic:
    # - if missing budget AND savings → borderline at best
    # - if in probation → downgrade
    # - if has debt → downgrade
    # - if salary + savings + budget known and no risk modifiers → clearly_affordable (still "likely" without concrete numbers)

    # Base level
    if ctx.has_salary and ctx.has_savings and ctx.has_budget and not ctx.has_debt and not ctx.in_probation:
        ctx.posture = "likely_affordable_with_caveats"
        ctx.confidence = "medium"
    elif ctx.has_salary and (ctx.has_savings or ctx.has_budget):
        ctx.posture = "borderline"
        ctx.confidence = "low"
    elif ctx.has_salary and not ctx.has_savings and not ctx.has_budget:
        ctx.posture = "borderline"
        ctx.confidence = "low"
        limiters.append("no_savings_or_budget_visibility")
    else:
        ctx.posture = "insufficient_data"
        ctx.confidence = "low"

    # Risk downgrades
    if ctx.in_probation and ctx.posture in ("likely_affordable_with_caveats", "borderline"):
        ctx.posture = "likely_stretched" if ctx.posture == "borderline" else "borderline"

    if ctx.has_debt and ctx.posture in ("likely_affordable_with_caveats", "borderline"):
        ctx.posture = "likely_stretched" if ctx.posture == "borderline" else "borderline"

    # Without knowing the purchase amount relative to income we cannot claim "clearly_affordable"
    # — stay honest.
