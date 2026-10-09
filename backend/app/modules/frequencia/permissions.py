"""Permissões do módulo frequência."""

from app.core.roles import Role

CAN_LANCAR_FREQUENCIA: tuple[Role, ...] = (Role.ADMIN, Role.SECRETARIA, Role.PROFESSOR)
CAN_VER_FREQUENCIA: tuple[Role, ...] = (
    Role.ADMIN,
    Role.SECRETARIA,
    Role.PROFESSOR,
    Role.RESPONSAVEL,
    Role.ALUNO,
)
