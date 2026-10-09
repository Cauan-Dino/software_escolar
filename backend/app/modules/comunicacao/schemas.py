from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from app.shared.schemas import InputSchema, OutputSchema


class PublicoAlvo(StrEnum):
    TODOS = "TODOS"
    TURMA = "TURMA"
    RESPONSAVEIS = "RESPONSAVEIS"
    PROFESSORES = "PROFESSORES"


class AvisoCreate(InputSchema):
    titulo: str = Field(min_length=1, max_length=200)
    corpo: str = Field(min_length=1)
    publico_alvo: PublicoAlvo
    turma_id: int | None = None
    fixado: bool = False

    @model_validator(mode="after")
    def _valida_turma(self) -> Self:
        if self.publico_alvo == PublicoAlvo.TURMA and self.turma_id is None:
            raise ValueError("turma_id é obrigatório quando publico_alvo é TURMA.")
        if self.publico_alvo != PublicoAlvo.TURMA and self.turma_id is not None:
            raise ValueError("turma_id só pode ser informado quando publico_alvo é TURMA.")
        return self


class AvisoUpdate(InputSchema):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    corpo: str | None = Field(default=None, min_length=1)
    publico_alvo: PublicoAlvo | None = None
    turma_id: int | None = None
    fixado: bool | None = None


class AvisoRead(OutputSchema):
    id: int
    titulo: str
    corpo: str
    publico_alvo: PublicoAlvo
    turma_id: int | None
    fixado: bool
    publicado_por_user_id: int
    publicado_em: datetime
    lido: bool = False


class NaoLidosTotal(OutputSchema):
    total: int
