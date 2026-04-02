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


class APIResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None
