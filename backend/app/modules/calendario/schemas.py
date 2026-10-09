from datetime import date
from enum import StrEnum

from pydantic import Field, model_validator

from app.shared.schemas import InputSchema, OutputSchema


class TipoEvento(StrEnum):
    PROVA = "PROVA"
    FERIADO = "FERIADO"
    REUNIAO = "REUNIAO"
    EVENTO = "EVENTO"
    OUTRO = "OUTRO"


TITULO_LEN = Field(min_length=1, max_length=200)


class EventoCalendarioCreate(InputSchema):
    titulo: str = TITULO_LEN
    descricao: str | None = Field(default=None, max_length=2000)
    data_inicio: date
    data_fim: date | None = None
    tipo: TipoEvento
    turma_id: int | None = None

    @model_validator(mode="after")
    def valida_intervalo(self) -> "EventoCalendarioCreate":
        if self.data_fim is not None and self.data_fim < self.data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio.")
        return self


class EventoCalendarioUpdate(InputSchema):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    descricao: str | None = Field(default=None, max_length=2000)
    data_inicio: date | None = None
    data_fim: date | None = None
    tipo: TipoEvento | None = None

    @model_validator(mode="after")
    def valida_intervalo(self) -> "EventoCalendarioUpdate":
        if self.data_inicio is not None and self.data_fim is not None:
            if self.data_fim < self.data_inicio:
                raise ValueError("data_fim não pode ser anterior a data_inicio.")
        return self


class EventoCalendarioRead(OutputSchema):
    id: int
    titulo: str
    descricao: str | None
    data_inicio: date
    data_fim: date | None
    tipo: TipoEvento
    turma_id: int | None
    criado_por_user_id: int
