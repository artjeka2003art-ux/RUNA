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

        # Commit first score snapshot + return spheres for reveal
        if result.get("completed"):
            try:
                life_score_engine = request.app.state.life_score_engine
                score = await life_score_engine.calculate(payload.user_id)
                await life_score_engine.commit_score_snapshot(payload.user_id, score)

                # Add spheres data for reveal screen
                graph_builder = request.app.state.graph_builder
                sphere_rows = await graph_builder.get_spheres(payload.user_id)
                score_map = {s.sphere: s.score for s in score.spheres}
                result["spheres"] = [
                    {
                        "id": r["id"],
                        "name": r["name"],
                        "description": r.get("description", ""),
                        "score": score_map.get(r["name"]),
                    }
                    for r in sphere_rows
                ]
                result["life_score"] = score.total
            except Exception:
                pass  # Non-blocking — onboarding result is more important

        return APIResponse(success=True, data=result)
    except ValueError as e:
        return APIResponse(success=False, error=str(e))
    except Exception as e:
        return APIResponse(success=False, error=str(e))
