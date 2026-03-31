"""Zep Cloud integration — long-term conversation memory.

Zep gives the companion agent:
1. Memory of ALL past conversations (not just current session)
2. Extracted facts about the user ("prefers mornings", "afraid of failure")
3. Semantic search ("what did user say about their father?")

Architecture:
- Each user = Zep user
- Each checkin session = Zep thread
- After each message exchange → save to Zep
- Before companion responds → get user context from Zep
"""

from zep_cloud import AsyncZep, Message


class ZepMemoryClient:
    """Long-term conversation memory via Zep Cloud."""

    def __init__(self, api_key: str):
        self.client = AsyncZep(api_key=api_key)

    async def ensure_user(self, user_id: str) -> None:
        """Create user in Zep if doesn't exist."""
        try:
            await self.client.user.get(user_id)
        except Exception:
            await self.client.user.add(user_id=user_id)

    async def ensure_thread(self, user_id: str, thread_id: str) -> None:
        """Create thread in Zep if doesn't exist."""
        try:
            await self.client.thread.get(thread_id=thread_id)
        except Exception:
            await self.client.thread.create(thread_id=thread_id, user_id=user_id)

    async def add_messages(
        self, user_id: str, thread_id: str, user_message: str, assistant_reply: str
    ) -> None:
        """Save a message exchange (user + assistant) to Zep."""
        await self.ensure_user(user_id)
        await self.ensure_thread(user_id, thread_id)

        await self.client.thread.add_messages(
            thread_id=thread_id,
            messages=[
                Message(role="user", content=user_message),
                Message(role="assistant", content=assistant_reply),
            ],
        )

    async def get_user_context(self, user_id: str, thread_id: str) -> str:
        """Get relevant context from ALL past conversations.

        Returns a string with facts and context Zep extracted from
        the user's entire conversation history.
        """
        try:
            await self.ensure_user(user_id)
            await self.ensure_thread(user_id, thread_id)

            response = await self.client.thread.get_user_context(thread_id=thread_id)

            parts = []
            if response.context:
                parts.append(response.context)
            if response.facts:
                parts.append("Факты: " + "; ".join(response.facts))

            return "\n".join(parts) if parts else ""
        except Exception:
            return ""

    async def search_memory(self, user_id: str, query: str, limit: int = 5) -> list[str]:
        """Semantic search across all conversations.

        Example: search("отец") → returns all moments user talked about father.
        """
        try:
            results = await self.client.graph.search(
                user_id=user_id,
                query=query,
                limit=limit,
            )
            return [r.data for r in (results.results or []) if r.data]
        except Exception:
            return []
