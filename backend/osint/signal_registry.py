"""Signal registry: decision-specific retrieval configuration per QuestionMode.

For each question mode, defines:
- what signal types matter
- what source families to use
- freshness requirements
- personal factors critical for fusion
- search query templates
"""

from __future__ import annotations

from .models import QuestionMode, RetrievalPlan


# ── Registry entries ─────────────────────────────────────────────────

_REGISTRY: dict[QuestionMode, dict] = {
    QuestionMode.investment: {
        "signal_types": [
            "market_movement",
            "volatility_context",
            "macro_news",
            "regulation_signal",
            "geopolitical_event",
            "expert_forecast",
        ],
        "source_families": ["market_data_api", "sentiment_api", "search/news", "finance_domains"],
        "has_structured_adapter": True,  # market_data + sentiment adapters
        "freshness_priority": "high",
        "personal_factors_to_check": [
            "финансовая подушка / runway",
            "горизонт инвестирования",
            "толерантность к потерям",
            "текущий портфель / активы",
            "уровень финансовой грамотности",
        ],
        "preferred_domains": [
            "bloomberg.com", "reuters.com", "ft.com", "wsj.com",
            "cnbc.com", "investopedia.com", "seekingalpha.com",
            "coindesk.com", "coingecko.com", "tradingview.com",
        ],
        "query_templates": [
            "{asset_or_topic} market outlook {year}",
            "{asset_or_topic} price forecast risks",
            "{asset_or_topic} investment analysis current conditions",
        ],
        "max_signals": 5,
    },
    QuestionMode.career: {
        "signal_types": [
            "hiring_market",
            "company_context",
            "role_demand",
            "industry_conditions",
            "salary_benchmark",
            "layoff_signal",
        ],
        "source_families": ["search/news", "career_domains"],
        "freshness_priority": "medium",
        "personal_factors_to_check": [
            "финансовая подушка / runway",
            "текущий уровень выгорания",
            "наличие альтернатив / офферов",
            "контрактные обязательства",
            "зависимые (семья, ипотека)",
        ],
        "preferred_domains": [
            "hbr.org", "glassdoor.com", "linkedin.com",
            "levels.fyi", "indeed.com", "bls.gov",
        ],
        "query_templates": [
            "{role_or_industry} job market {year} outlook",
            "{role_or_industry} hiring trends layoffs",
            "career change {field} risks success factors",
        ],
        "max_signals": 4,
    },
    QuestionMode.health_activity: {
        "signal_types": [
            "weather_conditions",
            "air_quality",
            "health_advisory",
            "training_science",
            "recovery_factors",
        ],
        "source_families": ["search/news", "health_domains"],
        "freshness_priority": "high",
        "personal_factors_to_check": [
            "текущее физическое состояние",
            "режим сна / восстановление",
            "текущая нагрузка (тренировочная)",
            "хронические условия / травмы",
            "цели по здоровью",
        ],
        "preferred_domains": [
            "mayoclinic.org", "nih.gov", "webmd.com",
            "pubmed.ncbi.nlm.nih.gov", "healthline.com",
        ],
        "query_templates": [
            "{activity} safety guidelines conditions",
            "{activity} recovery training frequency evidence",
            "{health_topic} current research recommendations",
        ],
        "max_signals": 3,
    },
    QuestionMode.education: {
        "signal_types": [
            "program_reputation",
            "market_value_of_degree",
            "admission_trends",
            "career_outcomes",
            "cost_benefit",
        ],
        "source_families": ["search/news", "education_domains"],
        "freshness_priority": "medium",
        "personal_factors_to_check": [
            "текущий уровень образования",
            "финансовые возможности / стипендии",
            "карьерная цель после обучения",
            "время / возможность совмещения",
            "альтернативные пути (курсы, self-study)",
        ],
        "preferred_domains": [
            "timeshighereducation.com", "topuniversities.com",
            "niche.com", "usnews.com", ".edu",
        ],
        "query_templates": [
            "{program_or_field} degree value {year}",
            "{program_or_field} career outcomes salary",
            "{program_or_field} vs alternative learning paths",
        ],
        "max_signals": 4,
    },
    QuestionMode.startup: {
        "signal_types": [
            "market_size",
            "funding_climate",
            "competitor_landscape",
            "regulatory_environment",
            "founder_success_factors",
        ],
        "source_families": ["search/news", "startup_domains"],
        "freshness_priority": "medium",
        "personal_factors_to_check": [
            "финансовый runway",
            "опыт в домене",
            "наличие команды / кофаундера",
            "готовность к риску",
            "текущие обязательства (работа, семья)",
        ],
        "preferred_domains": [
            "techcrunch.com", "crunchbase.com", "ycombinator.com",
            "a16z.com", "firstround.com", "hbr.org",
        ],
        "query_templates": [
            "{domain} startup market {year}",
            "{domain} startup success failure factors",
            "bootstrapping vs funding {domain} {year}",
        ],
        "max_signals": 4,
    },
    QuestionMode.relationship: {
        "signal_types": [
            "relationship_research",
            "psychological_patterns",
            "communication_strategies",
            "life_transition_impact",
        ],
        "source_families": ["search/news", "psychology_domains"],
        "freshness_priority": "low",
        "personal_factors_to_check": [
            "длительность отношений",
            "наличие общих обязательств (дети, жильё)",
            "текущий эмоциональный фон",
            "поддержка окружения",
            "предыдущий опыт / паттерны",
        ],
        "preferred_domains": [
            "psychologytoday.com", "gottman.com", "apa.org",
            "ncbi.nlm.nih.gov",
        ],
        "query_templates": [
            "{topic} relationship research outcomes",
            "{topic} psychological factors decision",
        ],
        "max_signals": 3,
    },
    QuestionMode.relocation: {
        "signal_types": [
            "cost_of_living",
            "quality_of_life",
            "job_market_destination",
            "immigration_policy",
            "expat_experience",
        ],
        "source_families": ["search/news", "relocation_domains"],
        "freshness_priority": "medium",
        "personal_factors_to_check": [
            "финансовая готовность к переезду",
            "языковые навыки",
            "карьерные перспективы в новом месте",
            "семья / близкие (кто переезжает)",
            "текущие обязательства (аренда, работа)",
        ],
        "preferred_domains": [
            "numbeo.com", "expatica.com", "internations.org",
        ],
        "query_templates": [
            "{destination} cost of living quality of life {year}",
            "{destination} expat experience pros cons",
            "relocating to {destination} job market {industry}",
        ],
        "max_signals": 4,
    },
    QuestionMode.general_decision: {
        "signal_types": [
            "expert_framework",
            "research_evidence",
            "statistical_context",
        ],
        "source_families": ["search/news"],
        "freshness_priority": "low",
        "personal_factors_to_check": [
            "ключевые ограничения",
            "приоритеты / ценности",
            "временной горизонт решения",
        ],
        "preferred_domains": [],
        "query_templates": [
            "{topic} decision framework research",
            "{topic} outcomes risks evidence",
        ],
        "max_signals": 3,
    },
}


def get_retrieval_plan(mode: QuestionMode, search_queries: list[str] | None = None) -> RetrievalPlan:
    """Build a RetrievalPlan from signal registry for the given mode."""
    entry = _REGISTRY.get(mode, _REGISTRY[QuestionMode.general_decision])
    return RetrievalPlan(
        question_mode=mode,
        signal_types=entry["signal_types"],
        source_families=entry["source_families"],
        freshness_priority=entry["freshness_priority"],
        search_queries=search_queries or [],
        personal_factors_to_check=entry["personal_factors_to_check"],
        max_signals=entry.get("max_signals", 4),
    )


def get_preferred_domains(mode: QuestionMode) -> list[str]:
    """Return preferred domains for a question mode."""
    entry = _REGISTRY.get(mode, _REGISTRY[QuestionMode.general_decision])
    return entry.get("preferred_domains", [])


def get_query_templates(mode: QuestionMode) -> list[str]:
    """Return search query templates for a question mode."""
    entry = _REGISTRY.get(mode, _REGISTRY[QuestionMode.general_decision])
    return entry.get("query_templates", [])
