from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries


class GraphBuilder:
    """High-level graph operations built on top of graph_queries."""

    def __init__(self, client: Neo4jClient):
        self.client = client

    async def init_user_graph(self, user_id: str, name: str, spheres: list[str]) -> dict:
        # TODO: Create Person node + Sphere nodes + AFFECTS edges
        # 1. Create Person
        # 2. Create Sphere nodes for each sphere
        # 3. Create AFFECTS edges from Person to each Sphere
        raise NotImplementedError

    async def add_event(self, user_id: str, event_data: dict) -> dict:
        # TODO: Create Event node and connect to relevant spheres
        raise NotImplementedError

    async def add_pattern(self, user_id: str, pattern_data: dict) -> dict:
        # TODO: Create Pattern node and connect to related nodes
        raise NotImplementedError

    async def add_blocker(self, user_id: str, blocker_data: dict) -> dict:
        # TODO: Create Blocker node and connect via CAUSED_BY / CONFLICTS_WITH
        raise NotImplementedError
