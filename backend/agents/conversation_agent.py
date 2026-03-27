import json
import re
import uuid
from pathlib import Path

from backend.constants import ANTHROPIC_MODEL
from backend.graph.graph_builder import GraphBuilder

ONBOARDING_PROMPT = (Path(__file__).parent.parent / "prompts" / "onboarding_prompt.txt").read_text()

# In-memory session storage (Phase 1 — migrate to Redis in Phase 2)
_sessions: dict[str, dict] = {}


class ConversationAgent:
    """Handles onboarding (15-min deep conversation) and daily check-ins."""

    def __init__(self, anthropic_client, graph_builder: GraphBuilder):
        self.anthropic = anthropic_client
        self.graph = graph_builder
        self.model = ANTHROPIC_MODEL

    async def start_onboarding(self, user_id: str) -> dict:
        """Create a new onboarding session and send the first message from Runa."""
        session_id = str(uuid.uuid4())

        # First turn: Claude speaks first with the system prompt
        response = await self.anthropic.messages.create(
            model=self.model,
            max_tokens=1024,
            system=ONBOARDING_PROMPT,
            messages=[{"role": "user", "content": "Привет"}],
        )

        assistant_text = response.content[0].text

        _sessions[session_id] = {
            "user_id": user_id,
            "messages": [
                {"role": "user", "content": "Привет"},
                {"role": "assistant", "content": assistant_text},
            ],
            "completed": False,
        }

        return {
            "session_id": session_id,
            "reply": assistant_text,
            "completed": False,
        }

    async def process_onboarding_message(self, user_id: str, session_id: str, message: str) -> dict:
        """Process next user message during onboarding."""
        session = _sessions.get(session_id)
        if not session or session["user_id"] != user_id:
            raise ValueError("Session not found")

        session["messages"].append({"role": "user", "content": message})

        response = await self.anthropic.messages.create(
            model=self.model,
            max_tokens=2048,
            system=ONBOARDING_PROMPT,
            messages=session["messages"],
        )

        assistant_text = response.content[0].text
        session["messages"].append({"role": "assistant", "content": assistant_text})

        # Check if Claude returned extraction (onboarding complete)
        entities = self._extract_entities(assistant_text)

        if entities:
            session["completed"] = True
            # Build the full personal graph
            counts = await self.graph.build_from_onboarding(
                user_id=user_id,
                name=user_id,  # Will be replaced with real name from user data
                entities=entities,
            )

            # Send a final human-readable message to the user
            spheres = entities.get("spheres", [])
            summary_reply = (
                f"Я построила твою карту. Вот что я вижу:\n\n"
                f"Сферы жизни: {', '.join(spheres)}\n"
                f"Событий: {counts['events']}, паттернов: {counts['patterns']}, "
                f"блоков: {counts['blockers']}, целей: {counts['goals']}\n\n"
                f"Теперь я буду отслеживать изменения и каждый день спрашивать как дела. "
                f"Не шаблонно — а конкретно, по твоей карте."
            )

            return {
                "session_id": session_id,
                "reply": summary_reply,
                "completed": True,
                "spheres": spheres,
                "nodes_created": sum(counts.values()),
            }

        return {
            "session_id": session_id,
            "reply": assistant_text,
            "completed": False,
        }

    def _extract_entities(self, text: str) -> dict | None:
        """Parse <extraction> JSON from Claude's response."""
        match = re.search(r"<extraction>\s*(.*?)\s*</extraction>", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
