from datetime import datetime
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


class SphereMessageRequest(BaseModel):
    user_id: str
    message: str


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


class APIResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None
