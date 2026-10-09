"""Permissões do módulo comunicacao."""

from app.core.roles import ALL_ROLES, Role

# Criação é liberada na rota para ADMIN/SECRETARIA/PROFESSOR; o service restringe o
# PROFESSOR a avisos de TURMA das turmas em que leciona.
CAN_CREATE_AVISO: tuple[Role, ...] = (Role.ADMIN, Role.SECRETARIA, Role.PROFESSOR)
CAN_READ_AVISOS: tuple[Role, ...] = ALL_ROLES
