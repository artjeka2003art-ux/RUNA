from pathlib import Path

from backend.constants import AI_MODEL
from backend.graph.neo4j_client import Neo4jClient
from backend.graph import graph_queries
from backend.memory.session_store import SessionStore

SPHERE_PROMPT_TEMPLATE = (Path(__file__).parent.parent / "prompts" / "sphere_chat_prompt.txt").read_text()


class SphereAgent:
    """Chat agent scoped to a single sphere but aware of the full graph."""

    def __init__(
        self,
        ai_client,
        graph_client: Neo4jClient,
        session_store: SessionStore,
    ):
        self.ai = ai_client
        self.graph = graph_client
        self.sessions = session_store
        self.model = AI_MODEL

    async def respond(self, user_id: str, sphere_id: str, sphere_name: str, message: str) -> str:
        """Generate a response grounded in sphere context + global graph."""

        # 1. Sphere-specific context
        sphere_context, sphere_desc = await self._build_sphere_context(user_id, sphere_name)

        # 2. Related spheres
        related = await self._get_related_spheres(user_id, sphere_id)

        # 3. Global context (all spheres + key nodes)
        global_context = await self._build_global_context(user_id)

        # 4. Recent checkins
        recent_checkins = await self._get_recent_checkins(user_id)

        # 5. Session history for this sphere chat
        session_key = f"sphere-{user_id}-{sphere_id}"
        history = await self.sessions.get_session(session_key) or []
        history.append({"role": "user", "content": message})

        # 6. Build prompt
        system_prompt = SPHERE_PROMPT_TEMPLATE.format(
            sphere_name=sphere_name,
            sphere_description=sphere_desc,
            sphere_context=sphere_context,
            related_spheres=related,
            global_context=global_context,
            recent_checkins=recent_checkins,
        )

        api_messages = [{"role": "system", "content": system_prompt}] + history

        # 7. Call AI
        response = await self.ai.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=api_messages,
        )

        reply = response.choices[0].message.content

        # 8. Save history
        history.append({"role": "assistant", "content": reply})
        await self.sessions.save_session(session_key, history)

        return reply

    async def generate_description(self, user_id: str, sphere_name: str, conversation_snippet: str = "") -> str:
        """Generate a short human-readable description for a sphere."""
        global_context = await self._build_global_context(user_id)
        sphere_context, _ = await self._build_sphere_context(user_id, sphere_name)

        prompt = (
            f"Пользователь создал сферу жизни: \"{sphere_name}\".\n"
            f"Контекст его жизни:\n{global_context}\n\n"
        )
        if sphere_context and "Пока нет данных" not in sphere_context:
            prompt += f"Что уже связано с этой сферой:\n{sphere_context}\n\n"
        if conversation_snippet:
            prompt += f"Из разговора:\n{conversation_snippet}\n\n"
        prompt += (
            "Напиши ОДНО предложение (до 100 символов), описывающее суть этой сферы "
            "для этого конкретного человека. Без кавычек, без пояснений — только само предложение."
        )

        response = await self.ai.chat.completions.create(
            model=self.model,
            max_tokens=100,
            messages=[
                {"role": "system", "content": "Ты — Runa. Пиши на русском. Коротко и по сути."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip().strip('"').strip("«»")

    async def generate_intro(self, user_id: str, sphere_name: str) -> str:
        """Generate a welcoming first message when user opens a new sphere."""
        global_context = await self._build_global_context(user_id)

        prompt = (
            f"Пользователь только что создал новую сферу жизни: \"{sphere_name}\".\n"
            f"Контекст его жизни:\n{global_context}\n\n"
            f"Напиши тёплое первое сообщение (2-3 предложения) от Runa.\n"
            f"Цель: помочь человеку раскрыть, что для него значит эта сфера.\n"
            f"Задай один конкретный вопрос, чтобы начать разговор.\n"
            f"Пиши на русском. Не начинай с 'Привет'."
        )

        response = await self.ai.chat.completions.create(
            model=self.model,
            max_tokens=200,
            messages=[
                {"role": "system", "content": "Ты — Runa, персональная AI-система."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()

    async def _build_sphere_context(self, user_id: str, sphere_name: str) -> tuple[str, str]:
        """Get all nodes connected to this sphere."""
        query, params = graph_queries.get_sphere_full_data(user_id, sphere_name)
        rows = await self.graph.execute_query(query, params)

        if not rows:
            return "Пока нет данных о связях этой сферы.", ""

        lines = []
        desc = ""
        for r in rows:
            labels = r.get("node_labels", [])
            label = labels[0] if labels else "?"
            name = r.get("node_name", "?")
            node_desc = r.get("description", "")
            weight = r.get("weight", 0.5)

            type_ru = {
                "Blocker": "Блокер",
                "Goal": "Цель",
                "Pattern": "Паттерн",
                "Value": "Ценность",
                "Event": "Событие",
            }.get(label, label)

            line = f"- {type_ru}: {name} (вес: {weight})"
            if node_desc:
                line += f" — {node_desc}"
            lines.append(line)

        return "\n".join(lines), desc

    async def _get_related_spheres(self, user_id: str, sphere_id: str) -> str:
        query, params = graph_queries.get_related_spheres(user_id, sphere_id)
        rows = await self.graph.execute_query(query, params)
        if not rows:
            return "Нет связанных сфер."
        return ", ".join(r["name"] for r in rows)

    async def _build_global_context(self, user_id: str) -> str:
        lines = []
        query, params = graph_queries.get_spheres(user_id)
        spheres = await self.graph.execute_query(query, params)
        if spheres:
            lines.append(f"Все сферы: {', '.join(s['name'] for s in spheres)}")

        for node_type, label_ru in [("Blocker", "Блок"), ("Goal", "Цель")]:
            query, params = graph_queries.get_user_nodes_by_type(user_id, node_type)
            nodes = await self.graph.execute_query(query, params)
            for n in nodes[:3]:
                lines.append(f"{label_ru}: {n['name']}")

        return "\n".join(lines) if lines else "Мало данных."

    async def _get_recent_checkins(self, user_id: str) -> str:
        query, params = graph_queries.get_recent_checkins(user_id, limit=5)
        checkins = await self.graph.execute_query(query, params)
        if not checkins:
            return "Чекинов пока нет."
        return "\n".join(f"- {c.get('summary', '')}" for c in checkins)
