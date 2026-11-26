from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, create_engine
from sqlalchemy.pool import NullPool

from dusema.config import Settings
from dusema.models import Base

config = context.config


def run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_online_migrations() -> None:
    existing_connection = config.attributes.get("connection")
    if existing_connection is not None:
        run_migrations(existing_connection)
        return

    database_url = Settings().database_url
    if database_url is None:
        raise SystemExit(
            "Set DUSEMA_DATABASE_PASSWORD before running online migrations."
        )
    engine = create_engine(
        database_url,
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 2},
    )
    try:
        with engine.connect() as connection:
            run_migrations(connection)
    finally:
        engine.dispose()


if config.config_file_name is not None and "connection" not in config.attributes:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

if context.is_offline_mode():
    context.configure(
        dialect_name="postgresql", target_metadata=Base.metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_online_migrations()
