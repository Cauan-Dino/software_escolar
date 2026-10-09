from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.shared.clock import now as clock_now
from decimal import Decimal


class TipoCobranca(StrEnum):
    MATRICULA = "MATRICULA"
    MENSALIDADE = "MENSALIDADE"
    TAXA_EXTRA = "TAXA_EXTRA"


class StatusCobranca(StrEnum):
    PENDENTE = "PENDENTE"
    PAGA = "PAGA"
    ATRASADA = "ATRASADA"
    CANCELADA = "CANCELADA"


class TabelaPreco(TimestampMixin, Base):
    __tablename__ = "tabela_precos"
    __table_args__ = (UniqueConstraint("serie", "ano_letivo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    serie: Mapped[str] = mapped_column(String(20))
    ano_letivo: Mapped[int] = mapped_column(index=True)
    valor_matricula: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    valor_mensalidade: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class Bolsa(TimestampMixin, Base):
    __tablename__ = "bolsas"
    __table_args__ = (
        CheckConstraint(
            "percentual_desconto >= 0 AND percentual_desconto <= 100",
            name="percentual_desconto_valido",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), index=True)
    percentual_desconto: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    motivo: Mapped[str] = mapped_column(String(255))
    vigencia_inicio: Mapped[date] = mapped_column(Date)
    vigencia_fim: Mapped[date | None] = mapped_column(Date, default=None)


class Cobranca(Base):
    __tablename__ = "cobrancas"

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), index=True)
    matricula_id: Mapped[int | None] = mapped_column(default=None)
    tipo: Mapped[TipoCobranca] = mapped_column(Enum(TipoCobranca, native_enum=False, length=20))
    competencia: Mapped[str | None] = mapped_column(String(7), default=None, index=True)
    valor_original: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    valor_desconto: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    valor_final: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    vencimento: Mapped[date] = mapped_column(Date)
    status: Mapped[StatusCobranca] = mapped_column(
        Enum(StatusCobranca, native_enum=False, length=20),
        default=StatusCobranca.PENDENTE,
        server_default=StatusCobranca.PENDENTE.value,
    )
    pago_em: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    gateway_referencia: Mapped[str | None] = mapped_column(String(100), default=None)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), default=clock_now)
