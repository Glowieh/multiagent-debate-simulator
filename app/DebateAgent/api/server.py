from fastapi import FastAPI

from api.routes.debate import router as debate_router

app = FastAPI(title="LangGraph Debate Simulator")
app.include_router(debate_router)
