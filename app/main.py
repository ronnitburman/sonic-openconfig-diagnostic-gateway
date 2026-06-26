from fastapi import FastAPI

app = FastAPI(
    title="SONiC OpenConfig Diagnostic Gateway",
    version="0.1.0",
)

from app.api.health import router as health_router

app.include_router(health_router)
