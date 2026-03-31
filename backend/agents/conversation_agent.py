import json
import re
import uuid
from pathlib import Path

from backend.constants import AI_MODEL
from backend.graph.graph_builder import GraphBuilder
from backend.memory.session_store import SessionStore

ONBOARDING_PROMPT = (Path(__file__).parent.parent / "prompts" / "onboarding_prompt.txt").read_text()


class ConversationAgent:
    """Handles onboarding (15-min deep conversation) and daily check-ins."""

    def __init__(self, ai_client, graph_builder: GraphBuilder, session_store: SessionStore):
        self.ai = ai_client
        self.graph = graph_builder
        self.sessions = session_store
        self.model = AI_MODEL

    async def start_onboarding(self, user_id: str) -> dict:
        """Create a new onboarding session and send the first message from Runa."""
        session_id = str(uuid.uuid4())

        response = await self.ai.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": ONBOARDING_PROMPT},
                {"role": "user", "content": "Привет"},
            ],
        )

        assistant_text = response.choices[0].message.content

        await self.sessions.save_onboarding(session_id, {
            "user_id": user_id,
            "messages": [
                {"role": "user", "content": "Привет"},
                {"role": "assistant", "content": assistant_text},
            ],
            "completed": False,
        })

        return {
            "session_id": session_id,
            "reply": assistant_text,
            "completed": False,
        }

    async def process_onboarding_message(self, user_id: str, session_id: str, message: str) -> dict:
        """Process next user message during onboarding."""
        session = await self.sessions.get_onboarding(session_id)
        if not session or session["user_id"] != user_id:
            raise ValueError("Session not found")

        session["messages"].append({"role": "user", "content": message})

        api_messages = [{"role": "system", "content": ONBOARDING_PROMPT}] + session["messages"]

        response = await self.ai.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            messages=api_messages,
        )

        assistant_text = response.choices[0].message.content
        session["messages"].append({"role": "assistant", "content": assistant_text})

        # Save updated session to Redis
        await self.sessions.save_onboarding(session_id, session)

        # Check if model returned extraction (onboarding complete)
        entities = self._extract_entities(assistant_text)

        if entities:
            session["completed"] = True
            await self.sessions.save_onboarding(session_id, session)

            counts = await self.graph.build_from_onboarding(
                user_id=user_id,
                name=user_id,
                entities=entities,
            )

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
        """Parse <extraction> JSON from model response."""
        match = re.search(r"<extraction>\s*(.*?)\s*</extraction>", text, re.DOTALL)
        if not match:
            # Fallback for models that don't use tags
            match = re.search(r"\{.*\"spheres\".*\}", text, re.DOTALL)
            if not match:
                return None
        try:
            return json.loads(match.group(1) if match.lastindex else match.group(0))
        except json.JSONDecodeError:
            return None
