"""Permissões do módulo matrícula.

Além do perfil, o service checa:
- vínculo: RESPONSAVEL só mexe em matrículas dos próprios filhos;
- status: RESPONSAVEL só cancela a própria pré-matrícula enquanto ela não entrou em análise.
"""

from app.core.roles import SECRETARIA_E_ADMIN, STAFF, Role
from app.modules.matricula.schemas import StatusMatricula

CAN_CREATE: tuple[Role, ...] = (*SECRETARIA_E_ADMIN, Role.RESPONSAVEL)
CAN_READ: tuple[Role, ...] = (*STAFF, Role.RESPONSAVEL)
CAN_REVIEW: tuple[Role, ...] = SECRETARIA_E_ADMIN  # iniciar análise, aprovar, rejeitar
CAN_CANCEL: tuple[Role, ...] = (*SECRETARIA_E_ADMIN, Role.RESPONSAVEL)
CAN_CHECK_DOCUMENTOS: tuple[Role, ...] = SECRETARIA_E_ADMIN
CAN_UPLOAD_DOCUMENTOS: tuple[Role, ...] = (*SECRETARIA_E_ADMIN, Role.RESPONSAVEL)

RESPONSAVEL_CAN_CANCEL_FROM = frozenset({StatusMatricula.PRE_MATRICULA})
UPLOAD_ALLOWED_IN = frozenset({StatusMatricula.PRE_MATRICULA, StatusMatricula.EM_ANALISE})


def is_staff(role: Role) -> bool:
    return role in STAFF
