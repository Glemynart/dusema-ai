import socket
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import Request
from fastapi.testclient import TestClient
from psycopg.errors import QueryCanceled
from sqlalchemy import Engine, create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.pool import NullPool

from dusema.config import Settings
from dusema.database import create_database_engine, get_session
from dusema.main import create_app
from dusema.models import Organization

pytestmark = pytest.mark.integration


@pytest.fixture
def test_database() -> Iterator[Settings]:
    settings = Settings()
    url = settings.database_url
    if url is None:
        pytest.fail(
            "Integration tests require a disposable PostgreSQL server and database settings."
        )

    database_name = f"dusema_test_{uuid4().hex}"
    admin = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 2},
    )
    try:
        with admin.connect() as connection:
            # The identifier is generated above from a fixed prefix and UUID hex.
            connection.exec_driver_sql(
                f"CREATE DATABASE {database_name} TEMPLATE template0"
            )
        try:
            yield settings.model_copy(update={"database_name": database_name})
        finally:
            with admin.connect() as connection:
                connection.exec_driver_sql(f"DROP DATABASE {database_name}")
    finally:
        admin.dispose()


@pytest.fixture
def engine(test_database: Settings) -> Iterator[Engine]:
    url = test_database.database_url
    assert url is not None
    engine = create_database_engine(url)
    try:
        yield engine
    finally:
        engine.dispose()


def migration_config() -> Config:
    return Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))


@pytest.fixture
def migrated_database(engine: Engine, test_database: Settings) -> Settings:
    config = migration_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    return test_database


def test_initial_migration_lifecycle_matches_model_metadata(engine: Engine) -> None:
    config = migration_config()
    head = ScriptDirectory.from_config(config).get_current_head()
    assert head == "0001_create_organizations"

    with engine.connect() as connection:
        config.attributes["connection"] = connection
        assert inspect(connection).get_table_names() == []
        connection.rollback()

        command.upgrade(config, "head")
        assert MigrationContext.configure(connection).get_current_revision() == head
        assert inspect(connection).has_table("organizations")
        connection.rollback()

        command.downgrade(config, "base")
        assert MigrationContext.configure(connection).get_current_revision() is None
        assert not inspect(connection).has_table("organizations")
        connection.rollback()

        command.upgrade(config, "head")
        command.check(config)
        assert MigrationContext.configure(connection).get_current_revision() == head


def test_readiness_succeeds_and_returns_connection_to_pool(
    migrated_database: Settings,
) -> None:
    app = create_app(migrated_database)
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert app.state.database_engine.pool.checkedout() == 0


def test_readiness_hides_real_connection_failure(test_database: Settings) -> None:
    # Keep the port bound without listening so the driver reaches a closed endpoint.
    with socket.socket() as unused_port:
        unused_port.bind(("127.0.0.1", 0))
        settings = test_database.model_copy(
            update={
                "database_host": "127.0.0.1",
                "database_port": unused_port.getsockname()[1],
            }
        )
        with TestClient(create_app(settings)) as client:
            readiness = client.get("/ready")
            health = client.get("/health")

    assert readiness.status_code == 503
    assert readiness.json() == {"detail": "Database unavailable"}
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


def test_sessions_commit_rollback_and_close(migrated_database: Settings) -> None:
    app = create_app(migrated_database)
    request = Request({"type": "http", "app": app})
    session_for_request = contextmanager(get_session)

    with TestClient(app):
        with session_for_request(request) as session, session.begin():
            organization = Organization(name="Synthetic Accounts Payable")
            session.add(organization)
            session.flush()
            assert isinstance(organization.id, UUID)
            assert organization.created_at.tzinfo is not None

        with session_for_request(request) as session:
            with pytest.raises(IntegrityError), session.begin():
                session.add(Organization(name="Rollback after error"))
                session.flush()
                session.add(Organization(name="   "))
                session.flush()
            assert session.scalars(select(Organization.name)).all() == [
                "Synthetic Accounts Payable"
            ]

        with session_for_request(request) as session:
            session.add(Organization(name="Uncommitted organization"))
            session.flush()

        with session_for_request(request) as session:
            assert session.scalars(select(Organization.name)).all() == [
                "Synthetic Accounts Payable"
            ]

        pool = app.state.database_engine.pool
        assert pool.checkedout() == 0
        assert pool.checkedin() > 0

    assert pool.checkedin() == 0


def test_postgresql_enforces_statement_timeout(engine: Engine) -> None:
    with engine.connect() as connection:
        assert connection.scalar(text("SHOW statement_timeout")) == "2s"
        with pytest.raises(OperationalError) as failure:
            connection.execute(text("SELECT pg_sleep(5)"))
        assert isinstance(failure.value.orig, QueryCanceled)
