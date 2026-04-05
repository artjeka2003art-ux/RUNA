import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import onboarding, checkin, dashboard, spheres, prediction
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.graph_builder import GraphBuilder
from backend.memory.session_store import SessionStore
from backend.memory.zep_client import ZepMemoryClient
from backend.agents.conversation_agent import ConversationAgent
from backend.agents.companion_agent import CompanionAgent
from backend.agents.analyst_agent import AnalystAgent
from backend.agents.scenario_agent import ScenarioAgent
from backend.agents.sphere_agent import SphereAgent
from backend.agents.prediction_query_agent import PredictionQueryAgent
from backend.scoring.life_score_engine import LifeScoreEngine
from backend.services.document_service import DocumentStore


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

    # Redis session store
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    session_store = SessionStore(redis_url)
    print(f"✓ Redis: sessions at {redis_url}")

    # Zep long-term memory
    zep_api_key = os.getenv("ZEP_API_KEY", "")
    zep_client = None
    if zep_api_key and not zep_api_key.startswith("xxx"):
        zep_client = ZepMemoryClient(api_key=zep_api_key)
        print("✓ Zep: long-term memory connected")
    else:
        print("⚠ Zep: no API key, running without long-term memory")

    # OpenAI client
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("sk-xxx"):
        from openai import AsyncOpenAI
        ai_client = AsyncOpenAI(api_key=api_key)
        print("✓ OpenAI: real API connected")
    else:
        from backend.agents.mock_openai import MockOpenAI
        ai_client = MockOpenAI()
        print("⚠ OpenAI: mock mode (set OPENAI_API_KEY for real API)")

    # Scoring
    life_score_engine = LifeScoreEngine(neo4j)

    # Agents (now with Redis-backed sessions)
    conversation_agent = ConversationAgent(ai_client, graph_builder, session_store)
    companion_agent = CompanionAgent(ai_client, neo4j, session_store, zep_client)
    analyst_agent = AnalystAgent(ai_client, neo4j, graph_builder)
    scenario_agent = ScenarioAgent(ai_client, neo4j)
    sphere_agent = SphereAgent(ai_client, neo4j, session_store, zep_client)
    document_store = DocumentStore(session_store)
    prediction_query_agent = PredictionQueryAgent(ai_client, neo4j, session_store, zep_client, document_store)

    # Make available to routes
    app.state.neo4j = neo4j
    app.state.document_store = document_store
    app.state.graph_builder = graph_builder
    app.state.session_store = session_store
    app.state.conversation_agent = conversation_agent
    app.state.companion_agent = companion_agent
    app.state.analyst_agent = analyst_agent
    app.state.scenario_agent = scenario_agent
    app.state.sphere_agent = sphere_agent
    app.state.life_score_engine = life_score_engine
    app.state.prediction_query_agent = prediction_query_agent

    yield

    await session_store.close()
    await neo4j.close()


app = FastAPI(title="Runa", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(onboarding.router, prefix="/api")
app.include_router(checkin.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(spheres.router, prefix="/api")
app.include_router(prediction.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "runa"}
