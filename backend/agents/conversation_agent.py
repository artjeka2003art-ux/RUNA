from pathlib import Path

from backend.constants import ANTHROPIC_MODEL

ONBOARDING_PROMPT = (Path(__file__).parent.parent / "prompts" / "onboarding_prompt.txt").read_text


class ConversationAgent:
    """Handles onboarding (15-min deep conversation) and daily check-ins."""

    def __init__(self, anthropic_client, graph_client, memory_client):
        self.anthropic = anthropic_client
        self.graph = graph_client
        self.memory = memory_client
        self.model = ANTHROPIC_MODEL

    async def start_onboarding(self, user_id: str) -> dict:
        # TODO: Initialize onboarding session
        # 1. Create session in memory
        # 2. Load onboarding prompt
        # 3. Send first message via Claude API
        raise NotImplementedError

    async def process_onboarding_message(self, user_id: str, session_id: str, message: str) -> dict:
        # TODO: Process user message during onboarding
        # 1. Load conversation history from memory
        # 2. Send to Claude API with onboarding prompt
        # 3. Extract entities and update graph
        # 4. Check if onboarding is complete
        raise NotImplementedError

    async def daily_checkin(self, user_id: str, message: str) -> dict:
        # TODO: Process daily check-in message
        # 1. Load user graph context
        # 2. Load conversation history
        # 3. Generate contextual response via Claude API
        raise NotImplementedError
