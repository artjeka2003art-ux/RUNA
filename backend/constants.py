NODE_TYPES = [
    "Person",
    "Sphere",
    "Event",
    "Pattern",
    "Value",
    "Blocker",
    "Goal",
    "CheckIn",
]

EDGE_TYPES = [
    "AFFECTS",
    "CAUSED_BY",
    "CONFLICTS_WITH",
    "SUPPORTS",
    "CHANGED_ON",
    "PREDICTS",
]

AGENT_NAMES = [
    "conversation_agent",
    "analyst_agent",
    "scenario_agent",
    "companion_agent",
]

# OpenAI model — gpt-4o-mini is cheap and fast, good for MVP testing
AI_MODEL = "gpt-4o-mini"
