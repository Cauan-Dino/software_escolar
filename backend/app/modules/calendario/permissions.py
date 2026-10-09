"""Permissões do módulo calendario."""

from app.core.roles import Role

# A leitura de eventos é liberada a qualquer usuário autenticado (sem dados sensíveis),
# então o router usa Depends(get_current_user) direto, sem require_roles.
CAN_CREATE_EVENTO: tuple[Role, ...] = (Role.ADMIN, Role.SECRETARIA, Role.PROFESSOR)
