"""OSINT foundation entities: QuestionMode, RetrievalPlan, ExternalSignal, SignalBundle."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class QuestionMode(str, Enum):
    """Decision-specific question classification.

    Not just a label — this is the routing primitive for external intelligence.
    Each mode maps to a different retrieval strategy, signal types, and freshness requirements.
    """
    investment = "investment"
    career = "career"
    health_activity = "health_activity"
    education = "education"
    startup = "startup"
    relationship = "relationship"
    relocation = "relocation"
    general_decision = "general_decision"


class FreshnessLabel(str, Enum):
    fresh = "fresh"              # < 24h / very recent
    recent = "recent"            # days–weeks
    timeless_or_unknown = "timeless_or_unknown"


class RetrievalPlan(BaseModel):
    """Describes what external intelligence to gather for a question.

    Built from signal registry based on QuestionMode.
    """
    question_mode: QuestionMode
    signal_types: list[str] = Field(
        default_factory=list,
        description="Types of signals to look for (e.g. 'market_movement', 'hiring_market')",
    )
    source_families: list[str] = Field(
        default_factory=list,
        description="Source categories to search (e.g. 'search/news', 'finance_domains')",
    )
    freshness_priority: Literal["high", "medium", "low"] = "medium"
    search_queries: list[str] = Field(
        default_factory=list,
        description="Targeted search queries to execute",
    )
    personal_factors_to_check: list[str] = Field(
        default_factory=list,
        description="Personal context factors especially critical for fusion with external signals",
    )
    max_signals: int = 5
    notes: str = ""


class ExternalSignal(BaseModel):
    """A single normalized signal from the external world.

    Not a raw web result — a decision-relevant signal with quality metadata.
    """
    signal_type: str = ""
    source_type: Literal["full_text", "snippet", "api_data"] = "snippet"
    source_name: str = ""
    title: str = ""
    url: str = ""
    snippet: str = ""
    timestamp: datetime | None = None
    freshness_label: FreshnessLabel = FreshnessLabel.timeless_or_unknown
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    why_it_matters: str = ""


class SignalBundle(BaseModel):
    """Container for the final set of external signals for a question.

    This is what gets passed to synthesis — not raw text blocks.
    """
    question_mode: QuestionMode
    retrieval_plan: RetrievalPlan
    signals: list[ExternalSignal] = Field(default_factory=list)
    quality_summary: str = ""
    signal_coverage: str = ""  # which signal_types were found vs missing
    fusion_context: str = ""   # derived insights from cross-referencing signals

    def to_synthesis_context(self) -> str:
        """Format signal bundle for LLM synthesis prompt."""
        if not self.signals:
            return (
                f"Question mode: {self.question_mode.value}\n"
                f"Внешние сигналы: не найдены.\n"
                f"Качество: {self.quality_summary or 'источники недоступны'}\n"
                f"Прогноз основан только на личном контексте пользователя."
            )

        lines = [
            f"## Внешние сигналы (mode: {self.question_mode.value})",
            f"Качество: {self.quality_summary}",
            f"Покрытие: {self.signal_coverage}",
            "",
        ]

        for i, sig in enumerate(self.signals, 1):
            freshness = {
                "fresh": "свежий",
                "recent": "недавний",
                "timeless_or_unknown": "без привязки ко времени",
            }.get(sig.freshness_label.value, "")

            lines.append(
                f"{i}. [{sig.signal_type}] {sig.title}\n"
                f"   Релевантность: {sig.relevance_score:.1f} | Качество: {sig.quality_score:.1f} | {freshness}\n"
                f"   {sig.snippet[:500]}\n"
                f"   **Почему важно для решения:** {sig.why_it_matters}\n"
                f"   Источник: {sig.source_name}"
            )

        # Fusion context (derived insights from cross-referencing signals)
        if self.fusion_context:
            lines.append("")
            lines.append(self.fusion_context)

        # Personal factors to check reminder
        pf = self.retrieval_plan.personal_factors_to_check
        if pf:
            lines.append(f"\n## Личные факторы, критичные для fusion с этими сигналами:")
            for f in pf:
                lines.append(f"  - {f}")

        return "\n".join(lines)

    def to_sources_list(self) -> list[dict]:
        """Extract source metadata for API response."""
        sources = []
        for sig in self.signals:
            if sig.url:
                domain = ""
                try:
                    domain = sig.url.split("/")[2]
                except (IndexError, AttributeError):
                    pass
                sources.append({
                    "title": sig.title,
                    "url": sig.url,
                    "domain": domain,
                })
        return sources
