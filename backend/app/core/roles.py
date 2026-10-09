"""Perfis de acesso (RBAC) usados em todo o sistema."""

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"  # direção
    SECRETARIA = "SECRETARIA"
    FINANCEIRO = "FINANCEIRO"
    PROFESSOR = "PROFESSOR"
    RESPONSAVEL = "RESPONSAVEL"
    ALUNO = "ALUNO"


# Agrupamentos reutilizados pelos permissions.py dos módulos.
STAFF: tuple[Role, ...] = (Role.ADMIN, Role.SECRETARIA, Role.FINANCEIRO)
SECRETARIA_E_ADMIN: tuple[Role, ...] = (Role.ADMIN, Role.SECRETARIA)
ALL_ROLES: tuple[Role, ...] = tuple(Role)
