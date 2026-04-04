from fastapi import APIRouter, Request

from backend.models.schemas import APIResponse, PredictionQuery, WorkspaceQuery

router = APIRouter(prefix="/prediction", tags=["prediction"])


@router.post("/query", response_model=APIResponse)
async def prediction_query(body: PredictionQuery, request: Request):
    """Legacy single-answer prediction. Kept for backwards compatibility."""
    agent = request.app.state.prediction_query_agent
    try:
        result = await agent.answer(
            user_id=body.user_id,
            question=body.question,
            sphere_id=body.sphere_id,
        )
        return APIResponse(success=True, data=result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return APIResponse(success=False, error=str(e))


@router.post("/workspace", response_model=APIResponse)
async def prediction_workspace(body: WorkspaceQuery, request: Request):
    """Decision Workspace: question → scenario variants → reports → comparison → missing context."""
    agent = request.app.state.prediction_query_agent
    try:
        result = await agent.workspace(
            user_id=body.user_id,
            question=body.question,
            sphere_id=body.sphere_id,
            variants=body.variants if body.variants else None,
        )
        return APIResponse(success=True, data=result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return APIResponse(success=False, error=str(e))
