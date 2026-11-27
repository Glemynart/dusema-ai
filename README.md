# DUSEMA AI

DUSEMA AI is an enterprise AI engineering portfolio project in active development. It demonstrates professional skills in designing, testing, and evaluating business workflows that combine AI-assisted document processing with deterministic validation, human approval, and auditability.

The first planned release focuses on accounts payable. It will help teams validate synthetic invoices against purchase orders, review documentary evidence, and approve posting to a simulated ERP.

Foundation provides a FastAPI application, a PostgreSQL development service, and a versioned Alembic schema. `GET /health` reports liveness. `GET /ready` checks whether the application can connect to PostgreSQL and run a query.

## Run locally

Install uv and Docker with Compose, then open a terminal in the repository root. `.python-version` sets the interpreter version and `uv.lock` records dependency versions. [uv installation](https://docs.astral.sh/uv/getting-started/installation/) · [Docker Compose installation](https://docs.docker.com/compose/install/)

Create a local `.env` from the example if one does not already exist. In PowerShell, use `if (-not (Test-Path .env)) { Copy-Item .env.example .env }`. Set a disposable development password before the first database start. Keep `.env` outside version control.

```sh
uv python install
uv sync --locked
docker compose up -d --wait --wait-timeout 60 postgres
uv run --no-sync alembic upgrade head
uv run --no-sync uvicorn dusema.main:create_app --factory --host 127.0.0.1 --port 8000
```

| Variable | Default and purpose |
| --- | --- |
| `DUSEMA_ENVIRONMENT` | `development`. Valid values are `development`, `test`, and `production`. The production setting disables the generated OpenAPI and docs routes. |
| `DUSEMA_DATABASE_HOST` | `127.0.0.1` for the host application. Use `postgres` from a container on the Compose network. |
| `DUSEMA_DATABASE_PORT` | `55436` for the host application and Compose host port. PostgreSQL listens on `5432` inside the container. |
| `DUSEMA_DATABASE_NAME` | `dusema`. Database initialized by Compose and selected by the application. Use lowercase SQL identifiers for the database and role. |
| `DUSEMA_DATABASE_USER` | `dusema`. The Compose service uses this role to initialize the local database. |
| `DUSEMA_DATABASE_PASSWORD` | Required to initialize Compose and connect. Use a disposable value for development. Missing configuration leaves the process live and readiness returns HTTP 503. |

Process environment variables take precedence over `.env`. The database publishes its port on loopback and persists data in a named volume. The Compose PostgreSQL image is pinned by version and digest. [Official PostgreSQL image](https://hub.docker.com/_/postgres)

## Operate and check PostgreSQL

```sh
docker compose ps
docker compose logs --tail 30 postgres
docker compose stop postgres
docker compose up -d --wait --wait-timeout 60 postgres
docker compose restart postgres
docker compose down
```

Use `stop` to pause the service, `restart` to restart the existing container, and `down` to remove the service and network while retaining the named volume. After a restart, check `docker compose ps` for a healthy service. Use `up` after changing the Compose definition. The image initializes the database, role, and password only when the data directory is empty.

With the API running, execute these commands in another PowerShell terminal.

```powershell
curl.exe -i http://127.0.0.1:8000/health
curl.exe -i http://127.0.0.1:8000/ready
```

Both return HTTP 200 with `{"status":"ok"}` when PostgreSQL is available. With PostgreSQL stopped, `/health` still returns 200 and `/ready` returns 503 with `{"detail":"Database unavailable"}`. Liveness monitors the process. Readiness can keep traffic away from an instance during a database outage. `/ready` checks connectivity. Apply migrations explicitly before running workflows that use the schema. API documentation is available at `/docs` in development.

For a port conflict, set a free loopback port in `.env` and run `docker compose up -d --wait postgres` again. If credentials change for an existing volume, update the database role first or use a separate disposable Compose project. For readiness failures, check `docker compose ps`, the PostgreSQL logs, and the application's connection settings.

## Migrate the schema

```sh
uv run --no-sync alembic upgrade head
uv run --no-sync alembic current --check-heads
uv run --no-sync alembic check
```

Revision `0001_create_organizations` establishes organizational identity for future role and resource scoping. It creates the UUID key, organization name, and creation timestamp. Alembic reads the same environment settings as the application. The CLI can also render SQL with `alembic upgrade head --sql`.

Use `uv run --no-sync alembic downgrade base` only with a disposable database when practicing reversals. That revision reversal drops `organizations` and its data. Follow it with `uv run --no-sync alembic upgrade head` to reapply the schema. [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

## Sessions and transactions

Each app instance owns a synchronous SQLAlchemy engine with a connection pool. FastAPI executes the synchronous readiness handler off the event loop. A request gets its own short-lived SQLAlchemy session. Write operations should use `with session.begin()` to commit on success or roll back when an exception escapes the block. Closing the request session releases resources and discards uncommitted writes. Keep model calls and document processing outside open database transactions. [SQLAlchemy transaction management](https://docs.sqlalchemy.org/en/21/orm/session_transaction.html)

The readiness path sets separate two-second bounds for obtaining a pooled connection, establishing a PostgreSQL connection, and executing a server-side statement. SQLAlchemy checks pooled connections before reuse so the app can recover after PostgreSQL restarts. Alembic uses its own short-lived migration connection. [SQLAlchemy pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html) · [PostgreSQL connection parameters](https://www.postgresql.org/docs/18/libpq-connect.html)

## Verify changes

```sh
uv sync --locked
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest
uv run --no-sync pytest -m integration
```

`pytest` runs the unit tests with no database. `pytest -m integration` requires the disposable local PostgreSQL service and a role with `CREATEDB`. Each database test creates and drops its own database with a generated name. The integration suite exercises real transactions, downtime handling, session cleanup, initial migration, rollback, reapplication, and schema comparison.

GitHub Actions performs these checks with a temporary PostgreSQL service, including migrations against an empty database. Hosted CI could not start during verification because GitHub reported an account billing or spending-limit issue. The same Python checks, migrations, and tests were run locally in Linux while hosted CI was unavailable.

## Project documentation

- [Discovery and Definition of Done](docs/DISCOVERY.md)
- [Release roadmap](docs/ROADMAP.md)
- [Initial authentication and security policy](docs/SECURITY.md)
- [Architecture decisions](docs/adr/)
