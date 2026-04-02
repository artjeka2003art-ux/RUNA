from fastapi import APIRouter, Request

from backend.models.schemas import (
    APIResponse,
    SphereCreate,
    SphereRename,
    SphereMessageRequest,
)

router = APIRouter(prefix="/spheres", tags=["spheres"])


@router.get("/{user_id}", response_model=APIResponse)
async def list_spheres(user_id: str, request: Request):
    """Get all active spheres for a user."""
    graph_builder = request.app.state.graph_builder
    life_score_engine = request.app.state.life_score_engine

    try:
        rows = await graph_builder.get_spheres(user_id)

        # Enrich with scores
        score_data = await life_score_engine.calculate(user_id)
        score_map = {s.sphere: s.score for s in score_data.spheres}

        spheres = []
        for r in rows:
            spheres.append({
                "id": r["id"],
                "name": r["name"],
                "description": r.get("description", ""),
                "score": score_map.get(r["name"]),
                "archived": False,
            })

        return APIResponse(success=True, data={"spheres": spheres})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{user_id}/{sphere_id}", response_model=APIResponse)
async def get_sphere_detail(user_id: str, sphere_id: str, request: Request):
    """Get full sphere detail with related entities."""
    graph_builder = request.app.state.graph_builder
    life_score_engine = request.app.state.life_score_engine

    try:
        row = await graph_builder.get_sphere_detail(user_id, sphere_id)
        if not row:
            return APIResponse(success=False, error="Sphere not found")

        # Parse related nodes by type
        related = row.get("related", [])
        blockers, goals, patterns, values = [], [], [], []

        for node in related:
            if node is None:
                continue
            labels = set(node.get("labels", []))
            item = {
                "type": (labels - {"__all__"}).pop() if labels else "Unknown",
                "name": node.get("name", ""),
                "description": node.get("description", ""),
                "weight": node.get("weight", 0.5),
            }
            if "Blocker" in labels:
                blockers.append(item)
            elif "Goal" in labels:
                goals.append(item)
            elif "Pattern" in labels:
                patterns.append(item)
            elif "Value" in labels:
                values.append(item)

        # Score
        score_data = await life_score_engine.calculate(user_id)
        score_map = {s.sphere: s.score for s in score_data.spheres}

        # Related spheres
        related_spheres = await graph_builder.get_related_spheres(user_id, sphere_id)

        detail = {
            "id": row["id"],
            "name": row["name"],
            "description": row.get("description", ""),
            "score": score_map.get(row["name"]),
            "related_blockers": blockers,
            "related_goals": goals,
            "related_patterns": patterns,
            "related_values": values,
            "related_spheres": related_spheres,
        }

        return APIResponse(success=True, data={"sphere": detail})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("", response_model=APIResponse)
async def create_sphere(payload: SphereCreate, request: Request):
    """Create a new sphere and generate AI intro message."""
    graph_builder = request.app.state.graph_builder
    sphere_agent = request.app.state.sphere_agent

    try:
        result = await graph_builder.create_sphere(payload.user_id, payload.name)
        if not result:
            return APIResponse(success=False, error="Failed to create sphere")

        sphere_id = result["id"]

        # Generate AI intro for this new sphere
        intro = ""
        try:
            intro = await sphere_agent.generate_intro(payload.user_id, payload.name)
        except Exception:
            pass

        return APIResponse(success=True, data={
            "sphere": {
                "id": sphere_id,
                "name": result["name"],
                "description": "",
                "score": None,
                "archived": False,
            },
            "intro": intro,
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.patch("/{sphere_id}", response_model=APIResponse)
async def rename_sphere(sphere_id: str, payload: SphereRename, request: Request):
    """Rename a sphere."""
    graph_builder = request.app.state.graph_builder

    try:
        result = await graph_builder.rename_sphere(sphere_id, payload.name)
        if not result:
            return APIResponse(success=False, error="Sphere not found")

        return APIResponse(success=True, data={
            "sphere": {
                "id": result["id"],
                "name": result["name"],
            }
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.delete("/{sphere_id}", response_model=APIResponse)
async def delete_sphere(sphere_id: str, user_id: str, request: Request):
    """Archive (soft-delete) a sphere."""
    graph_builder = request.app.state.graph_builder

    try:
        ok = await graph_builder.archive_sphere(sphere_id)
        if not ok:
            return APIResponse(success=False, error="Sphere not found")

        return APIResponse(success=True, data={"archived": True})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/{sphere_id}/message", response_model=APIResponse)
async def sphere_message(sphere_id: str, payload: SphereMessageRequest, request: Request):
    """Send a message in sphere chat. AI responds with sphere context, then analyst updates graph."""
    sphere_agent = request.app.state.sphere_agent
    analyst = request.app.state.analyst_agent
    graph_builder = request.app.state.graph_builder
    life_score_engine = request.app.state.life_score_engine

    try:
        # 1. Get sphere info
        from backend.graph import graph_queries
        neo4j = request.app.state.neo4j
        rows = await neo4j.execute_query(*graph_queries.get_sphere_by_id(sphere_id))
        if not rows:
            return APIResponse(success=False, error="Sphere not found")

        sphere = rows[0]
        sphere_name = sphere["name"]

        # 2. AI responds
        reply = await sphere_agent.respond(
            user_id=payload.user_id,
            sphere_id=sphere_id,
            sphere_name=sphere_name,
            message=payload.message,
        )

        # 3. Log as checkin
        await graph_builder.add_checkin(payload.user_id, f"[{sphere_name}] {payload.message}")

        # 4. Analyst updates full graph — with sphere context
        analysis = {"changes": 0}
        try:
            analysis = await analyst.run_after_checkin(
                user_id=payload.user_id,
                user_message=payload.message,
                companion_reply=reply,
                sphere_context={"sphere_id": sphere_id, "sphere_name": sphere_name},
            )
        except Exception:
            pass

        # 5. Update sphere description if empty or after meaningful exchange
        sphere_desc = sphere.get("description", "")
        try:
            if not sphere_desc or len(sphere_desc) < 5:
                sphere_desc = await sphere_agent.generate_description(
                    payload.user_id, sphere_name, payload.message,
                )
                await graph_builder.update_sphere_description(sphere_id, sphere_desc)
        except Exception:
            pass

        # 6. Calculate score
        life_score = await life_score_engine.calculate(payload.user_id)
        await life_score_engine.commit_score_snapshot(payload.user_id, life_score)

        score_map = {s.sphere: s.score for s in life_score.spheres}

        return APIResponse(success=True, data={
            "reply": reply,
            "sphere": {
                "id": sphere_id,
                "name": sphere_name,
                "description": sphere_desc,
                "score": score_map.get(sphere_name),
                "archived": False,
            },
            "graph_updates": {
                "weights_updated": analysis.get("weights_updated", 0),
                "nodes_created": analysis.get("nodes_created", 0),
                "resolved": analysis.get("resolved", 0),
            },
            "life_score": life_score.total,
            "score_delta": life_score.score_delta,
        })
    except Exception as e:
        return APIResponse(success=False, error=str(e))
