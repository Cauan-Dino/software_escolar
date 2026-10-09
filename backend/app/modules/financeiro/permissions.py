"""Permissões do módulo financeiro."""

from app.core.roles import Role

CAN_MANAGE_FINANCEIRO: tuple[Role, ...] = (Role.ADMIN, Role.FINANCEIRO)
