from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from dusema.config import Settings


class HealthResponse(BaseModel):
    status: Literal["ok"]


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(
        title="DUSEMA AI",
        openapi_url=None if settings.environment == "production" else "/openapi.json",
    )

    @app.get("/health", tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app
