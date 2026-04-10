from fastapi import APIRouter, Request

from backend.models.schemas import APIResponse, OneMoveFeedback, InvestmentProfile, InvestmentProfileUpdate
from backend.graph import graph_queries

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{user_id}/score", response_model=APIResponse)
async def get_life_score(user_id: str, request: Request):
    life_score_engine = request.app.state.life_score_engine
    try:
        score = await life_score_engine.calculate(user_id)
        return APIResponse(success=True, data=score.model_dump())
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{user_id}/graph", response_model=APIResponse)
async def get_graph(user_id: str, request: Request):
    graph = request.app.state.neo4j
    try:
        query, params = graph_queries.get_user_graph(user_id)
        rows = await graph.execute_query(query, params)

        nodes = set()
        edges = []
        for row in rows:
            from_name = row.get("from_name", "")
            to_name = row.get("to_name", "")
            from_label = row.get("from_labels", [""])[0]
            to_label = row.get("to_labels", [""])[0]

            nodes.add((from_label, from_name))
            nodes.add((to_label, to_name))
            edges.append({
                "from": from_name,
                "to": to_name,
                "type": row.get("edge_type", ""),
                "weight": row.get("weight", 0),
            })

        node_list = [{"label": label, "name": name} for label, name in nodes]

        return APIResponse(success=True, data={
            "user_id": user_id,
            "nodes": node_list,
            "edges": edges,
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{user_id}/score-history", response_model=APIResponse)
async def get_score_history(user_id: str, request: Request):
    """Return last N Life Score snapshots for trend display."""
    graph = request.app.state.neo4j
    try:
        query = """
        MATCH (sh:ScoreHistory {user_id: $uid})
        RETURN sh.total AS total, sh.created_at AS created_at
        ORDER BY sh.created_at DESC
        LIMIT 14
        """
        rows = await graph.execute_query(query, {"uid": user_id})
        # Return in chronological order
        history = [
            {"total": round(r["total"], 1), "created_at": str(r["created_at"])}
            for r in reversed(rows)
        ]
        return APIResponse(success=True, data={
            "user_id": user_id,
            "history": history,
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{user_id}/compass", response_model=APIResponse)
async def get_daily_compass(user_id: str, request: Request):
    """Daily Compass — retention core of the Today screen."""
    life_score_engine = request.app.state.life_score_engine
    try:
        compass = await life_score_engine.calculate_compass(user_id)
        return APIResponse(success=True, data=compass.model_dump())
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/{user_id}/one-move-feedback", response_model=APIResponse)
async def submit_one_move_feedback(user_id: str, body: OneMoveFeedback, request: Request):
    """Record whether user completed their one move. Deduplicates by one_move text."""
    graph = request.app.state.neo4j
    try:
        status = body.status
        if status not in ("done", "not_done"):
            return APIResponse(success=False, error="status must be 'done' or 'not_done'")

        # ── Deduplicate: check if feedback for this exact one_move already exists
        q_dup = """
        MATCH (af:ActionFeedback {user_id: $uid})
        WHERE af.one_move = $one_move
          AND af.created_at > datetime() - duration('PT12H')
        RETURN af.status AS status
        LIMIT 1
        """
        dup_rows = await graph.execute_query(q_dup, {"uid": user_id, "one_move": body.one_move})
        if dup_rows:
            prev = dup_rows[0].get("status", "")
            return APIResponse(success=True, data={
                "status": prev,
                "message": "Уже учтено. Система запомнила твой ответ.",
                "score_impact": 0,
                "duplicate": True,
            })

        # ── Save feedback node
        q, p = graph_queries.create_action_feedback(
            user_id, status, body.one_move, body.sphere_name,
        )
        await graph.execute_query(q, p)

        # ── If done: slightly boost focus sphere's positive edges
        score_impact = 0.0
        if status == "done" and body.sphere_name:
            try:
                q_boost = """
                MATCH (n)-[r]->(s:Sphere {user_id: $uid, name: $sname})
                WHERE (n:Goal OR n:Value) AND r.weight < 1.0
                WITH n, r, s ORDER BY r.weight ASC LIMIT 1
                SET r.weight = CASE WHEN r.weight + 0.05 > 1.0 THEN 1.0
                                    ELSE r.weight + 0.05 END,
                    r.updated_at = datetime()
                RETURN n.name AS boosted, r.weight AS new_weight
                """
                rows = await graph.execute_query(q_boost, {"uid": user_id, "sname": body.sphere_name})
                if rows:
                    score_impact = 0.05 * 15.0
            except Exception:
                pass

        if status == "done":
            message = "Зафиксировано. Это реальный шаг — система учтёт его в твоей траектории."
        else:
            message = "Честно — тоже важно. Система видит это и учтёт при следующем расчёте."

        return APIResponse(success=True, data={
            "status": status,
            "message": message,
            "score_impact": round(score_impact, 1),
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{user_id}/investment-profile", response_model=APIResponse)
async def get_investment_profile(user_id: str, request: Request):
    graph_builder = request.app.state.graph_builder
    try:
        data = await graph_builder.get_investment_profile(user_id)
        return APIResponse(success=True, data={"profile": data})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/{user_id}/investment-profile", response_model=APIResponse)
async def save_investment_profile(user_id: str, body: InvestmentProfileUpdate, request: Request):
    graph_builder = request.app.state.graph_builder
    try:
        profile_dict = body.profile.model_dump(exclude_none=True, exclude_defaults=False)
        # Remove empty strings to keep storage clean
        profile_dict = {k: v for k, v in profile_dict.items() if v != "" and v is not None}
        ok = await graph_builder.save_investment_profile(user_id, profile_dict)
        return APIResponse(success=True, data={"saved": ok, "profile": profile_dict})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{user_id}/scenarios", response_model=APIResponse)
async def get_scenarios(user_id: str, request: Request):
    """Generate prediction via graph math + Claude narratives."""
    scenario_agent = request.app.state.scenario_agent

    try:
        report = await scenario_agent.generate_scenarios(user_id)

        if report.get("error") == "no_data":
            return APIResponse(success=True, data={
                "user_id": user_id,
                "scenarios": [],
                "message": "Недостаточно данных для prediction. Пройдите онбординг и сделайте несколько чекинов.",
            })

        return APIResponse(success=True, data={
            "user_id": user_id,
            **report,
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))


# ── Promoted facts (persistent world model) control API ────────────

import json as _json
from pydantic import BaseModel
from datetime import datetime, timezone


class PromotedFactAction(BaseModel):
    user_id: str
    fact_key: str
    source_document_id: str = ""


class DocumentInvalidateAction(BaseModel):
    user_id: str
    source_document_id: str
    reason: str = ""


async def _load_facts(request: Request, user_id: str) -> list:
    graph = request.app.state.neo4j
    q, p = graph_queries.get_promoted_facts(user_id)
    rows = await graph.execute_query(q, p)
    if rows and rows[0].get("promoted_facts"):
        return _json.loads(rows[0]["promoted_facts"])
    return []


async def _save_facts(request: Request, user_id: str, facts: list) -> None:
    graph = request.app.state.neo4j
    q, p = graph_queries.save_promoted_facts(user_id, _json.dumps(facts, ensure_ascii=False))
    await graph.execute_query(q, p)


@router.get("/{user_id}/promoted-facts", response_model=APIResponse)
async def list_promoted_facts(user_id: str, request: Request):
    """List all promoted facts for a user (any state)."""
    try:
        facts = await _load_facts(request, user_id)
        return APIResponse(success=True, data={"promoted_facts": facts})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/promoted-facts/confirm", response_model=APIResponse)
async def confirm_promoted_fact(payload: PromotedFactAction, request: Request):
    """Promote pending fact to user_confirmed (authoritative)."""
    try:
        facts = await _load_facts(request, payload.user_id)
        now = datetime.now(timezone.utc).isoformat()
        found = False
        for f in facts:
            if f.get("fact_key") == payload.fact_key and (
                not payload.source_document_id or f.get("source_document_id") == payload.source_document_id
            ):
                if f.get("state") in ("pending_confirmation", "active"):
                    # Also supersede any other active fact with same key
                    for other in facts:
                        if other is f:
                            continue
                        if other.get("fact_key") == payload.fact_key and other.get("state") in ("active", "user_confirmed"):
                            other["state"] = "superseded"
                            other["superseded_at"] = now
                            other["superseded_reason"] = "replaced by user-confirmed fact"
                    f["state"] = "user_confirmed"
                    f["confirmed_at"] = now
                    found = True
        if not found:
            return APIResponse(success=False, error="Fact not found")
        await _save_facts(request, payload.user_id, facts)
        return APIResponse(success=True, data={"promoted_facts": facts})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/promoted-facts/dismiss", response_model=APIResponse)
async def dismiss_promoted_fact(payload: PromotedFactAction, request: Request):
    """Dismiss a pending/suggested fact (will not be used in reasoning)."""
    try:
        facts = await _load_facts(request, payload.user_id)
        now = datetime.now(timezone.utc).isoformat()
        found = False
        for f in facts:
            if f.get("fact_key") == payload.fact_key and (
                not payload.source_document_id or f.get("source_document_id") == payload.source_document_id
            ):
                f["state"] = "user_dismissed"
                f["dismissed_at"] = now
                found = True
        if not found:
            return APIResponse(success=False, error="Fact not found")
        await _save_facts(request, payload.user_id, facts)
        return APIResponse(success=True, data={"promoted_facts": facts})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/promoted-facts/invalidate-document", response_model=APIResponse)
async def invalidate_document(payload: DocumentInvalidateAction, request: Request):
    """Bulk-invalidate all promoted facts from a given source document.

    Semantics: document is no longer treated as a source of active persistent truth.
    All active / pending / user_confirmed facts with matching source_document_id
    transition to state 'invalidated_by_document'. History is preserved (trace stays).
    """
    try:
        from backend.agents.prediction_query_agent import invalidate_facts_by_document
        facts = await _load_facts(request, payload.user_id)
        reason = payload.reason or "document marked as no longer current"
        updated, count = invalidate_facts_by_document(facts, payload.source_document_id, reason)
        if count == 0:
            return APIResponse(success=True, data={"promoted_facts": updated, "invalidated_count": 0})
        await _save_facts(request, payload.user_id, updated)
        return APIResponse(success=True, data={"promoted_facts": updated, "invalidated_count": count})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/promoted-facts/deactivate", response_model=APIResponse)
async def deactivate_promoted_fact(payload: PromotedFactAction, request: Request):
    """Mark an active fact as no longer current (e.g., user changed jobs)."""
    try:
        facts = await _load_facts(request, payload.user_id)
        now = datetime.now(timezone.utc).isoformat()
        found = False
        for f in facts:
            if f.get("fact_key") == payload.fact_key and (
                not payload.source_document_id or f.get("source_document_id") == payload.source_document_id
            ):
                f["state"] = "deactivated"
                f["deactivated_at"] = now
                found = True
        if not found:
            return APIResponse(success=False, error="Fact not found")
        await _save_facts(request, payload.user_id, facts)
        return APIResponse(success=True, data={"promoted_facts": facts})
    except Exception as e:
        return APIResponse(success=False, error=str(e))
