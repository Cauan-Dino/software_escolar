"""Tabelas do assistente: conversas, mensagens (histórico enviado ao LLM) e ações pendentes."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin

JsonValue = JSON().with_variant(JSONB(), "postgresql")


class StatusAcao(StrEnum):
    PENDENTE = "PENDENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    EXPIRADA = "EXPIRADA"
    FALHOU = "FALHOU"


class Conversa(TimestampMixin, Base):
    __tablename__ = "assistente_conversas"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    titulo: Mapped[str] = mapped_column(String(120), default="Nova conversa")


class Mensagem(Base):
    """Uma mensagem no formato do chat do LLM (user | assistant | tool).

    - `assistant` pode ter `tool_calls` (lista no formato OpenAI);
    - `tool` tem `tool_call_id` e, quando é a resposta de uma ferramenta de escrita que ficou
      aguardando confirmação, `acao_id`.
    """

    __tablename__ = "assistente_mensagens"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversa_id: Mapped[int] = mapped_column(
        ForeignKey("assistente_conversas.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(12))
    conteudo: Mapped[str | None] = mapped_column(Text)
    tool_calls: Mapped[list[dict[str, Any]] | None] = mapped_column(JsonValue)
    tool_call_id: Mapped[str | None] = mapped_column(String(80))
    acao_id: Mapped[str | None] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AcaoPendente(Base):
    """Ação de escrita proposta pelo modelo. Só vira efeito após o usuário confirmar."""

    __tablename__ = "assistente_acoes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversa_id: Mapped[int] = mapped_column(
        ForeignKey("assistente_conversas.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    ferramenta: Mapped[str] = mapped_column(String(60))
    argumentos: Mapped[dict[str, Any]] = mapped_column(JsonValue)
    resumo: Mapped[str] = mapped_column(Text)
    destrutiva: Mapped[bool] = mapped_column(default=False, server_default="false")
    status: Mapped[StatusAcao] = mapped_column(
        Enum(StatusAcao, native_enum=False, length=12), default=StatusAcao.PENDENTE, index=True
    )
    resultado: Mapped[dict[str, Any] | None] = mapped_column(JsonValue)
    erro: Mapped[str | None] = mapped_column(Text)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decidida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
