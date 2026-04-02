from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries


class GraphBuilder:
    """High-level graph operations built on top of graph_queries."""

    def __init__(self, client: Neo4jClient):
        self.client = client

    async def _run(self, query: str, params: dict) -> list[dict]:
        return await self.client.execute_query(query, params)

    async def init_user_graph(self, user_id: str, name: str, spheres: list[str]) -> dict:
        """Create Person + Spheres + AFFECTS edges. Called after onboarding."""
        await self._run(*graph_queries.create_person(user_id, name))

        for sphere_name in spheres:
            await self._run(*graph_queries.create_sphere(user_id, sphere_name))
            await self._run(*graph_queries.connect_person_to_sphere(user_id, sphere_name))

        return {"person": name, "spheres": spheres, "edges": len(spheres)}

    async def add_event(self, user_id: str, name: str, description: str = "", spheres: list[str] | None = None) -> dict:
        """Create Event node and connect to relevant spheres via CAUSED_BY."""
        await self._run(*graph_queries.create_event(user_id, name, description))

        for sphere_name in (spheres or []):
            await self._run(*graph_queries.create_edge_by_name(
                user_id, "Event", name, "Sphere", sphere_name, "AFFECTS",
            ))

        return {"event": name, "connected_spheres": spheres or []}

    async def add_pattern(self, user_id: str, name: str, description: str = "", spheres: list[str] | None = None) -> dict:
        """Create Pattern node and connect to relevant spheres."""
        await self._run(*graph_queries.create_pattern(user_id, name, description))

        for sphere_name in (spheres or []):
            await self._run(*graph_queries.create_edge_by_name(
                user_id, "Pattern", name, "Sphere", sphere_name, "AFFECTS",
            ))

        return {"pattern": name, "connected_spheres": spheres or []}

    async def add_value(self, user_id: str, name: str, description: str = "", goals: list[str] | None = None) -> dict:
        """Create Value node and optionally connect to Goals via SUPPORTS."""
        await self._run(*graph_queries.create_value(user_id, name, description))

        for goal_name in (goals or []):
            await self._run(*graph_queries.create_edge_by_name(
                user_id, "Value", name, "Goal", goal_name, "SUPPORTS",
            ))

        return {"value": name, "supports_goals": goals or []}

    async def add_blocker(self, user_id: str, name: str, description: str = "", spheres: list[str] | None = None) -> dict:
        """Create Blocker node and connect to spheres via AFFECTS."""
        await self._run(*graph_queries.create_blocker(user_id, name, description))

        for sphere_name in (spheres or []):
            await self._run(*graph_queries.create_edge_by_name(
                user_id, "Blocker", name, "Sphere", sphere_name, "AFFECTS", weight=0.8,
            ))

        return {"blocker": name, "affects_spheres": spheres or []}

    async def add_goal(self, user_id: str, name: str, description: str = "", spheres: list[str] | None = None) -> dict:
        """Create Goal node and connect to spheres via AFFECTS."""
        await self._run(*graph_queries.create_goal(user_id, name, description))

        for sphere_name in (spheres or []):
            await self._run(*graph_queries.create_edge_by_name(
                user_id, "Goal", name, "Sphere", sphere_name, "AFFECTS",
            ))

        return {"goal": name, "affects_spheres": spheres or []}

    async def add_checkin(self, user_id: str, summary: str) -> dict:
        """Create CheckIn node linked to Person."""
        result = await self._run(*graph_queries.create_checkin(user_id, summary))
        return {"checkin_created": bool(result)}

    async def build_from_onboarding(self, user_id: str, name: str, entities: dict) -> dict:
        """Build full initial graph from onboarding extraction results.

        entities format (from Claude):
        {
            "spheres": ["Карьера", "Здоровье", ...],
            "events": [{"name": "...", "description": "...", "spheres": ["..."]}],
            "patterns": [{"name": "...", "description": "...", "spheres": ["..."]}],
            "values": [{"name": "...", "description": "..."}],
            "blockers": [{"name": "...", "description": "...", "spheres": ["..."]}],
            "goals": [{"name": "...", "description": "...", "spheres": ["..."]}]
        }
        """
        spheres = entities.get("spheres", [])
        await self.init_user_graph(user_id, name, spheres)

        counts = {"spheres": len(spheres), "events": 0, "patterns": 0, "values": 0, "blockers": 0, "goals": 0}

        for event in entities.get("events", []):
            await self.add_event(user_id, event["name"], event.get("description", ""), event.get("spheres"))
            counts["events"] += 1

        for pattern in entities.get("patterns", []):
            await self.add_pattern(user_id, pattern["name"], pattern.get("description", ""), pattern.get("spheres"))
            counts["patterns"] += 1

        for value in entities.get("values", []):
            await self.add_value(user_id, value["name"], value.get("description", ""), value.get("goals"))
            counts["values"] += 1

        for blocker in entities.get("blockers", []):
            await self.add_blocker(user_id, blocker["name"], blocker.get("description", ""), blocker.get("spheres"))
            counts["blockers"] += 1

        for goal in entities.get("goals", []):
            await self.add_goal(user_id, goal["name"], goal.get("description", ""), goal.get("spheres"))
            counts["goals"] += 1

        return counts

    # ── Sphere CRUD (Phase A) ──────────────────────────────────────

    async def create_sphere(self, user_id: str, name: str, description: str = "") -> dict:
        """Create a new sphere and connect to Person."""
        rows = await self._run(*graph_queries.create_sphere_with_id(user_id, name, description))
        if rows:
            return {"id": rows[0]["id"], "name": rows[0]["name"]}
        return {}

    async def get_spheres(self, user_id: str) -> list[dict]:
        return await self._run(*graph_queries.get_spheres_with_ids(user_id))

    async def get_sphere_detail(self, user_id: str, sphere_id: str) -> dict | None:
        rows = await self._run(*graph_queries.get_sphere_detail(user_id, sphere_id))
        if not rows:
            return None
        return rows[0]

    async def rename_sphere(self, sphere_id: str, new_name: str) -> dict | None:
        rows = await self._run(*graph_queries.rename_sphere(sphere_id, new_name))
        return rows[0] if rows else None

    async def archive_sphere(self, sphere_id: str) -> bool:
        rows = await self._run(*graph_queries.archive_sphere(sphere_id))
        return bool(rows)

    async def get_related_spheres(self, user_id: str, sphere_id: str) -> list[str]:
        rows = await self._run(*graph_queries.get_related_spheres(user_id, sphere_id))
        return [r["name"] for r in rows]

    async def update_sphere_description(self, sphere_id: str, description: str) -> dict | None:
        rows = await self._run(*graph_queries.update_sphere_description(sphere_id, description))
        return rows[0] if rows else None
