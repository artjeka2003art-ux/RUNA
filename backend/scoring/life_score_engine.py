from backend.graph.neo4j_client import Neo4jClient
from backend.models.schemas import LifeScore, SphereScore


class LifeScoreEngine:
    """Calculates Life Score (0-100) from graph state."""

    def __init__(self, graph_client: Neo4jClient):
        self.graph = graph_client

    async def calculate(self, user_id: str) -> LifeScore:
        # TODO: Calculate life score
        # 1. Get all spheres and their connected nodes/edges
        # 2. For each sphere: aggregate edge weights, count blockers vs supports
        # 3. Normalize to 0-100 per sphere
        # 4. Calculate weighted total
        raise NotImplementedError

    async def calculate_sphere_score(self, user_id: str, sphere_name: str) -> SphereScore:
        # TODO: Calculate score for a single sphere
        # 1. Get sphere node and all connected edges
        # 2. Sum positive (SUPPORTS) and negative (CONFLICTS_WITH, CAUSED_BY blockers) weights
        # 3. Normalize to 0-100
        raise NotImplementedError
