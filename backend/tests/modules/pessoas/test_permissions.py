from app.core.roles import Role
from app.modules.pessoas import permissions


def test_responsavel_can_view_but_not_list_or_manage_alunos():
    assert Role.RESPONSAVEL in permissions.CAN_VIEW_ALUNO
    assert Role.RESPONSAVEL not in permissions.CAN_LIST_ALUNOS
    assert Role.RESPONSAVEL not in permissions.CAN_MANAGE_ALUNOS


def test_only_admin_deletes_alunos_and_manages_funcionarios():
    assert permissions.CAN_DELETE_ALUNO == (Role.ADMIN,)
    assert permissions.CAN_MANAGE_FUNCIONARIOS == (Role.ADMIN,)


def test_sees_any_aluno_only_for_staff():
    assert permissions.sees_any_aluno(Role.SECRETARIA)
    assert not permissions.sees_any_aluno(Role.RESPONSAVEL)
    assert not permissions.sees_any_aluno(Role.PROFESSOR)
