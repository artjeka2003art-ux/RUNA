from backend.constants import ANTHROPIC_MODEL


class PredictorAgent:
    """Calculates probabilities for each scenario based on graph data."""

    def __init__(self, anthropic_client, graph_client):
        self.anthropic = anthropic_client
        self.graph = graph_client
        self.model = ANTHROPIC_MODEL

    async def predict(self, user_id: str, scenarios: list[dict]) -> list[dict]:
        # TODO: Calculate probability for each scenario
        # 1. Load current graph state (weights, patterns, blockers)
        # 2. Ask Claude to assign probabilities with reasoning
        # 3. Return scenarios with probabilities attached
        raise NotImplementedError
