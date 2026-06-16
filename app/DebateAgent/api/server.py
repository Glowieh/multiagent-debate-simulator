from fastapi import FastAPI

from api.routes.debate import router as debate_router
from api.routes.health import router as health_router

app = FastAPI(title="LangGraph Debate Simulator")
app.include_router(debate_router)
app.include_router(health_router)
