"""Permissões do módulo notas."""

from app.core.roles import Role

# Quem pode lançar/consultar a grade de notas de uma turma: ADMIN, SECRETARIA e o
# PROFESSOR (checado no service que ele realmente leciona na turma).
CAN_LANCAR_NOTAS: tuple[Role, ...] = (Role.ADMIN, Role.SECRETARIA, Role.PROFESSOR)

# Quem pode ver o boletim de um aluno: equipe + professor (sem checagem extra) e o
# responsável (checado via pessoas.service.ensure_can_access_aluno).
CAN_VER_BOLETIM: tuple[Role, ...] = (
    Role.ADMIN,
    Role.SECRETARIA,
    Role.PROFESSOR,
    Role.RESPONSAVEL,
    Role.ALUNO,
)
