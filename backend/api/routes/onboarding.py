from fastapi import APIRouter, Request

from backend.models.schemas import (
    APIResponse,
    OnboardingStart,
    OnboardingMessage,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/start", response_model=APIResponse)
async def start_onboarding(payload: OnboardingStart, request: Request):
    agent = request.app.state.conversation_agent
    try:
        result = await agent.start_onboarding(payload.user_id)
        return APIResponse(success=True, data=result)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/message", response_model=APIResponse)
async def send_message(payload: OnboardingMessage, request: Request):
    agent = request.app.state.conversation_agent
    try:
        result = await agent.process_onboarding_message(
            user_id=payload.user_id,
            session_id=payload.session_id,
            message=payload.message,
        )

        # Commit first score snapshot when onboarding completes
        if result.get("completed"):
            try:
                life_score_engine = request.app.state.life_score_engine
                score = await life_score_engine.calculate(payload.user_id)
                await life_score_engine.commit_score_snapshot(payload.user_id, score)
            except Exception:
                pass  # Non-blocking — onboarding result is more important

        return APIResponse(success=True, data=result)
    except ValueError as e:
        return APIResponse(success=False, error=str(e))
    except Exception as e:
        return APIResponse(success=False, error=str(e))
