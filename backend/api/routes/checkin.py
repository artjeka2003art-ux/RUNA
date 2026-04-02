from fastapi import APIRouter, Request

from backend.models.schemas import APIResponse, CheckInCreate

router = APIRouter(prefix="/checkin", tags=["checkin"])


def _build_checkin_summary(analysis: dict, life_score) -> dict:
    """Build structured checkin_summary from analyst's structured output.

    Uses the analyst's typed fields (weights_updated, nodes_created, resolved)
    instead of regex-parsing free text.
    """
    updates = []
    concerns = []

    for detail in (analysis.get("details") or []):
        text = str(detail)
        # Classify by analyst's structured prefix, not keyword guessing
        if text.startswith("weight:"):
            # Weight change — parse direction from the numbers if possible
            if "Blocker" in text or "blocker" in text:
                concerns.append(text.replace("weight: ", ""))
            else:
                updates.append(text.replace("weight: ", ""))
        elif text.startswith("new Blocker"):
            concerns.append(text.replace("new ", "Новый "))
        elif text.startswith("new "):
            updates.append(text.replace("new ", "Новый узел: "))
        elif text.startswith("resolved"):
            updates.append(text.replace("resolved ", "Снят: "))
        else:
            updates.append(text)

    # Add summary counts if we have structured data
    w = analysis.get("weights_updated", 0)
    n = analysis.get("nodes_created", 0)
    r = analysis.get("resolved", 0)

    if w > 0 and not any("weight" in u.lower() or "->" in u for u in updates):
        updates.append(f"Обновлено {w} связей в графе")
    if n > 0 and not any("новый" in u.lower() or "new" in u.lower() for u in updates):
        updates.append(f"Добавлено {n} новых узлов")
    if r > 0 and not any("снят" in u.lower() or "resolved" in u.lower() for u in updates):
        updates.append(f"Снято {r} блокеров/паттернов")

    return {
        "updates": updates[:5],
        "concerns": concerns[:3],
        "score_delta": life_score.score_delta,
        "new_score": life_score.total,
        "weights_updated": w,
        "nodes_created": n,
        "resolved": r,
    }


@router.post("/message", response_model=APIResponse)
async def checkin_message(payload: CheckInCreate, request: Request):
    companion = request.app.state.companion_agent
    analyst = request.app.state.analyst_agent
    graph_builder = request.app.state.graph_builder
    life_score_engine = request.app.state.life_score_engine

    try:
        reply = await companion.respond(payload.user_id, payload.message)
        await graph_builder.add_checkin(payload.user_id, payload.message)

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

        life_score = await life_score_engine.calculate(payload.user_id)

        # Commit snapshot — this is a real state change (check-in happened)
        await life_score_engine.commit_score_snapshot(payload.user_id, life_score)

        checkin_summary = _build_checkin_summary(analysis, life_score)

        return APIResponse(success=True, data={
            "reply": reply,
            "life_score": life_score.model_dump(),
            "graph_updates": analysis,
            "checkin_summary": checkin_summary,
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))
