from app.core.roles import Role
from app.modules.auth import permissions


def test_only_admin_manages_users():
    assert permissions.CAN_MANAGE_USERS == (Role.ADMIN,)
