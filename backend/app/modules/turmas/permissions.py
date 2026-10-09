"""Permissões do módulo turmas."""

from app.core.roles import SECRETARIA_E_ADMIN, STAFF, Role

CAN_READ_TURMAS: tuple[Role, ...] = STAFF
CAN_MANAGE_TURMAS: tuple[Role, ...] = SECRETARIA_E_ADMIN
CAN_VIEW_OWN_TURMAS: tuple[Role, ...] = (Role.PROFESSOR,)
# Detalhe de uma turma: equipe, ou o professor que leciona nela (checado no service).
CAN_VIEW_TURMA: tuple[Role, ...] = (*STAFF, Role.PROFESSOR)
