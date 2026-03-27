from fastapi import APIRouter, Request

from backend.models.schemas import APIResponse, CheckInCreate
from backend.graph import graph_queries

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("/message", response_model=APIResponse)
async def checkin_message(payload: CheckInCreate, request: Request):
    companion = request.app.state.companion_agent
    graph = request.app.state.neo4j
    graph_builder = request.app.state.graph_builder
    life_score_engine = request.app.state.life_score_engine

    try:
        # 1. Companion Agent responds
        reply = await companion.respond(payload.user_id, payload.message)

        # 2. Save check-in to graph
        await graph_builder.add_checkin(payload.user_id, payload.message)

        # 3. Recalculate Life Score
        life_score = await life_score_engine.calculate(payload.user_id)

        return APIResponse(success=True, data={
            "reply": reply,
            "life_score": life_score.model_dump(),
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))
