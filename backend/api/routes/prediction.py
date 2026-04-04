from fastapi import APIRouter, Request

from backend.models.schemas import APIResponse, PredictionQuery

router = APIRouter(prefix="/prediction", tags=["prediction"])


@router.post("/query", response_model=APIResponse)
async def prediction_query(body: PredictionQuery, request: Request):
    """Query-based prediction: user asks a question, system answers with structured analysis."""
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
