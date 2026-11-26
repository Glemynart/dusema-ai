from collections.abc import Iterator

from fastapi import HTTPException, Request, status
from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Session


def create_database_engine(url: URL) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_timeout=2,
        hide_parameters=True,
        connect_args={"connect_timeout": 2, "options": "-c statement_timeout=2000"},
    )


def database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database unavailable",
    )


def get_session(request: Request) -> Iterator[Session]:
    engine: Engine | None = request.app.state.database_engine
    if engine is None:
        raise database_unavailable()

    with Session(engine) as session:
        yield session
