import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import onboarding, checkin, dashboard
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.graph_builder import GraphBuilder
from backend.agents.conversation_agent import ConversationAgent
from backend.agents.companion_agent import CompanionAgent
from backend.scoring.life_score_engine import LifeScoreEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start services on startup, clean up on shutdown."""
    # Neo4j
    neo4j = Neo4jClient(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
    )
    graph_builder = GraphBuilder(neo4j)

    # Anthropic — real client if API key exists, mock for development
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key and not api_key.startswith("sk-ant-xxx"):
        import anthropic
        anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)
        print("✓ Anthropic: real Claude API")
    else:
        from backend.agents.mock_anthropic import MockAnthropic
        anthropic_client = MockAnthropic()
        print("⚠ Anthropic: mock mode (set ANTHROPIC_API_KEY for real Claude)")

    # Scoring
    life_score_engine = LifeScoreEngine(neo4j)

    # Agents
    conversation_agent = ConversationAgent(anthropic_client, graph_builder)
    companion_agent = CompanionAgent(anthropic_client, neo4j)

    # Make available to routes
    app.state.neo4j = neo4j
    app.state.graph_builder = graph_builder
    app.state.conversation_agent = conversation_agent
    app.state.companion_agent = companion_agent
    app.state.life_score_engine = life_score_engine

    yield

    await neo4j.close()


app = FastAPI(title="Runa", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(onboarding.router, prefix="/api")
app.include_router(checkin.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "runa"}
