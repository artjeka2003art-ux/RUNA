import json
import re
import uuid
from pathlib import Path

from backend.constants import AI_MODEL
from backend.graph.graph_builder import GraphBuilder
from backend.memory.session_store import SessionStore

ONBOARDING_PROMPT = (Path(__file__).parent.parent / "prompts" / "onboarding_prompt.txt").read_text()

BRIDGE_PROMPT = """You are Runa — a personal decision intelligence system.

The user just finished onboarding. From the conversation, you identified an active tension / life decision.

Your task: turn this tension into a **decision workspace draft** so the user can start modelling their first decision immediately.

Input:
- Active tension: {tension_name}
- Description: {tension_description}
- Related spheres: {tension_spheres}
- All identified spheres: {all_spheres}

Output a JSON object with exactly these fields:
- "draft_question": a clear, decision-oriented question in Russian (not generic, tied to their specific tension)
- "draft_variants": array of 2-3 short scenario variant labels in Russian (distinct, actionable alternatives)
- "bridge_reason": one sentence in Russian explaining why this is the first useful decision to explore

Rules:
- The question must be specific to THIS person's tension, not generic
- Variants must be meaningfully different alternatives
- Keep everything concise — labels under 8 words, question under 30 words
- Language: Russian
- Output ONLY valid JSON, no markdown, no extra text

Example output:
{{"draft_question": "Что будет, если я уволюсь сейчас vs останусь ещё на полгода?", "draft_variants": ["Уволиться сейчас", "Остаться ещё на полгода", "Остаться, но снизить нагрузку"], "bridge_reason": "Это главная развилка, которую вы обозначили — разберём варианты."}}
"""


class ConversationAgent:
    """Handles onboarding (guided world-model building) and daily check-ins."""

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
            "exchange_count": 1,
        })

        return {
            "session_id": session_id,
            "reply": assistant_text,
            "completed": False,
            "exchange_count": 1,
        }

    async def process_onboarding_message(
        self, user_id: str, session_id: str, message: str, force_complete: bool = False,
    ) -> dict:
        """Process next user message during onboarding.

        If force_complete=True, the agent is asked to wrap up immediately
        and produce extraction from whatever context has been collected.
        """
        session = await self.sessions.get_onboarding(session_id)
        if not session or session["user_id"] != user_id:
            raise ValueError("Session not found")

        exchange_count = session.get("exchange_count", len(session["messages"]) // 2)
        exchange_count += 1

        if force_complete:
            user_content = (
                f"{message}\n\n"
                "[SYSTEM: The user wants to finish onboarding now. "
                "Summarize what you know, then immediately output <extraction> "
                "with all the spheres, events, patterns, blockers, values, goals, "
                "and active_tensions you've collected so far. Do NOT ask more questions.]"
            )
        else:
            user_content = message

        session["messages"].append({"role": "user", "content": user_content})

        api_messages = [{"role": "system", "content": ONBOARDING_PROMPT}] + session["messages"]

        response = await self.ai.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            messages=api_messages,
        )

        assistant_text = response.choices[0].message.content

        # Store clean message (without system injection) for display
        session["messages"][-1] = {"role": "user", "content": message}
        session["messages"].append({"role": "assistant", "content": assistant_text})
        session["exchange_count"] = exchange_count

        # Save updated session to Redis
        await self.sessions.save_onboarding(session_id, session)

        # Check if model returned extraction (onboarding complete)
        entities = self._extract_entities(assistant_text)

        if entities:
            return await self._finalize_onboarding(
                user_id, session_id, session, entities, exchange_count,
            )

        return {
            "session_id": session_id,
            "reply": assistant_text,
            "completed": False,
            "exchange_count": exchange_count,
        }

    async def _finalize_onboarding(
        self, user_id: str, session_id: str, session: dict,
        entities: dict, exchange_count: int,
    ) -> dict:
        """Build graph from extracted entities and return completion result."""
        session["completed"] = True
        await self.sessions.save_onboarding(session_id, session)

        counts = await self.graph.build_from_onboarding(
            user_id=user_id,
            name=user_id,
            entities=entities,
        )

        spheres = entities.get("spheres", [])
        active_tensions = entities.get("active_tensions", [])

        # Build decision bridge from first active tension
        decision_bridge = None
        if active_tensions:
            decision_bridge = await self._build_decision_bridge(
                active_tensions[0], spheres,
            )

        # Build a decision-oriented summary
        tension_hint = ""
        if active_tensions:
            first_tension = active_tensions[0]
            tension_name = first_tension.get("name", "") if isinstance(first_tension, dict) else str(first_tension)
            if tension_name:
                tension_hint = f"\n\nГлавная развилка, которую я вижу: **{tension_name}**. Можем разобрать её в Decision Workspace."

        summary_reply = (
            f"Карта построена.\n\n"
            f"Сферы: {', '.join(spheres)}\n"
            f"Собрано: {counts['events']} событий, {counts['patterns']} паттернов, "
            f"{counts['blockers']} блоков, {counts['goals']} целей"
            f"{tension_hint}"
        )

        return {
            "session_id": session_id,
            "reply": summary_reply,
            "completed": True,
            "spheres": spheres,
            "active_tensions": active_tensions,
            "decision_bridge": decision_bridge,
            "nodes_created": sum(counts.values()),
            "exchange_count": exchange_count,
        }

    async def _build_decision_bridge(
        self, tension: dict | str, all_spheres: list[str],
    ) -> dict | None:
        """Generate a first decision draft from the primary active tension."""
        if isinstance(tension, str):
            tension_name = tension
            tension_desc = tension
            tension_spheres = []
        else:
            tension_name = tension.get("name", "")
            tension_desc = tension.get("description", tension_name)
            tension_spheres = tension.get("spheres", [])

        if not tension_name:
            return None

        prompt = BRIDGE_PROMPT.format(
            tension_name=tension_name,
            tension_description=tension_desc,
            tension_spheres=", ".join(tension_spheres) if tension_spheres else "не указаны",
            all_spheres=", ".join(all_spheres),
        )

        try:
            response = await self.ai.chat.completions.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            bridge = json.loads(raw)
            # Validate required fields
            if "draft_question" in bridge and "draft_variants" in bridge:
                return {
                    "source_tension": tension_name,
                    "draft_question": bridge["draft_question"],
                    "draft_variants": bridge["draft_variants"][:3],
                    "bridge_reason": bridge.get("bridge_reason", "Это главная развилка из вашего онбординга."),
                }
        except Exception:
            pass

        # Fallback: simple template-based bridge
        return {
            "source_tension": tension_name,
            "draft_question": f"Что будет, если {tension_name.lower()}?",
            "draft_variants": [tension_name],
            "bridge_reason": "Это главная развилка, которую мы нашли в онбординге.",
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
