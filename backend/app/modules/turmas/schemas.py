from pydantic import Field, computed_field

from app.shared.schemas import InputSchema, OutputSchema
from app.shared.serie import Segmento, Serie, Turno

CAPACIDADE_MAXIMA = 30
"""Limite legal/pedagógico da escola: nenhuma turma passa de 30 alunos."""

TURNO_LABELS = {Turno.MANHA: "Manhã", Turno.TARDE: "Tarde", Turno.INTEGRAL: "Integral"}

AnoLetivo = Field(ge=2020, le=2100)


class TurmaCreate(InputSchema):
    serie: Serie
    ano_letivo: int = AnoLetivo
    turno: Turno
    capacidade: int = Field(default=CAPACIDADE_MAXIMA, ge=1, le=CAPACIDADE_MAXIMA)


class TurmaUpdate(InputSchema):
    capacidade: int | None = Field(default=None, ge=1, le=CAPACIDADE_MAXIMA)
    ativa: bool | None = None


class ProfessorDaTurma(InputSchema):
    professor_id: int


class ProfessorResumo(OutputSchema):
    id: int
    nome: str


class TurmaRead(OutputSchema):
    id: int
    serie: Serie
    ano_letivo: int
    turno: Turno
    capacidade: int
    vagas_ocupadas: int
    ativa: bool
    professores: list[ProfessorResumo] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nome(self) -> str:
        return f"{self.serie.label} - {TURNO_LABELS[self.turno]} - {self.ano_letivo}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def segmento(self) -> Segmento:
        return self.serie.segmento

    @computed_field  # type: ignore[prop-decorator]
    @property
    def vagas_disponiveis(self) -> int:
        return max(self.capacidade - self.vagas_ocupadas, 0)
