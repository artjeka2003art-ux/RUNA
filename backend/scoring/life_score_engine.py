from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries
from backend.models.schemas import LifeScore, SphereScore


# What kind of node pushes the score up or down
_POSITIVE_TYPES = {"Goal", "Value"}
_NEGATIVE_TYPES = {"Blocker"}
# Pattern and Event are neutral by default — their weight determines direction

# Base score — everyone starts here, then adjustments move it up or down
_BASE_SCORE = 50.0

# How much one connection can shift the score (prevents one blocker from killing everything)
_MAX_SHIFT_PER_NODE = 15.0


class LifeScoreEngine:
    """Calculates Life Score (0-100) from graph state."""

    def __init__(self, graph_client: Neo4jClient):
        self.graph = graph_client

    async def calculate(self, user_id: str) -> LifeScore:
        """Calculate full Life Score: per-sphere + total."""
        # Get all spheres for this user
        query, params = graph_queries.get_spheres(user_id)
        sphere_rows = await self.graph.execute_query(query, params)

        if not sphere_rows:
            return LifeScore(user_id=user_id, total=_BASE_SCORE, spheres=[])

        sphere_scores = []
        for row in sphere_rows:
            sphere_name = row["name"]
            score = await self.calculate_sphere_score(user_id, sphere_name)
            sphere_scores.append(score)

        # Total = average of all sphere scores
        total = sum(s.score for s in sphere_scores) / len(sphere_scores)

        return LifeScore(
            user_id=user_id,
            total=round(total, 1),
            spheres=sphere_scores,
        )

    async def calculate_sphere_score(self, user_id: str, sphere_name: str) -> SphereScore:
        """Calculate score for one sphere based on its graph connections.

        Logic:
        - Start at 50 (neutral)
        - Each Goal/Value connected → pushes score UP (weight * max_shift)
        - Each Blocker connected → pushes score DOWN (weight * max_shift)
        - Patterns/Events → up or down depending on edge type
        - Clamp to 0-100
        """
        query, params = graph_queries.get_sphere_connections(user_id, sphere_name)
        connections = await self.graph.execute_query(query, params)

        score = _BASE_SCORE
        reasons = []

        for conn in connections:
            node_labels = set(conn.get("node_labels", []))
            node_name = conn.get("node_name", "")
            weight = conn.get("weight", 0.5)
            shift = weight * _MAX_SHIFT_PER_NODE

            if node_labels & _POSITIVE_TYPES:
                score += shift
                reasons.append(f"+{node_name}")
            elif node_labels & _NEGATIVE_TYPES:
                score -= shift
                reasons.append(f"-{node_name}")
            else:
                # Pattern/Event — light positive if connected (means graph is rich)
                score += shift * 0.2
                reasons.append(f"~{node_name}")

        score = max(0.0, min(100.0, score))

        reason = ", ".join(reasons[:3]) if reasons else "нет данных"

        return SphereScore(
            sphere=sphere_name,
            score=round(score, 1),
            delta=0.0,  # Delta will be calculated when we have history
            reason=reason,
        )
