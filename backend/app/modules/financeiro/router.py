import hashlib
import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request, status

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.exceptions import BusinessRuleError, NotFoundError, UnauthorizedError
from app.core.roles import Role
from app.modules.financeiro import permissions, service
from app.modules.financeiro.models import StatusCobranca
from app.modules.financeiro.schemas import (
    BolsaCreate,
    BolsaRead,
    BolsaUpdate,
    CobrancaCreate,
    CobrancaRead,
    TabelaPrecoCreate,
    TabelaPrecoRead,
    TabelaPrecoUpdate,
)
from app.modules.pessoas import service as pessoas_service
from app.shared.pagination import Page, Pagination

router = APIRouter(prefix="/api/v1/financeiro", tags=["financeiro"])


# --- Cobranças --------------------------------------------------------------------------------


@router.get("/cobrancas", response_model=Page[CobrancaRead])
def list_cobrancas(
    db: DbSession,
    pagination: Pagination,
    user: CurrentUser = Depends(
        require_roles(*permissions.CAN_MANAGE_FINANCEIRO, Role.RESPONSAVEL, Role.ALUNO)
    ),
    aluno_id: Annotated[int | None, Query()] = None,
    status_filtro: Annotated[StatusCobranca | None, Query(alias="status")] = None,
) -> Page[CobrancaRead]:
    aluno_ids: list[int] | None = None
    if user.role == Role.RESPONSAVEL:
        if aluno_id is not None:
            pessoas_service.ensure_can_access_aluno(db, user, aluno_id)
        else:
            aluno_ids = pessoas_service.list_aluno_ids_do_usuario(db, user)
    elif user.role == Role.ALUNO:
        meu_aluno = pessoas_service.get_aluno_by_user(db, user.id)
        meu_aluno_id = meu_aluno.id if meu_aluno else None
        if aluno_id is not None:
            if meu_aluno_id is None or aluno_id != meu_aluno_id:
                raise NotFoundError("Aluno não encontrado.")
        else:
            aluno_ids = [meu_aluno_id] if meu_aluno_id is not None else []
    return service.list_cobrancas(
        db,
        aluno_id=aluno_id,
        aluno_ids=aluno_ids,
        status=status_filtro,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post("/cobrancas", response_model=CobrancaRead, status_code=status.HTTP_201_CREATED)
def create_cobranca(
    payload: CobrancaCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> CobrancaRead:
    return service.criar_cobranca_avulsa(db, payload)


@router.post("/cobrancas/gerar-mensalidades", response_model=list[CobrancaRead])
def gerar_mensalidades(
    db: DbSession,
    competencia: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> list[CobrancaRead]:
    return service.gerar_mensalidades(db, competencia)


@router.post("/cobrancas/{cobranca_id}/marcar-paga", response_model=CobrancaRead)
def marcar_cobranca_paga(
    cobranca_id: int,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> CobrancaRead:
    return service.marcar_cobranca_paga(db, cobranca_id, user)


# --- Webhook do gateway de pagamento (sem autenticação JWT) ----------------------------------


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook(
    request: Request,
    db: DbSession,
    x_signature: Annotated[str | None, Header(alias="X-Signature")] = None,
) -> dict[str, bool]:
    corpo_bruto = await request.body()
    if x_signature is None:
        raise UnauthorizedError("Assinatura ausente.", "MISSING_SIGNATURE")
    esperado = hmac.new(
        settings.payment_webhook_secret.encode(), corpo_bruto, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(esperado, x_signature):
        raise UnauthorizedError("Assinatura inválida.", "INVALID_SIGNATURE")

    payload = await request.json()
    cobranca_id = payload.get("cobranca_id")
    if cobranca_id is None:
        raise BusinessRuleError("Campo 'cobranca_id' é obrigatório.", "COBRANCA_ID_AUSENTE")
    service.marcar_cobranca_paga(db, int(cobranca_id))
    return {"ok": True}


# --- Bolsas -------------------------------------------------------------------------------------


@router.get("/bolsas", response_model=list[BolsaRead])
def list_bolsas(
    db: DbSession,
    aluno_id: Annotated[int | None, Query()] = None,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> list[BolsaRead]:
    return service.list_bolsas(db, aluno_id=aluno_id)


@router.post("/bolsas", response_model=BolsaRead, status_code=status.HTTP_201_CREATED)
def create_bolsa(
    payload: BolsaCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> BolsaRead:
    return service.create_bolsa(db, payload)


@router.patch("/bolsas/{bolsa_id}", response_model=BolsaRead)
def update_bolsa(
    bolsa_id: int,
    payload: BolsaUpdate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> BolsaRead:
    return service.update_bolsa(db, bolsa_id, payload)


# --- Tabela de preços ---------------------------------------------------------------------------


@router.get("/precos", response_model=list[TabelaPrecoRead])
def list_precos(
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> list[TabelaPrecoRead]:
    return service.list_precos(db)


@router.post("/precos", response_model=TabelaPrecoRead, status_code=status.HTTP_201_CREATED)
def create_preco(
    payload: TabelaPrecoCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> TabelaPrecoRead:
    return service.create_preco(db, payload)


@router.patch("/precos/{preco_id}", response_model=TabelaPrecoRead)
def update_preco(
    preco_id: int,
    payload: TabelaPrecoUpdate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FINANCEIRO)),
) -> TabelaPrecoRead:
    return service.update_preco(db, preco_id, payload)
