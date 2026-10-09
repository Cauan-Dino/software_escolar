from datetime import date
from enum import StrEnum

from pydantic import Field

from app.shared.schemas import InputSchema, OutputSchema


class StatusFrequencia(StrEnum):
    PRESENTE = "PRESENTE"
    FALTA = "FALTA"
    FALTA_JUSTIFICADA = "FALTA_JUSTIFICADA"


# Status que contam como presença para o cálculo do percentual de presença.
STATUS_CONTAM_PRESENCA = frozenset({StatusFrequencia.PRESENTE, StatusFrequencia.FALTA_JUSTIFICADA})


# --- Entradas ------------------------------------------------------------------------------


class RegistroFrequenciaInput(InputSchema):
    aluno_id: int
    status: StatusFrequencia
    observacao: str | None = Field(default=None, max_length=500)


class LancarChamada(InputSchema):
    registros: list[RegistroFrequenciaInput] = Field(default_factory=list, min_length=1)


class CorrigirRegistro(InputSchema):
    status: StatusFrequencia
    observacao: str | None = Field(default=None, max_length=500)


# --- Saídas --------------------------------------------------------------------------------


class AlunoChamada(OutputSchema):
    """Um aluno da turma na chamada do dia: status já lançado, ou PRESENTE como sugestão."""

    aluno_id: int
    aluno_nome: str
    status: StatusFrequencia
    observacao: str | None = None
    lancado: bool
    """Se já existe um registro gravado para este aluno nesta data."""


class FrequenciaRead(OutputSchema):
    id: int
    aluno_id: int
    turma_id: int
    data: date
    status: StatusFrequencia
    observacao: str | None


class HistoricoFrequencia(OutputSchema):
    aluno_id: int
    de: date
    ate: date
    percentual_presenca: float
    registros: list[FrequenciaRead] = Field(default_factory=list)
