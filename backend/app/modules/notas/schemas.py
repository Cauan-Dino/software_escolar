from datetime import datetime
from enum import StrEnum

from pydantic import Field

from app.shared.schemas import InputSchema, OutputSchema


class Periodo(StrEnum):
    BIMESTRE_1 = "BIMESTRE_1"
    BIMESTRE_2 = "BIMESTRE_2"
    BIMESTRE_3 = "BIMESTRE_3"
    BIMESTRE_4 = "BIMESTRE_4"


PERIODO_LABELS = {
    Periodo.BIMESTRE_1: "1º Bimestre",
    Periodo.BIMESTRE_2: "2º Bimestre",
    Periodo.BIMESTRE_3: "3º Bimestre",
    Periodo.BIMESTRE_4: "4º Bimestre",
}

# Lista fixa de disciplinas comuns (sem tabela própria).
DISCIPLINAS: list[str] = [
    "Português",
    "Matemática",
    "Ciências",
    "História",
    "Geografia",
    "Artes",
    "Educação Física",
    "Inglês",
]

ValorNota = Field(ge=0, le=10)


class NotaUpsert(InputSchema):
    disciplina: str
    periodo: Periodo
    valor: float = ValorNota
    observacao: str | None = None


class NotaRead(OutputSchema):
    id: int
    aluno_id: int
    turma_id: int
    disciplina: str
    periodo: Periodo
    valor: float
    observacao: str | None
    lancado_por_user_id: int
    lancado_em: datetime


class GradeCelula(OutputSchema):
    """Uma célula da grade de lançamento: nota de um aluno em uma disciplina."""

    nota_id: int | None
    aluno_id: int
    aluno_nome: str
    disciplina: str
    periodo: Periodo
    valor: float | None
    observacao: str | None


class TurmaGradeRead(OutputSchema):
    turma_id: int
    periodo: Periodo
    disciplinas: list[str] = Field(default_factory=lambda: list(DISCIPLINAS))
    celulas: list[GradeCelula] = Field(default_factory=list)


class NotaPeriodo(OutputSchema):
    periodo: Periodo
    valor: float
    observacao: str | None


class BoletimDisciplina(OutputSchema):
    disciplina: str
    notas: list[NotaPeriodo] = Field(default_factory=list)
    media: float | None
    situacao: str


class BoletimRead(OutputSchema):
    aluno_id: int
    disciplinas: list[BoletimDisciplina] = Field(default_factory=list)
