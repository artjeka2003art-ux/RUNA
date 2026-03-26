from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import onboarding, checkin, dashboard

app = FastAPI(title="Runa", version="0.1.0")

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
