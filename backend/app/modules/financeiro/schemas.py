from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.modules.financeiro.models import StatusCobranca, TipoCobranca
from app.shared.schemas import InputSchema, OutputSchema

Percentual = Field(ge=0, le=100)


# --- Eventos de domínio -------------------------------------------------------------------


@dataclass(frozen=True)
class CobrancaPaga:
    """Publicado quando uma cobrança é marcada como paga. O módulo `matricula` pode se
    inscrever nisso no futuro para ativar a matrícula."""

    cobranca_id: int
    aluno_id: int


# --- Tabela de preços ----------------------------------------------------------------------


class TabelaPrecoCreate(InputSchema):
    serie: str
    ano_letivo: int = Field(ge=2020, le=2100)
    valor_matricula: Decimal = Field(ge=0)
    valor_mensalidade: Decimal = Field(ge=0)


class TabelaPrecoUpdate(InputSchema):
    valor_matricula: Decimal | None = Field(default=None, ge=0)
    valor_mensalidade: Decimal | None = Field(default=None, ge=0)


class TabelaPrecoRead(OutputSchema):
    id: int
    serie: str
    ano_letivo: int
    valor_matricula: Decimal
    valor_mensalidade: Decimal


# --- Bolsas ----------------------------------------------------------------------------------


class BolsaCreate(InputSchema):
    aluno_id: int
    percentual_desconto: Decimal = Percentual
    motivo: str
    vigencia_inicio: date
    vigencia_fim: date | None = None


class BolsaUpdate(InputSchema):
    percentual_desconto: Decimal | None = Field(default=None, ge=0, le=100)
    motivo: str | None = None
    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None


class BolsaRead(OutputSchema):
    id: int
    aluno_id: int
    percentual_desconto: Decimal
    motivo: str
    vigencia_inicio: date
    vigencia_fim: date | None


# --- Cobranças -------------------------------------------------------------------------------


class CobrancaCreate(InputSchema):
    aluno_id: int
    tipo: TipoCobranca
    competencia: str | None = None
    valor_original: Decimal = Field(gt=0)
    vencimento: date
    matricula_id: int | None = None


class CobrancaRead(OutputSchema):
    id: int
    aluno_id: int
    matricula_id: int | None
    tipo: TipoCobranca
    competencia: str | None
    valor_original: Decimal
    valor_desconto: Decimal
    valor_final: Decimal
    vencimento: date
    status: StatusCobranca
    pago_em: datetime | None
    gateway_referencia: str | None
    criado_em: datetime
