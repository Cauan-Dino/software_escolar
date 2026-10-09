"""Permissões do módulo pessoas.

Perfis definem O QUE cada um pode fazer; a checagem de vínculo (responsável só vê os próprios
filhos) é feita no service por `ensure_can_access_aluno`.
"""

from app.core.roles import SECRETARIA_E_ADMIN, STAFF, Role

CAN_LIST_ALUNOS: tuple[Role, ...] = STAFF
CAN_VIEW_ALUNO: tuple[Role, ...] = (*STAFF, Role.RESPONSAVEL)
CAN_MANAGE_ALUNOS: tuple[Role, ...] = SECRETARIA_E_ADMIN
CAN_DELETE_ALUNO: tuple[Role, ...] = (Role.ADMIN,)

CAN_READ_RESPONSAVEIS: tuple[Role, ...] = STAFF
CAN_MANAGE_RESPONSAVEIS: tuple[Role, ...] = SECRETARIA_E_ADMIN

CAN_READ_PROFESSORES: tuple[Role, ...] = SECRETARIA_E_ADMIN
CAN_MANAGE_PROFESSORES: tuple[Role, ...] = SECRETARIA_E_ADMIN

CAN_MANAGE_FUNCIONARIOS: tuple[Role, ...] = (Role.ADMIN,)


def sees_any_aluno(role: Role) -> bool:
    """Perfis da equipe enxergam qualquer aluno; os demais só os vinculados."""
    return role in STAFF
