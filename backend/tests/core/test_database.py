from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import NAMING_CONVENTION, Base, get_db


def test_get_db_yields_a_session_and_closes_it():
    generator = get_db()
    session = next(generator)
    assert isinstance(session, Session)
    generator.close()


def test_base_uses_naming_convention():
    assert Base.metadata.naming_convention["pk"] == NAMING_CONVENTION["pk"]


def test_transactional_fixture_talks_to_postgres(db):
    assert db.execute(text("SELECT 1")).scalar_one() == 1
    version = db.execute(text("SHOW server_version")).scalar_one()
    assert int(version.split(".")[0]) >= 16
