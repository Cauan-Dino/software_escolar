"""Schemas do assistente: API pública (chat) e entradas das ferramentas.

As entradas das ferramentas reaproveitam os schemas dos módulos de negócio (mesma validação
da API) e só acrescentam os ids que, na API REST, ficam no caminho da URL.
"""

from datetime import date, datetime
from typing import Any

from pydantic import Field

from app.modules.assistente.models import StatusAcao
from app.modules.calendario.schemas import EventoCalendarioCreate, EventoCalendarioUpdate
from app.modules.comunicacao.schemas import AvisoCreate, AvisoUpdate
from app.modules.financeiro.schemas import (
    BolsaCreate,
    BolsaUpdate,
    CobrancaCreate,
    StatusCobranca,
    TabelaPrecoCreate,
    TabelaPrecoUpdate,
)
from app.modules.frequencia.schemas import RegistroFrequenciaInput, StatusFrequencia
from app.modules.matricula.schemas import PreMatriculaCreate, StatusMatricula, TipoDocumento
from app.modules.notas.schemas import NotaUpsert, Periodo
from app.modules.pessoas.schemas import (
    AlunoUpdate,
    ResponsavelDados,
    ResponsavelUpdate,
    VinculoCreate,
    VinculoUpdate,
)
from app.modules.turmas.schemas import TurmaUpdate
from app.shared.schemas import InputSchema, OutputSchema
from app.shared.serie import Serie

# --- API do chat ----------------------------------------------------------------------------


class MensagemInput(InputSchema):
    texto: str = Field(min_length=1, max_length=2000)


class AcaoRead(OutputSchema):
    id: str
    ferramenta: str
    titulo: str
    resumo: str
    destrutiva: bool
    status: StatusAcao
    expira_em: datetime
    decidida_em: datetime | None
    resultado: dict[str, Any] | None
    erro: str | None


class MensagemRead(OutputSchema):
    id: int
    role: str  # "user" | "assistant" | "acao"
    conteudo: str | None
    created_at: datetime
    acao: AcaoRead | None = None


class ConversaRead(OutputSchema):
    id: int
    titulo: str
    created_at: datetime
    updated_at: datetime


class ConversaDetalhe(ConversaRead):
    mensagens: list[MensagemRead] = Field(default_factory=list)


class RespostaChat(OutputSchema):
    """Mensagens novas geradas por um envio."""

    conversa_id: int
    mensagens: list[MensagemRead]


class DecisaoAcao(OutputSchema):
    """Resultado de confirmar/cancelar: a ação atualizada e a mensagem registrada no chat."""

    acao: AcaoRead
    mensagens: list[MensagemRead]


# --- Entradas das ferramentas: comuns ---------------------------------------------------------


class SemArgumentos(InputSchema):
    pass


class BuscaInput(InputSchema):
    busca: str | None = Field(
        default=None, max_length=100, description="Parte do nome (ou CPF completo)."
    )
    limite: int = Field(default=10, ge=1, le=20)


class LimiteInput(InputSchema):
    limite: int = Field(default=10, ge=1, le=20)


class AjudaInput(InputSchema):
    topico: str = Field(
        min_length=2,
        max_length=100,
        description="Assunto da dúvida, em poucas palavras (ex.: 'aprovar matrícula').",
    )


# --- Pessoas --------------------------------------------------------------------------------


class AlunoIdInput(InputSchema):
    aluno_id: int


class ResponsavelIdInput(InputSchema):
    responsavel_id: int


class AtualizarAlunoInput(AlunoUpdate):
    aluno_id: int


class VincularResponsavelInput(VinculoCreate):
    aluno_id: int


class AtualizarVinculoInput(VinculoUpdate):
    aluno_id: int
    responsavel_id: int


class RemoverVinculoInput(InputSchema):
    aluno_id: int
    responsavel_id: int


class CriarResponsavelInput(ResponsavelDados):
    pass


class AtualizarResponsavelInput(ResponsavelUpdate):
    responsavel_id: int


# --- Turmas ---------------------------------------------------------------------------------


class ListarTurmasInput(InputSchema):
    ano_letivo: int | None = None
    serie: Serie | None = None
    ativa: bool | None = None


class TurmaIdInput(InputSchema):
    turma_id: int


class AtualizarTurmaInput(TurmaUpdate):
    turma_id: int


class ProfessorTurmaInput(InputSchema):
    turma_id: int
    professor_id: int


# --- Matrículas -----------------------------------------------------------------------------


class ListarMatriculasInput(InputSchema):
    status: StatusMatricula | None = None
    ano_letivo: int | None = None
    serie: Serie | None = None
    limite: int = Field(default=10, ge=1, le=20)


class MatriculaIdInput(InputSchema):
    matricula_id: int


class AprovarMatriculaInput(InputSchema):
    matricula_id: int
    turma_id: int


class MotivoMatriculaInput(InputSchema):
    matricula_id: int
    motivo: str = Field(min_length=5, max_length=500)


class DocumentoMatriculaInput(InputSchema):
    matricula_id: int
    tipo: TipoDocumento
    entregue: bool


class CriarPreMatriculaInput(PreMatriculaCreate):
    pass


# --- Notas e frequência ---------------------------------------------------------------------


class GradeNotasInput(InputSchema):
    turma_id: int
    periodo: Periodo


class LancarNotaInput(NotaUpsert):
    turma_id: int
    aluno_id: int


class ChamadaDiaInput(InputSchema):
    turma_id: int
    data: date | None = Field(default=None, description="Padrão: hoje.")


class HistoricoFrequenciaInput(InputSchema):
    aluno_id: int
    de: date | None = Field(default=None, description="Padrão: 30 dias atrás.")
    ate: date | None = Field(default=None, description="Padrão: hoje.")


class LancarChamadaInput(InputSchema):
    turma_id: int
    data: date | None = Field(default=None, description="Padrão: hoje.")
    registros: list[RegistroFrequenciaInput] = Field(min_length=1, max_length=40)


class CorrigirFrequenciaInput(InputSchema):
    turma_id: int
    aluno_id: int
    data: date | None = Field(default=None, description="Padrão: hoje.")
    status: StatusFrequencia
    observacao: str | None = Field(default=None, max_length=500)


# --- Financeiro -----------------------------------------------------------------------------


class ListarCobrancasInput(InputSchema):
    aluno_id: int | None = None
    status: StatusCobranca | None = None
    limite: int = Field(default=10, ge=1, le=20)


class ListarBolsasInput(InputSchema):
    aluno_id: int | None = None


class CriarCobrancaInput(CobrancaCreate):
    pass


class GerarMensalidadesInput(InputSchema):
    competencia: str = Field(pattern=r"^\d{4}-\d{2}$", description="Mês no formato AAAA-MM.")


class CobrancaIdInput(InputSchema):
    cobranca_id: int


class CriarBolsaInput(BolsaCreate):
    pass


class AtualizarBolsaInput(BolsaUpdate):
    bolsa_id: int


class CriarPrecoInput(TabelaPrecoCreate):
    pass


class AtualizarPrecoInput(TabelaPrecoUpdate):
    preco_id: int


# --- Calendário e comunicação ---------------------------------------------------------------


class ListarEventosInput(InputSchema):
    de: date | None = Field(default=None, description="Padrão: hoje.")
    ate: date | None = Field(default=None, description="Padrão: 60 dias à frente.")
    turma_id: int | None = None


class CriarEventoInput(EventoCalendarioCreate):
    pass


class AtualizarEventoInput(EventoCalendarioUpdate):
    evento_id: int


class EventoIdInput(InputSchema):
    evento_id: int


class CriarAvisoInput(AvisoCreate):
    pass


class AtualizarAvisoInput(AvisoUpdate):
    aviso_id: int


class AvisoIdInput(InputSchema):
    aviso_id: int
