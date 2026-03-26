from fastapi import APIRouter

from backend.models.schemas import (
    APIResponse,
    OnboardingStart,
    OnboardingMessage,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/start", response_model=APIResponse)
async def start_onboarding(payload: OnboardingStart):
    # TODO: Initialize conversation agent and start onboarding
    return APIResponse(
        success=True,
        data={"session_id": "todo", "message": "Onboarding started"},
    )


@router.post("/message", response_model=APIResponse)
async def send_message(payload: OnboardingMessage):
    # TODO: Forward message to conversation agent
    return APIResponse(
        success=True,
        data={"reply": "TODO: agent response", "completed": False},
    )
