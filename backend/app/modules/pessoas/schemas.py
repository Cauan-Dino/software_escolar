from datetime import date
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, Field, computed_field, model_validator

from app.core.roles import Role
from app.modules.auth.schemas import Email, Password
from app.shared import clock
from app.shared.cpf import CPF, MaskedCPF
from app.shared.schemas import InputSchema, OutputSchema


class Parentesco(StrEnum):
    MAE = "MAE"
    PAI = "PAI"
    AVO = "AVO"
    TIO = "TIO"
    OUTRO = "OUTRO"


class TipoFuncionario(StrEnum):
    ADMINISTRATIVO = "ADMINISTRATIVO"
    PRESTADOR_SERVICO = "PRESTADOR_SERVICO"


Nome = Annotated[str, Field(min_length=3, max_length=150)]
Telefone = Annotated[str, Field(min_length=8, max_length=20, pattern=r"^[0-9()+\-\s]+$")]


def _validate_birth_date(value: date) -> date:
    today = clock.today()
    if value > today:
        raise ValueError("Data de nascimento no futuro")
    if today.year - value.year > 15:
        raise ValueError("Idade incompatível com as séries atendidas pela escola")
    return value


DataNascimento = Annotated[date, AfterValidator(_validate_birth_date)]


# --- Alunos ------------------------------------------------------------------------------


class AlunoDados(InputSchema):
    """Dados básicos do aluno (também usados dentro da pré-matrícula)."""

    nome: Nome
    data_nascimento: DataNascimento
    cpf: CPF | None = None


class VinculoCreate(InputSchema):
    responsavel_id: int
    parentesco: Parentesco
    responsavel_financeiro: bool = False
    pode_buscar: bool = True


class VinculoUpdate(InputSchema):
    parentesco: Parentesco | None = None
    pode_buscar: bool | None = None
    responsavel_financeiro: Literal[True] | None = Field(
        default=None,
        description="Só aceita `true`: torna este o responsável financeiro (e tira do anterior).",
    )


def _ensure_one_financeiro[T: VinculoCreate](vinculos: list[T]) -> list[T]:
    if sum(1 for v in vinculos if v.responsavel_financeiro) != 1:
        raise ValueError("Informe exatamente 1 responsável financeiro")
    ids = [v.responsavel_id for v in vinculos]
    if len(ids) != len(set(ids)):
        raise ValueError("Responsável repetido")
    return vinculos


class AlunoCreate(AlunoDados):
    responsaveis: list[VinculoCreate] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def _check_vinculos(self) -> Self:
        _ensure_one_financeiro(self.responsaveis)
        return self


class AlunoUpdate(InputSchema):
    nome: Nome | None = None
    data_nascimento: DataNascimento | None = None
    cpf: CPF | None = None


class VinculoRead(OutputSchema):
    responsavel_id: int
    nome: str
    parentesco: Parentesco
    responsavel_financeiro: bool
    pode_buscar: bool


class AlunoRead(OutputSchema):
    id: int
    nome: str
    data_nascimento: date
    cpf: str | None
    responsaveis: list[VinculoRead] = Field(default_factory=list)


class AlunoListItem(OutputSchema):
    id: int
    nome: str
    data_nascimento: date
    cpf: MaskedCPF


# --- Responsáveis ------------------------------------------------------------------------


class AcessoCreate(InputSchema):
    """Cria uma conta de login vinculada à pessoa."""

    email: Email
    password: Password


class ResponsavelDados(InputSchema):
    nome: Nome
    cpf: CPF
    email: Email | None = None
    telefone: Telefone | None = None


class ResponsavelCreate(ResponsavelDados):
    acesso: AcessoCreate | None = None


class ResponsavelRegistro(InputSchema):
    """Cadastro público de um responsável (o perfil é SEMPRE RESPONSAVEL)."""

    nome: Nome
    cpf: CPF
    email: Email
    telefone: Telefone
    password: Password


class ResponsavelUpdate(InputSchema):
    nome: Nome | None = None
    email: Email | None = None
    telefone: Telefone | None = None


class ResponsavelRead(OutputSchema):
    id: int
    user_id: int | None
    nome: str
    cpf: str
    email: str | None
    telefone: str | None


class ResponsavelListItem(OutputSchema):
    id: int
    user_id: int | None
    nome: str
    cpf: MaskedCPF
    email: str | None
    telefone: str | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tem_acesso(self) -> bool:
        return self.user_id is not None


# --- Professores e funcionários ----------------------------------------------------------


class ProfessorCreate(InputSchema):
    nome: Nome
    cpf: CPF
    email: Email | None = None
    telefone: Telefone | None = None
    formacao: str | None = Field(default=None, max_length=150)
    acesso: AcessoCreate | None = None


class ProfessorUpdate(InputSchema):
    nome: Nome | None = None
    email: Email | None = None
    telefone: Telefone | None = None
    formacao: str | None = Field(default=None, max_length=150)


class ProfessorRead(OutputSchema):
    id: int
    user_id: int | None
    nome: str
    cpf: str
    email: str | None
    telefone: str | None
    formacao: str | None


class ProfessorListItem(OutputSchema):
    id: int
    user_id: int | None
    nome: str
    cpf: MaskedCPF
    email: str | None
    formacao: str | None


StaffRole = Literal[Role.ADMIN, Role.SECRETARIA, Role.FINANCEIRO]


class FuncionarioAcesso(AcessoCreate):
    role: StaffRole


class FuncionarioCreate(InputSchema):
    nome: Nome
    cpf: CPF
    email: Email | None = None
    telefone: Telefone | None = None
    cargo: str = Field(min_length=2, max_length=100)
    tipo: TipoFuncionario
    acesso: FuncionarioAcesso | None = None


class FuncionarioUpdate(InputSchema):
    nome: Nome | None = None
    email: Email | None = None
    telefone: Telefone | None = None
    cargo: str | None = Field(default=None, min_length=2, max_length=100)
    tipo: TipoFuncionario | None = None


class FuncionarioRead(OutputSchema):
    id: int
    user_id: int | None
    nome: str
    cpf: str
    email: str | None
    telefone: str | None
    cargo: str
    tipo: TipoFuncionario


class FuncionarioListItem(OutputSchema):
    id: int
    user_id: int | None
    nome: str
    cpf: MaskedCPF
    cargo: str
    tipo: TipoFuncionario
