from pathlib import Path

from backend.constants import ANTHROPIC_MODEL
from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries

COMPANION_PROMPT_TEMPLATE = (Path(__file__).parent.parent / "prompts" / "companion_prompt.txt").read_text()

# In-memory checkin history (Phase 1 — migrate to Redis later)
_checkin_sessions: dict[str, list[dict]] = {}


class CompanionAgent:
    """Daily check-in agent. Reads graph and speaks to specific observations."""

    def __init__(self, anthropic_client, graph_client: Neo4jClient):
        self.anthropic = anthropic_client
        self.graph = graph_client
        self.model = ANTHROPIC_MODEL

    async def respond(self, user_id: str, message: str) -> str:
        """Generate a response grounded in the user's personal graph."""

        # 1. Load graph context — what do we know about this person?
        graph_context = await self._build_graph_context(user_id)

        # 2. Load recent check-ins
        recent_checkins = await self._get_recent_checkins(user_id)

        # 3. Get or create conversation history for this session
        if user_id not in _checkin_sessions:
            _checkin_sessions[user_id] = []
        history = _checkin_sessions[user_id]

        history.append({"role": "user", "content": message})

        # 4. Build system prompt with real graph data
        system_prompt = COMPANION_PROMPT_TEMPLATE.format(
            graph_context=graph_context,
            recent_checkins=recent_checkins,
            conversation_history="",  # History goes into messages, not system prompt
        )

        # 5. Call Claude
        response = await self.anthropic.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=history,
        )

        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})

        # Keep history manageable (last 20 messages)
        if len(history) > 20:
            _checkin_sessions[user_id] = history[-20:]

        return reply

    async def _build_graph_context(self, user_id: str) -> str:
        """Read the user's graph and format it as readable context for the prompt."""
        lines = []

        # Spheres
        query, params = graph_queries.get_spheres(user_id)
        spheres = await self.graph.execute_query(query, params)
        if spheres:
            sphere_names = [s["name"] for s in spheres]
            lines.append(f"Сферы жизни: {', '.join(sphere_names)}")

        # Blockers
        query, params = graph_queries.get_user_nodes_by_type(user_id, "Blocker")
        blockers = await self.graph.execute_query(query, params)
        for b in blockers:
            lines.append(f"Блок: {b['name']} — {b.get('description', '')}")

        # Patterns
        query, params = graph_queries.get_user_nodes_by_type(user_id, "Pattern")
        patterns = await self.graph.execute_query(query, params)
        for p in patterns:
            lines.append(f"Паттерн: {p['name']} — {p.get('description', '')}")

        # Goals
        query, params = graph_queries.get_user_nodes_by_type(user_id, "Goal")
        goals = await self.graph.execute_query(query, params)
        for g in goals:
            lines.append(f"Цель: {g['name']} — {g.get('description', '')}")

        # Values
        query, params = graph_queries.get_user_nodes_by_type(user_id, "Value")
        values = await self.graph.execute_query(query, params)
        for v in values:
            lines.append(f"Ценность: {v['name']} — {v.get('description', '')}")

        # Events
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

        lines = []
        for c in checkins:
            lines.append(f"- {c.get('summary', '')}")

        return "\n".join(lines)
