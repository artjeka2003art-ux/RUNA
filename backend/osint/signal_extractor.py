"""Signal extraction and normalization: raw search results → ExternalSignal.

Converts raw web search results into normalized, scored ExternalSignal objects
using the signal registry for mode-aware scoring.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

from .models import ExternalSignal, FreshnessLabel, QuestionMode, RetrievalPlan, SignalBundle
from .signal_registry import get_preferred_domains

logger = logging.getLogger(__name__)


# ── Freshness detection ──────────────────────────────────────────────

_DATE_PATTERNS = [
    # "Jan 15, 2025", "January 15, 2025"
    re.compile(r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+20\d{2}", re.I),
    # "2025-01-15"
    re.compile(r"20\d{2}-\d{2}-\d{2}"),
    # "15.01.2025"
    re.compile(r"\d{1,2}\.\d{1,2}\.20\d{2}"),
]

_FRESHNESS_KEYWORDS = {
    "fresh": ["today", "сегодня", "just now", "breaking", "hours ago", "час назад"],
    "recent": ["this week", "на этой неделе", "yesterday", "вчера", "days ago", "дней назад",
               "this month", "в этом месяце", "last week", "на прошлой неделе"],
}


def _detect_freshness(text: str, title: str = "") -> FreshnessLabel:
    """Detect freshness from text content and title."""
    combined = (text[:500] + " " + title).lower()

    for kw in _FRESHNESS_KEYWORDS["fresh"]:
        if kw in combined:
            return FreshnessLabel.fresh

    for kw in _FRESHNESS_KEYWORDS["recent"]:
        if kw in combined:
            return FreshnessLabel.recent

    # Check for dates in current year
    current_year = str(datetime.now().year)
    for pattern in _DATE_PATTERNS:
        match = pattern.search(combined)
        if match and current_year in match.group():
            return FreshnessLabel.recent

    return FreshnessLabel.timeless_or_unknown


# ── Signal type inference ────────────────────────────────────────────

_SIGNAL_TYPE_KEYWORDS: dict[str, list[str]] = {
    # Investment
    "market_movement": ["price", "rally", "drop", "surge", "decline", "bull", "bear", "цена", "рост", "падение"],
    "volatility_context": ["volatil", "risk", "uncertainty", "волатильн"],
    "macro_news": ["fed", "interest rate", "inflation", "gdp", "recession", "ставк", "инфляц"],
    "regulation_signal": ["regulat", "ban", "approve", "sec", "law", "регулир", "закон", "запрет"],
    "geopolitical_event": ["war", "sanction", "trade war", "geopolit", "sanctions", "война", "санкци"],
    "expert_forecast": ["forecast", "predict", "outlook", "expect", "прогноз", "ожидан"],
    # Career
    "hiring_market": ["hiring", "job market", "unemployment", "vacancy", "найм", "рынок труда", "вакансии"],
    "company_context": ["company", "layoff", "restructur", "компани", "сокращени", "реструктур"],
    "role_demand": ["demand", "skill", "role", "developer", "engineer", "спрос", "навык"],
    "industry_conditions": ["industry", "sector", "trend", "индустри", "сектор", "тренд"],
    "salary_benchmark": ["salary", "compensation", "pay", "зарплат", "компенсац", "оплат"],
    "layoff_signal": ["layoff", "fired", "downsiz", "увольнен", "сокращен"],
    # Health
    "weather_conditions": ["weather", "temperature", "rain", "snow", "погод", "температур"],
    "health_advisory": ["advisory", "warning", "outbreak", "рекомендац", "предупрежден"],
    "training_science": ["training", "exercise", "recovery", "тренировк", "упражнен", "восстановлен"],
    # Education
    "program_reputation": ["ranking", "reputation", "top universit", "рейтинг", "репутаци"],
    "market_value_of_degree": ["roi", "return", "salary after", "окупаемост", "зарплата после"],
    "career_outcomes": ["graduate outcome", "employment rate", "трудоустройство", "карьерные исход"],
    # Startup
    "market_size": ["market size", "tam", "addressable", "объём рынка", "размер рынка"],
    "funding_climate": ["funding", "venture", "investment round", "финансирован", "раунд"],
    "competitor_landscape": ["competitor", "market share", "конкурент", "доля рынка"],
    # Relationship
    "relationship_research": ["relationship", "attachment", "couple", "отношен", "привязанност"],
    "psychological_patterns": ["pattern", "behavior", "cognitive", "паттерн", "поведен"],
    # Relocation
    "cost_of_living": ["cost of living", "стоимость жизни", "rent", "аренда"],
    "quality_of_life": ["quality of life", "качество жизни", "safety", "безопасност"],
    "immigration_policy": ["visa", "immigration", "permit", "виза", "разрешен", "иммиграц"],
    # General
    "expert_framework": ["framework", "model", "approach", "research", "study", "исследован"],
    "research_evidence": ["evidence", "meta-analysis", "finding", "данные", "результат"],
    "statistical_context": ["statistic", "percent", "probability", "статистик", "процент", "вероятност"],
}


def _infer_signal_type(
    title: str,
    text: str,
    plan_signal_types: list[str],
) -> str:
    """Infer signal type from content, preferring types from the retrieval plan."""
    combined = (title + " " + text[:300]).lower()

    # Score each signal type from the plan
    best_type = "general_context"
    best_score = 0

    for stype in plan_signal_types:
        keywords = _SIGNAL_TYPE_KEYWORDS.get(stype, [])
        hits = sum(1 for kw in keywords if kw in combined)
        if hits > best_score:
            best_score = hits
            best_type = stype

    # If no plan type matched, try all types
    if best_score == 0:
        for stype, keywords in _SIGNAL_TYPE_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in combined)
            if hits > best_score:
                best_score = hits
                best_type = stype

    return best_type


# ── Relevance scoring ────────────────────────────────────────────────

def _score_relevance(
    title: str,
    text: str,
    question: str,
    mode: QuestionMode,
) -> float:
    """Score how relevant a result is to the question and mode."""
    q_lower = question.lower().replace("ё", "е")
    combined = (title + " " + text[:500]).lower()

    # Token overlap with question
    q_tokens = [t for t in re.split(r"[\s,.\-—/]+", q_lower) if len(t) > 2]
    if not q_tokens:
        return 0.3

    hits = sum(1 for t in q_tokens if t in combined)
    token_score = hits / len(q_tokens)

    # Mode-specific boost
    mode_keywords = _SIGNAL_TYPE_KEYWORDS.copy()
    mode_boost = 0.0
    for stype_kws in mode_keywords.values():
        if any(kw in combined for kw in stype_kws[:3]):
            mode_boost = 0.1
            break

    return min(1.0, token_score * 0.7 + mode_boost + 0.2)


# ── Quality scoring (mode-aware) ────────────────────────────────────

_HIGH_TRUST_PATTERNS = [
    ".edu", ".gov", ".ac.", ".org",
    "ncbi.nlm.nih.gov", "pubmed", "scholar.google",
    "nature.com", "sciencedirect.com",
]

_CLICKBAIT_SIGNALS = [
    "top 10", "top 5", "you won't believe", "ultimate guide",
    "hack your", "secrets to", "things you", "signs you",
    "best ways to", "simple tricks",
]

_REJECT_DOMAINS = {
    "pinterest.com", "facebook.com", "instagram.com", "tiktok.com",
    "twitter.com", "x.com", "reddit.com", "quora.com", "youtube.com",
    "wikihow.com", "buzzfeed.com", "boredpanda.com", "9gag.com",
}


def _score_quality(
    url: str,
    title: str,
    text: str,
    mode: QuestionMode,
) -> float:
    """Score source quality with mode-aware domain preferences."""
    href = url.lower()
    title_lower = title.lower()
    score = 0.5

    # Domain check
    domain = ""
    try:
        domain = url.split("/")[2].lower()
    except (IndexError, AttributeError):
        pass

    if any(d in domain for d in _REJECT_DOMAINS):
        return 0.0

    # Trust patterns
    if any(p in href for p in _HIGH_TRUST_PATTERNS):
        score += 0.25

    # Mode-specific preferred domains
    preferred = get_preferred_domains(mode)
    if any(p in domain for p in preferred):
        score += 0.2

    # Clickbait penalty
    if any(sig in title_lower for sig in _CLICKBAIT_SIGNALS):
        score -= 0.25

    # Content depth
    if len(text) > 500:
        score += 0.1
    elif len(text) < 100:
        score -= 0.15

    # Commercial penalty
    if any(w in href for w in ["shop", "buy", "product", "pricing", "affiliate"]):
        score -= 0.3

    return max(0.0, min(1.0, score))


# ── Main extraction pipeline ────────────────────────────────────────

def normalize_to_signal(
    raw_result: dict,
    full_text: str,
    question: str,
    plan: RetrievalPlan,
) -> ExternalSignal | None:
    """Convert a raw search result + fetched text into an ExternalSignal.

    Returns None if the result is too low quality to include.
    """
    title = raw_result.get("title", "")
    url = raw_result.get("href", "")
    snippet_raw = raw_result.get("body", "")
    text = full_text if len(full_text) > 100 else snippet_raw

    # Quality gate
    quality = _score_quality(url, title, text, plan.question_mode)
    if quality < 0.25:
        return None

    relevance = _score_relevance(title, text, question, plan.question_mode)
    if relevance < 0.15:
        return None

    signal_type = _infer_signal_type(title, text, plan.signal_types)
    freshness = _detect_freshness(text, title)

    # Freshness bonus/penalty based on plan priority
    if plan.freshness_priority == "high" and freshness == FreshnessLabel.timeless_or_unknown:
        quality = max(0.0, quality - 0.1)
    elif plan.freshness_priority == "high" and freshness == FreshnessLabel.fresh:
        quality = min(1.0, quality + 0.1)

    # Build snippet (prefer full text excerpt if available)
    if len(full_text) > 200:
        # Take first meaningful paragraph
        snippet = full_text[:600]
        source_type = "full_text"
    else:
        snippet = snippet_raw[:300]
        source_type = "snippet"

    source_name = ""
    try:
        source_name = url.split("/")[2]
    except (IndexError, AttributeError):
        pass

    return ExternalSignal(
        signal_type=signal_type,
        source_type=source_type,
        source_name=source_name,
        title=title,
        url=url,
        snippet=snippet,
        freshness_label=freshness,
        relevance_score=round(relevance, 2),
        quality_score=round(quality, 2),
        # why_it_matters will be filled by LLM in the synthesis step
        why_it_matters="",
    )


def build_signal_bundle(
    signals: list[ExternalSignal],
    plan: RetrievalPlan,
) -> SignalBundle:
    """Assemble signals into a SignalBundle with quality summary and coverage info."""
    # Sort by combined score (quality * 0.5 + relevance * 0.5)
    signals.sort(
        key=lambda s: s.quality_score * 0.5 + s.relevance_score * 0.5,
        reverse=True,
    )

    # Cap to max_signals
    signals = signals[:plan.max_signals]

    # Quality summary
    if not signals:
        quality_summary = "Качественных внешних сигналов по этому вопросу найти не удалось."
    else:
        avg_q = sum(s.quality_score for s in signals) / len(signals)
        avg_r = sum(s.relevance_score for s in signals) / len(signals)
        if avg_q >= 0.65:
            quality_summary = f"Найдены содержательные сигналы ({len(signals)} шт., avg quality {avg_q:.1f})."
        elif avg_q >= 0.45:
            quality_summary = f"Найдены сигналы среднего качества ({len(signals)} шт.). Выводы вероятностные."
        else:
            quality_summary = f"Доступные сигналы ограничены ({len(signals)} шт.). Выводы следует воспринимать осторожно."

    # Coverage: which signal types from plan were found
    found_types = {s.signal_type for s in signals}
    missing_types = [st for st in plan.signal_types if st not in found_types]
    if missing_types:
        coverage = f"Найдены: {', '.join(found_types)}. Не найдены: {', '.join(missing_types[:3])}."
    elif found_types:
        coverage = f"Покрыты все ключевые типы сигналов: {', '.join(found_types)}."
    else:
        coverage = "Внешние сигналы отсутствуют."

    return SignalBundle(
        question_mode=plan.question_mode,
        retrieval_plan=plan,
        signals=signals,
        quality_summary=quality_summary,
        signal_coverage=coverage,
    )
