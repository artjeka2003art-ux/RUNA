from fastapi import APIRouter, Request

from backend.models.schemas import APIResponse
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
