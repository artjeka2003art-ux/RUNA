from pathlib import Path

from backend.constants import AI_MODEL
from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries
from backend.memory.session_store import SessionStore
from backend.memory.zep_client import ZepMemoryClient

COMPANION_PROMPT_TEMPLATE = (Path(__file__).parent.parent / "prompts" / "companion_prompt.txt").read_text()


class CompanionAgent:
    """Daily check-in agent. Reads graph + Zep memory and speaks to specific observations."""

    def __init__(
        self,
        ai_client,
        graph_client: Neo4jClient,
        session_store: SessionStore,
        zep_client: ZepMemoryClient | None = None,
    ):
        self.ai = ai_client
        self.graph = graph_client
        self.sessions = session_store
        self.zep = zep_client
        self.model = AI_MODEL

    async def respond(self, user_id: str, message: str) -> str:
        """Generate a response grounded in graph + long-term memory."""

        # 1. Graph context (structure: spheres, blockers, goals...)
        graph_context = await self._build_graph_context(user_id)

        # 2. Recent check-ins from Neo4j
        recent_checkins = await self._get_recent_checkins(user_id)

        # 3. Long-term memory from Zep (facts, past conversations)
        zep_context = ""
        if self.zep:
            thread_id = f"checkin-{user_id}"
            zep_context = await self.zep.get_user_context(user_id, thread_id)

        # 4. Short-term session history from Redis
        history = await self.sessions.get_checkin_history(user_id)
        history.append({"role": "user", "content": message})

        # 5. Build system prompt with all context layers
        memory_section = ""
        if zep_context:
            memory_section = f"\n\n## Долгосрочная память (что ты помнишь из прошлых разговоров):\n{zep_context}"

        system_prompt = COMPANION_PROMPT_TEMPLATE.format(
            graph_context=graph_context,
            recent_checkins=recent_checkins,
            conversation_history=memory_section,
        )

        api_messages = [{"role": "system", "content": system_prompt}] + history

        # 6. Call AI
        response = await self.ai.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=api_messages,
        )

        reply = response.choices[0].message.content

        # 7. Save to Redis (short-term)
        history.append({"role": "assistant", "content": reply})
        await self.sessions.save_checkin_history(user_id, history)

        # 8. Save to Zep (long-term) — runs in background, doesn't block response
        if self.zep:
            try:
                thread_id = f"checkin-{user_id}"
                await self.zep.add_messages(user_id, thread_id, message, reply)
            except Exception:
                pass  # Zep failure must not block checkin

        return reply

    async def _build_graph_context(self, user_id: str) -> str:
        """Read the user's graph and format it as readable context for the prompt."""
        lines = []

        query, params = graph_queries.get_spheres(user_id)
        spheres = await self.graph.execute_query(query, params)
        if spheres:
            sphere_names = [s["name"] for s in spheres]
            lines.append(f"Сферы жизни: {', '.join(sphere_names)}")

        query, params = graph_queries.get_user_nodes_by_type(user_id, "Blocker")
        blockers = await self.graph.execute_query(query, params)
        for b in blockers:
            lines.append(f"Блок: {b['name']} — {b.get('description', '')}")

        query, params = graph_queries.get_user_nodes_by_type(user_id, "Pattern")
        patterns = await self.graph.execute_query(query, params)
        for p in patterns:
            lines.append(f"Паттерн: {p['name']} — {p.get('description', '')}")

        query, params = graph_queries.get_user_nodes_by_type(user_id, "Goal")
        goals = await self.graph.execute_query(query, params)
        for g in goals:
            lines.append(f"Цель: {g['name']} — {g.get('description', '')}")

        query, params = graph_queries.get_user_nodes_by_type(user_id, "Value")
        values = await self.graph.execute_query(query, params)
        for v in values:
            lines.append(f"Ценность: {v['name']} — {v.get('description', '')}")

        query, params = graph_queries.get_user_nodes_by_type(user_id, "Event")
        events = await self.graph.execute_query(query, params)
        for e in events:
            lines.append(f"Событие: {e['name']} — {e.get('description', '')}")

        return "\n".join(lines) if lines else "Граф пока пуст — это первый чекин после онбординга."

    async def _get_recent_checkins(self, user_id: str) -> str:
        """Get recent check-in summaries from graph."""
        query, params = graph_queries.get_recent_checkins(user_id, limit=7)
        checkins = await self.graph.execute_query(query, params)

        if not checkins:
            return "Предыдущих чекинов нет — это первый."

        return "\n".join(f"- {c.get('summary', '')}" for c in checkins)
