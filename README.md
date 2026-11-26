# DUSEMA AI

DUSEMA AI is an enterprise automation project. Its first release will help accounts payable teams validate synthetic invoices against purchase orders, review documentary evidence, and approve posting to a simulated ERP.

The first Foundation increment provides a local FastAPI application, validated environment settings, and CI checks. The only business-independent HTTP route is `GET /health`. It reports liveness. Database readiness will be introduced with persistence.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and open a terminal in the repository root. The setup was verified with uv 0.13.10. `.python-version` sets the interpreter version and `uv.lock` records dependency versions.

```sh
uv python install
uv sync --locked
uv run --no-sync uvicorn dusema.main:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/health` or run `curl.exe http://127.0.0.1:8000/health` in PowerShell. Expect HTTP 200 and `{"status":"ok"}`. Interactive API documentation is available at `/docs` in development.

The application defaults to `development`. To override it in PowerShell, copy `.env.example` with `Copy-Item .env.example .env` and edit `DUSEMA_ENVIRONMENT`, or set the corresponding process environment variable. Valid values are `development`, `test`, and `production`. Process environment variables take precedence over `.env`. Production disables the automatically generated API documentation. Keep `.env` local.

## Verify changes

```sh
uv sync --locked
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest
```

GitHub Actions uses these checks on pushes and pull requests. The first increment requires no model credentials or running database.

## Project documentation

- [Discovery and Definition of Done](docs/DISCOVERY.md)
- [Release roadmap](docs/ROADMAP.md)
- [Initial authentication and security policy](docs/SECURITY.md)
- [Architecture decisions](docs/adr/)
