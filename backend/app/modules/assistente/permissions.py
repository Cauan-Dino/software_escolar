"""Permissões do módulo assistente.

O chat é liberado a todo usuário autenticado. Cada FERRAMENTA tem os seus próprios perfis
(declarados em `tools.py` a partir destes grupos). Eles espelham os `permissions.py` dos
módulos de negócio: um teste de paridade (`tests/modules/assistente/test_tools.py`) compara com
as rotas reais e quebra se o assistente passar a permitir mais do que a API permite.
"""

from app.core.roles import ALL_ROLES, SECRETARIA_E_ADMIN, STAFF, Role

CAN_USE_ASSISTENTE: tuple[Role, ...] = ALL_ROLES

EQUIPE: tuple[Role, ...] = STAFF  # ADMIN, SECRETARIA, FINANCEIRO
SECRETARIA_ADMIN: tuple[Role, ...] = SECRETARIA_E_ADMIN
SOMENTE_ADMIN: tuple[Role, ...] = (Role.ADMIN,)
FINANCEIRO_ADMIN: tuple[Role, ...] = (Role.ADMIN, Role.FINANCEIRO)
ACADEMICO: tuple[Role, ...] = (Role.ADMIN, Role.SECRETARIA, Role.PROFESSOR)
EQUIPE_E_PROFESSOR: tuple[Role, ...] = (*STAFF, Role.PROFESSOR)
EQUIPE_E_FAMILIA: tuple[Role, ...] = (*STAFF, Role.RESPONSAVEL, Role.ALUNO)
ACADEMICO_E_FAMILIA: tuple[Role, ...] = (*ACADEMICO, Role.RESPONSAVEL, Role.ALUNO)
MATRICULA_LEITURA: tuple[Role, ...] = (*STAFF, Role.RESPONSAVEL)
MATRICULA_CRIAR_CANCELAR: tuple[Role, ...] = (*SECRETARIA_E_ADMIN, Role.RESPONSAVEL)
FINANCEIRO_LEITURA: tuple[Role, ...] = (*FINANCEIRO_ADMIN, Role.RESPONSAVEL, Role.ALUNO)
SOMENTE_RESPONSAVEL: tuple[Role, ...] = (Role.RESPONSAVEL,)
SOMENTE_ALUNO: tuple[Role, ...] = (Role.ALUNO,)
SOMENTE_PROFESSOR: tuple[Role, ...] = (Role.PROFESSOR,)
TODOS: tuple[Role, ...] = ALL_ROLES
