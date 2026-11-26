from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, TimeoutError
from sqlalchemy.orm import Session

from dusema.config import Settings
from dusema.database import create_database_engine, database_unavailable, get_session


class HealthResponse(BaseModel):
    status: Literal["ok"]


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()
    database_url = settings.database_url

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = (
            create_database_engine(database_url) if database_url is not None else None
        )
        app.state.database_engine = engine
        try:
            yield
        finally:
            if engine is not None:
                await run_in_threadpool(engine.dispose)

    app = FastAPI(
        title="DUSEMA AI",
        openapi_url=None if settings.environment == "production" else "/openapi.json",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get(
        "/ready",
        tags=["health"],
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unavailable"}
        },
    )
    def ready(
        session: Annotated[Session, Depends(get_session, scope="function")],
    ) -> HealthResponse:
        try:
            with session.begin():
                session.execute(text("SELECT 1"))
        except DBAPIError, TimeoutError:
            raise database_unavailable() from None
        return HealthResponse(status="ok")

    return app
