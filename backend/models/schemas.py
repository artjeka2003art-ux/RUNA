from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str
    name: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime


class OnboardingStart(BaseModel):
    user_id: str


class OnboardingMessage(BaseModel):
    user_id: str
    session_id: str
    message: str
    force_complete: bool = False


class OnboardingResult(BaseModel):
    session_id: str
    completed: bool
    spheres_identified: list[str] = Field(default_factory=list)
    nodes_created: int = 0


class CheckInCreate(BaseModel):
    user_id: str
    message: str


class CheckInResponse(BaseModel):
    user_id: str
    session_id: str
    reply: str
    life_score: "LifeScore | None" = None


class SphereScore(BaseModel):
    sphere: str
    score: float = Field(ge=0, le=100)
    delta: float = 0.0
    reason: str = ""


class NextStep(BaseModel):
    action: str = ""
    why: str = ""
    outcome: str = ""


class LifeScore(BaseModel):
    user_id: str
    total: float = Field(ge=0, le=100)
    spheres: list[SphereScore] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    daily_state: str = ""
    daily_state_reason: str = ""
    score_delta: float = 0.0
    next_step: NextStep = Field(default_factory=NextStep)


class SphereItem(BaseModel):
    """Sphere in a list view."""
    id: str
    name: str
    description: str = ""
    score: float | None = None
    archived: bool = False


class SphereRelatedNode(BaseModel):
    """A node related to a sphere (blocker, goal, pattern, value)."""
    type: str
    name: str
    description: str = ""
    weight: float = 0.5


class SphereDetail(BaseModel):
    """Full sphere view with related entities."""
    id: str
    name: str
    description: str = ""
    score: float | None = None
    related_blockers: list[SphereRelatedNode] = Field(default_factory=list)
    related_goals: list[SphereRelatedNode] = Field(default_factory=list)
    related_patterns: list[SphereRelatedNode] = Field(default_factory=list)
    related_values: list[SphereRelatedNode] = Field(default_factory=list)
    related_spheres: list[str] = Field(default_factory=list)


class SphereCreate(BaseModel):
    user_id: str
    name: str


class SphereRename(BaseModel):
    user_id: str
    name: str


class EnrichmentContext(BaseModel):
    """Context passed from Decision Workspace when user enters sphere to fill a gap."""
    missing_what: str = ""
    missing_why: str = ""
    question: str = ""


class SphereMessageRequest(BaseModel):
    user_id: str
    message: str
    enrichment_context: EnrichmentContext | None = None


class SphereMessageResponse(BaseModel):
    reply: str
    sphere: SphereItem
    graph_updates: dict = Field(default_factory=dict)
    life_score: float | None = None
    score_delta: float | None = None


class FocusSphere(BaseModel):
    id: str
    name: str
    score: float = 0.0


class ActionTrace(BaseModel):
    status: str = ""  # "done" | "not_done"
    message: str = ""
    sphere_name: str = ""


class DailyCompass(BaseModel):
    daily_state: str = ""
    daily_state_reason: str = ""
    key_shift_title: str = ""
    key_shift_reason: str = ""
    focus_sphere: FocusSphere | None = None
    one_move: str = ""
    one_move_reason: str = ""
    cost_of_ignoring: str = ""
    last_action_trace: ActionTrace | None = None


class OneMoveFeedback(BaseModel):
    user_id: str
    status: str  # "done" | "not_done"
    one_move: str = ""
    sphere_name: str = ""


class OneMoveFeedbackResponse(BaseModel):
    status: str
    message: str
    score_impact: float = 0.0


class PredictionQuery(BaseModel):
    user_id: str
    question: str
    sphere_id: str | None = None


class PredictionInfluencer(BaseModel):
    type: str = ""       # "blocker" | "pattern" | "goal" | "value" | "action_feedback"
    name: str = ""
    detail: str = ""


class PredictionScenario(BaseModel):
    label: str = ""      # "most_likely" | "alternative"
    title: str = ""
    description: str = ""


class PredictionSource(BaseModel):
    title: str = ""
    url: str = ""
    domain: str = ""


class PredictionResponse(BaseModel):
    question_type: str = ""         # decision | trajectory | change_impact | relationship | pattern_risk
    restated_question: str = ""
    summary: str = ""
    influencers: list[PredictionInfluencer] = Field(default_factory=list)
    external_insights: str = ""
    scenarios: list[PredictionScenario] = Field(default_factory=list)
    depends_on: str = ""
    next_step: str = ""
    sources: list[PredictionSource] = Field(default_factory=list)


# ── Decision Workspace entities ──────────────────────────────────


class QuestionType(str, Enum):
    decision = "decision"
    trajectory = "trajectory"
    change_impact = "change_impact"
    relationship = "relationship"
    pattern_risk = "pattern_risk"


# Re-export OSINT models for convenience
from backend.osint.models import QuestionMode, ExternalSignal, SignalBundle  # noqa: E402, F401


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# --- Request ---


class WorkspaceQuery(BaseModel):
    """User submits a question + optional scenario variants."""
    user_id: str
    question: str
    sphere_id: str | None = None
    variants: list[str] = Field(
        default_factory=list,
        description="User-defined scenario labels, e.g. ['уволиться в июне', 'остаться ещё на 3 месяца']",
    )


# --- Domain entities ---


class MissingContextItem(BaseModel):
    what: str = ""
    why_important: str = ""
    sphere_hint: str = ""
    # Routing v2 fields
    routing_mode: Literal[
        "existing_sphere", "multiple_candidates", "suggest_new_sphere"
    ] = "existing_sphere"
    candidate_spheres: list[str] = Field(
        default_factory=list,
        description="Sphere names for multiple_candidates mode",
    )
    suggested_sphere_name: str = ""
    routing_reason: str = ""


class QueryAssumption(BaseModel):
    """A base-context assumption implied by the question but not confirmed in world model."""
    assumption_text: str = ""
    domain: str = ""  # e.g. "work", "finance", "relationship"
    status: Literal["confirmed", "query_implied", "missing_critical"] = "query_implied"
    affects_confidence: bool = True


class ContextCompleteness(BaseModel):
    score: ConfidenceLevel = ConfidenceLevel.low
    known_factors: list[str] = Field(default_factory=list)
    missing: list[MissingContextItem] = Field(default_factory=list)
    assumptions: list[QueryAssumption] = Field(default_factory=list)


class LeverageFactor(BaseModel):
    factor: str = ""
    direction: str = ""       # e.g. "increases risk" / "improves outcome"
    weight: Literal["high", "medium", "low"] = "medium"


class ScenarioReport(BaseModel):
    """Prediction report for a single scenario variant."""
    variant_label: str = ""
    most_likely_outcome: str = ""
    alternative_outcome: str = ""
    main_risks: list[str] = Field(default_factory=list)
    leverage_factors: list[LeverageFactor] = Field(default_factory=list)
    primary_bottleneck: str = ""
    dominant_downside: str = ""
    non_obvious_insight: str = ""
    condition_that_changes_prediction: str = ""
    decision_signal: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.low
    confidence_reason: str = ""
    affected_spheres: list[str] = Field(default_factory=list)
    depends_on: str = ""
    next_step: str = ""


class ScenarioComparison(BaseModel):
    """Comparison across scenario variants."""
    summary: str = ""
    key_tradeoffs: list[str] = Field(default_factory=list)
    safest_variant: str = ""
    highest_upside_variant: str = ""
    most_sensitive_factor: str = ""
    hidden_trap: str = ""
    ranking_variable: str = ""


# --- Workspace response ---


class WorkspaceResponse(BaseModel):
    """Full Decision Workspace result."""
    question: str = ""
    question_type: QuestionType = QuestionType.trajectory
    question_mode: str = ""  # QuestionMode value (investment, career, etc.)
    restated_question: str = ""
    variants: list[str] = Field(default_factory=list)
    context_completeness: ContextCompleteness = Field(default_factory=ContextCompleteness)
    reports: list[ScenarioReport] = Field(default_factory=list)
    comparison: ScenarioComparison | None = None
    external_insights: str = ""
    sources: list[PredictionSource] = Field(default_factory=list)
    signal_quality: str = ""  # Quality summary from SignalBundle
    signal_coverage: str = ""  # Which signal types found/missing


class APIResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None
