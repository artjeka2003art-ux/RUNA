from backend.constants import ANTHROPIC_MODEL


class AnalystAgent:
    """Reads the personal knowledge graph, updates edge weights based on new data."""

    def __init__(self, anthropic_client, graph_client):
        self.anthropic = anthropic_client
        self.graph = graph_client
        self.model = ANTHROPIC_MODEL

    async def analyze(self, user_id: str) -> dict:
        # TODO: Analyze user graph and update weights
        # 1. Read full graph for user
        # 2. Identify changed patterns via Claude API
        # 3. Update edge weights in graph
        raise NotImplementedError

    async def detect_patterns(self, user_id: str) -> list[dict]:
        # TODO: Detect new patterns from recent check-ins
        # 1. Get recent check-ins from graph
        # 2. Ask Claude to identify patterns
        # 3. Create Pattern nodes and edges
        raise NotImplementedError
