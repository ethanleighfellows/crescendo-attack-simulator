from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.routes import router
from src.backend.api.websocket import ws_router
from src.backend.config.settings import Settings

settings = Settings()

app = FastAPI(
    title=settings.app_name,
    description="Standalone Crescendo multi-turn jailbreak prompt generator for LLM red-teaming research.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(ws_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
