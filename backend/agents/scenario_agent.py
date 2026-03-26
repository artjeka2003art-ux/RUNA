from pathlib import Path

from backend.constants import ANTHROPIC_MODEL

SCENARIO_PROMPT = (Path(__file__).parent.parent / "prompts" / "scenario_prompt.txt").read_text


class ScenarioAgent:
    """Builds 3 parallel future scenarios based on current graph state."""

    def __init__(self, anthropic_client, graph_client):
        self.anthropic = anthropic_client
        self.graph = graph_client
        self.model = ANTHROPIC_MODEL

    async def generate_scenarios(self, user_id: str) -> list[dict]:
        # TODO: Generate 3 future scenarios
        # 1. Load user graph (goals, blockers, patterns)
        # 2. Load scenario prompt
        # 3. Ask Claude to build optimistic / realistic / pessimistic scenarios
        # 4. Return structured scenarios
        raise NotImplementedError
