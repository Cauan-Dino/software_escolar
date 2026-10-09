from app.core.roles import ALL_ROLES, SECRETARIA_E_ADMIN, STAFF, Role


def test_role_groups():
    assert Role.RESPONSAVEL not in STAFF
    assert Role.PROFESSOR not in STAFF
    assert set(SECRETARIA_E_ADMIN) == {Role.ADMIN, Role.SECRETARIA}
    assert len(ALL_ROLES) == 5
