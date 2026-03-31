from fastapi import APIRouter, Request

from backend.models.schemas import APIResponse, CheckInCreate
from backend.graph import graph_queries

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("/message", response_model=APIResponse)
async def checkin_message(payload: CheckInCreate, request: Request):
    companion = request.app.state.companion_agent
    analyst = request.app.state.analyst_agent
    graph_builder = request.app.state.graph_builder
    life_score_engine = request.app.state.life_score_engine

    try:
        # 1. Companion Agent responds to the user
        reply = await companion.respond(payload.user_id, payload.message)

        # 2. Save check-in to graph
        await graph_builder.add_checkin(payload.user_id, payload.message)

        # 3. Analyst Agent analyzes and updates the graph (non-blocking)
        analysis = {"changes": 0}
        try:
            analysis = await analyst.run_after_checkin(
                user_id=payload.user_id,
                user_message=payload.message,
                companion_reply=reply,
            )
        except Exception as exc:
            import sys, traceback
            print(f"[ANALYST ERROR] {exc}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)

        # 4. Recalculate Life Score AFTER analyst updated the graph
        life_score = await life_score_engine.calculate(payload.user_id)

        return APIResponse(success=True, data={
            "reply": reply,
            "life_score": life_score.model_dump(),
            "graph_updates": analysis,
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))
