class ZepMemoryClient:
    """Long-term conversation memory via Zep."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        # TODO: Store message in Zep session
        raise NotImplementedError

    async def get_history(self, session_id: str, limit: int = 50) -> list[dict]:
        # TODO: Retrieve conversation history from Zep
        raise NotImplementedError

    async def search(self, session_id: str, query: str, limit: int = 5) -> list[dict]:
        # TODO: Semantic search over conversation memory
        raise NotImplementedError
