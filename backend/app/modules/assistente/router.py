"""Endpoints do assistente de IA (chat com ferramentas e confirmação por botão)."""

from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.rate_limit import RateLimiter
from app.modules.assistente import permissions, service
from app.modules.assistente.llm import LLMClient
from app.modules.assistente.schemas import (
    ConversaDetalhe,
    ConversaRead,
    DecisaoAcao,
    MensagemInput,
    RespostaChat,
)

router = APIRouter(prefix="/api/v1/assistente", tags=["assistente"])

mensagem_limiter = RateLimiter("assistente", settings.assistente_rate_limit_per_minute)

AssistenteUser = Depends(require_roles(*permissions.CAN_USE_ASSISTENTE))


@router.post("/conversas", response_model=ConversaRead, status_code=status.HTTP_201_CREATED)
def create_conversa(db: DbSession, user: CurrentUser = AssistenteUser) -> ConversaRead:
    return service.create_conversa(db, user)


@router.get("/conversas", response_model=list[ConversaRead])
def list_conversas(db: DbSession, user: CurrentUser = AssistenteUser) -> list[ConversaRead]:
    return service.list_conversas(db, user)


@router.get("/conversas/{conversa_id}", response_model=ConversaDetalhe)
def get_conversa(
    conversa_id: int, db: DbSession, user: CurrentUser = AssistenteUser
) -> ConversaDetalhe:
    return service.get_conversa(db, conversa_id, user)


@router.delete("/conversas/{conversa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversa(conversa_id: int, db: DbSession, user: CurrentUser = AssistenteUser) -> None:
    service.delete_conversa(db, conversa_id, user)


@router.post("/conversas/{conversa_id}/mensagens", response_model=RespostaChat)
def enviar_mensagem(
    conversa_id: int,
    payload: MensagemInput,
    db: DbSession,
    llm_client: LLMClient = Depends(service.get_llm_client),
    user: CurrentUser = AssistenteUser,
) -> RespostaChat:
    mensagem_limiter.hit(str(user.id))
    return service.enviar_mensagem(db, conversa_id, payload.texto, user, llm_client)


@router.post("/acoes/{acao_id}/confirmar", response_model=DecisaoAcao)
def confirmar_acao(acao_id: str, db: DbSession, user: CurrentUser = AssistenteUser) -> DecisaoAcao:
    return service.confirmar_acao(db, acao_id, user)


@router.post("/acoes/{acao_id}/cancelar", response_model=DecisaoAcao)
def cancelar_acao(acao_id: str, db: DbSession, user: CurrentUser = AssistenteUser) -> DecisaoAcao:
    return service.cancelar_acao(db, acao_id, user)
