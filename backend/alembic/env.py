"""Configuração do Alembic. Lê a URL do banco de `app.core.config` e os models de
`app.all_models`. Os testes podem passar uma conexão pronta em `config.attributes`."""

from alembic import context
from sqlalchemy import Connection, create_engine

from app.all_models import metadata
from app.core.config import settings

config = context.config


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    url = config.attributes.get("url") or settings.database_url
    engine = create_engine(url)
    with engine.connect() as conn:
        _run(conn)
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
