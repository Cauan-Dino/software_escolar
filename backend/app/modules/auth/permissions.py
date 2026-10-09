"""Permissões do módulo auth."""

from app.core.roles import Role

# Gerenciar contas de usuário (criar, mudar perfil, desativar).
CAN_MANAGE_USERS: tuple[Role, ...] = (Role.ADMIN,)
