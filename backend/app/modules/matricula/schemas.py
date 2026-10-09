from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import Field, computed_field, model_validator

from app.modules.pessoas.schemas import AlunoDados, Parentesco, ResponsavelDados
from app.shared.schemas import InputSchema, OutputSchema
from app.shared.serie import Serie, Turno


class StatusMatricula(StrEnum):
    PRE_MATRICULA = "PRE_MATRICULA"
    EM_ANALISE = "EM_ANALISE"
    APROVADA = "APROVADA"
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    ATIVA = "ATIVA"
    REJEITADA = "REJEITADA"
    CANCELADA = "CANCELADA"


# Status em que a matrícula ocupa uma vaga na turma.
STATUS_OCUPANDO_VAGA = frozenset(
    {StatusMatricula.APROVADA, StatusMatricula.AGUARDANDO_PAGAMENTO, StatusMatricula.ATIVA}
)
STATUS_ENCERRADOS = frozenset({StatusMatricula.REJEITADA, StatusMatricula.CANCELADA})


class TipoMatricula(StrEnum):
    NOVA = "NOVA"
    REMATRICULA = "REMATRICULA"


class TipoDocumento(StrEnum):
    CERTIDAO_NASCIMENTO = "CERTIDAO_NASCIMENTO"
    CARTAO_VACINA = "CARTAO_VACINA"
    COMPROVANTE_RESIDENCIA = "COMPROVANTE_RESIDENCIA"
    DOCUMENTO_RESPONSAVEL = "DOCUMENTO_RESPONSAVEL"


DOCUMENTO_LABELS = {
    TipoDocumento.CERTIDAO_NASCIMENTO: "Certidão de nascimento",
    TipoDocumento.CARTAO_VACINA: "Cartão de vacina",
    TipoDocumento.COMPROVANTE_RESIDENCIA: "Comprovante de residência",
    TipoDocumento.DOCUMENTO_RESPONSAVEL: "Documento do responsável",
}

# Na rematrícula os documentos do aluno já estão na secretaria; pede-se só o que muda.
DOCUMENTOS_EXIGIDOS: dict[TipoMatricula, tuple[TipoDocumento, ...]] = {
    TipoMatricula.NOVA: tuple(TipoDocumento),
    TipoMatricula.REMATRICULA: (TipoDocumento.COMPROVANTE_RESIDENCIA,),
}


# --- Entradas ----------------------------------------------------------------------------


class ResponsavelPreMatricula(ResponsavelDados):
    parentesco: Parentesco
    responsavel_financeiro: bool = False
    pode_buscar: bool = True


class PreMatriculaCreate(InputSchema):
    """Pré-matrícula. Matrícula nova × rematrícula é decidido pelo BACK-END:

    - `aluno_id` informado, ou CPF do aluno já cadastrado → REMATRICULA (atualiza o aluno);
    - caso contrário → NOVA (cria o aluno).
    """

    aluno_id: int | None = None
    aluno: AlunoDados | None = None
    responsaveis: list[ResponsavelPreMatricula] = Field(default_factory=list, max_length=4)
    ano_letivo: int = Field(ge=2020, le=2100)
    serie: Serie
    turno: Turno
    tamanho_farda: str | None = Field(default=None, min_length=1, max_length=10)
    observacoes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.aluno_id is None and self.aluno is None:
            raise ValueError("Informe o aluno (dados ou aluno_id)")
        if sum(1 for r in self.responsaveis if r.responsavel_financeiro) > 1:
            raise ValueError("Apenas 1 responsável financeiro")
        cpfs = [r.cpf for r in self.responsaveis]
        if len(cpfs) != len(set(cpfs)):
            raise ValueError("Responsável repetido")
        return self


class AprovarMatricula(InputSchema):
    turma_id: int


class MotivoInput(InputSchema):
    motivo: str = Field(min_length=5, max_length=500)


class DocumentoCheck(InputSchema):
    entregue: bool


# --- Saídas ------------------------------------------------------------------------------


class DocumentoRead(OutputSchema):
    tipo: TipoDocumento
    entregue: bool
    arquivo_nome: str | None
    conferido_em: datetime | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def label(self) -> str:
        return DOCUMENTO_LABELS[self.tipo]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tem_arquivo(self) -> bool:
        return self.arquivo_nome is not None


class MatriculaRead(OutputSchema):
    id: int
    aluno_id: int
    aluno_nome: str
    ano_letivo: int
    serie: Serie
    turno: Turno
    turma_id: int | None
    turma_nome: str | None = None
    tipo: TipoMatricula
    status: StatusMatricula
    tamanho_farda: str | None
    farda_indisponivel: bool
    observacoes: str | None
    motivo_rejeicao: str | None
    motivo_cancelamento: str | None
    created_at: datetime
    decidido_em: datetime | None
    documentos: list[DocumentoRead] = Field(default_factory=list)
    proximos_status: list[StatusMatricula] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def serie_label(self) -> str:
        return self.serie.label

    @computed_field  # type: ignore[prop-decorator]
    @property
    def documentos_pendentes(self) -> int:
        return sum(1 for d in self.documentos if not d.entregue)
