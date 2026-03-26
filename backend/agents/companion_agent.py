from pathlib import Path

from backend.constants import ANTHROPIC_MODEL

COMPANION_PROMPT = (Path(__file__).parent.parent / "prompts" / "companion_prompt.txt").read_text


class CompanionAgent:
    """Main conversational agent. Reads graph and speaks to specific observations.

    Key principle: NEVER scripts questions. Reads graph and notices specifics.
    BAD: "How are you on a scale of 1-10?"
    GOOD: "Three weeks ago you said you were afraid of failing again.
           You've been silent for two days. What's happening?"
    """

    def __init__(self, anthropic_client, graph_client, memory_client):
        self.anthropic = anthropic_client
        self.graph = graph_client
        self.memory = memory_client
        self.model = ANTHROPIC_MODEL

    async def respond(self, user_id: str, message: str) -> str:
        # TODO: Generate contextual response
        # 1. Load user graph context (recent events, patterns, blockers)
        # 2. Load conversation history from memory
        # 3. Build prompt with graph observations
        # 4. Generate response via Claude API
        raise NotImplementedError

    async def generate_proactive_message(self, user_id: str) -> str | None:
        # TODO: Generate proactive reach-out if user has been silent
        # 1. Check last activity timestamp
        # 2. Load relevant graph context
        # 3. Generate specific, empathetic message
        raise NotImplementedError
