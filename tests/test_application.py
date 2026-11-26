from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from dusema.main import create_app


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DUSEMA_ENVIRONMENT", raising=False)


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
