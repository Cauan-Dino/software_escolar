"""Garante que as migrations do Alembic produzem exatamente o schema descrito nos models.

Se falhar depois de você alterar um model, gere a migration:
    uv run alembic revision --autogenerate -m "descricao" --rev-id 00XX
"""

from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.all_models import metadata
from tests.conftest import alembic_config


def test_models_and_migrations_are_in_sync(engine):
    with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        diff = compare_metadata(context, metadata)
    assert diff == [], f"Models e migrations divergem: {diff}"


def test_migration_history_is_linear():
    heads = ScriptDirectory.from_config(alembic_config()).get_heads()
    assert len(heads) == 1, f"Mais de uma head de migration: {heads}. Faça merge/rebase."
