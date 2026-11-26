import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from dusema.config import Settings
from dusema.main import create_app


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for variable in list(os.environ):
        if variable.upper().startswith("DUSEMA_"):
            monkeypatch.delenv(variable)


def test_health_and_openapi_in_development() -> None:
    with TestClient(create_app()) as client:
        health = client.get("/health")
        schema = client.get("/openapi.json")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert schema.status_code == 200
    assert "get" in schema.json()["paths"]["/health"]


def test_production_keeps_health_available_and_hides_api_docs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DUSEMA_ENVIRONMENT", "production")

    with TestClient(create_app()) as client:
        assert client.get("/health").json() == {"status": "ok"}
        for path in ("/openapi.json", "/docs", "/redoc"):
            assert client.get(path).status_code == 404


def test_process_environment_overrides_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".env").write_text("DUSEMA_ENVIRONMENT=production\n", encoding="utf-8")
    assert create_app().openapi_url is None

    monkeypatch.setenv("DUSEMA_ENVIRONMENT", "test")
    assert create_app().openapi_url == "/openapi.json"


def test_invalid_environment_fails_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DUSEMA_ENVIRONMENT", "invalid")

    with pytest.raises(ValidationError, match="environment"):
        create_app()


def test_health_stays_live_without_database_configuration() -> None:
    with TestClient(create_app()) as client:
        readiness = client.get("/ready")
        health = client.get("/health")

    assert readiness.status_code == 503
    assert readiness.json() == {"detail": "Database unavailable"}
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


def test_database_settings_construct_a_safe_driver_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    example_password = "synthetic@password:/?%"
    monkeypatch.setenv("DUSEMA_DATABASE_PASSWORD", example_password)
    monkeypatch.setenv("DUSEMA_DATABASE_HOST", "postgres")
    monkeypatch.setenv("DUSEMA_DATABASE_PORT", "5432")

    settings = Settings()
    url = settings.database_url

    assert url is not None
    assert (url.drivername, url.host, url.port) == (
        "postgresql+psycopg",
        "postgres",
        5432,
    )
    assert (url.database, url.username, url.password) == (
        "dusema",
        "dusema",
        example_password,
    )
    assert example_password not in str(url)
    assert example_password not in repr(settings)


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("DUSEMA_DATABASE_PORT", "0"),
        ("DUSEMA_DATABASE_PORT", "65536"),
        ("DUSEMA_DATABASE_HOST", "host-one,host-two"),
        ("DUSEMA_DATABASE_NAME", "Invalid DB"),
        ("DUSEMA_DATABASE_USER", "Name With Spaces"),
        ("DUSEMA_DATABASE_PASSWORD", ""),
    ],
)
def test_database_settings_reject_invalid_values(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str
) -> None:
    monkeypatch.setenv(variable, value)
    with pytest.raises(ValidationError, match=variable.lower().removeprefix("dusema_")):
        Settings()
