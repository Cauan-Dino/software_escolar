"""Regras de negócio do financeiro: cobranças, bolsas, preços e inadimplência.

Simplificações assumidas (ver relatório de implementação):
- `gerar_mensalidades` não cruza a série do aluno (isso vive em `matricula`/`turmas`, e o
  módulo `pessoas` não guarda a série do aluno diretamente). Usamos o preço cadastrado em
  `tabela_precos` para o ano letivo da competência, pegando o primeiro registro daquele ano
  (sem filtrar por série); se não houver nenhum, usamos um valor padrão fixo de R$ 500,00.
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import events
from app.core.config import settings
from app.core.deps import CurrentUser
from app.core.exceptions import NotFoundError
from app.modules.financeiro import repository
from app.modules.financeiro.models import Bolsa, Cobranca, StatusCobranca, TabelaPreco, TipoCobranca
from app.modules.financeiro.schemas import (
    BolsaCreate,
    BolsaRead,
    BolsaUpdate,
    CobrancaCreate,
    CobrancaPaga,
    CobrancaRead,
    TabelaPrecoCreate,
    TabelaPrecoRead,
    TabelaPrecoUpdate,
)
from app.modules.pessoas import service as pessoas_service
from app.shared import clock
from app.shared.pagination import Page

COBRANCA_NAO_ENCONTRADA = "Cobrança não encontrada."
BOLSA_NAO_ENCONTRADA = "Bolsa não encontrada."
PRECO_NAO_ENCONTRADO = "Tabela de preço não encontrada."

VALOR_MENSALIDADE_PADRAO = Decimal("500.00")


# --- Helpers de conversão ------------------------------------------------------------------


def _bolsa_read(bolsa: Bolsa) -> BolsaRead:
    return BolsaRead.model_validate(bolsa)


def _preco_read(preco: TabelaPreco) -> TabelaPrecoRead:
    return TabelaPrecoRead.model_validate(preco)


def _cobranca_read(cobranca: Cobranca) -> CobrancaRead:
    return CobrancaRead.model_validate(cobranca)


def _get_cobranca_or_404(db: Session, cobranca_id: int) -> Cobranca:
    cobranca = repository.get_cobranca(db, cobranca_id)
    if cobranca is None:
        raise NotFoundError(COBRANCA_NAO_ENCONTRADA)
    return cobranca


def _data_limite_vencida(hoje: date | None = None) -> date:
    referencia = hoje or clock.today()
    return referencia - timedelta(days=settings.inadimplencia_dias_tolerancia)


def _atualizar_atraso(cobranca: Cobranca, hoje: date) -> None:
    if cobranca.status == StatusCobranca.PENDENTE and cobranca.vencimento < hoje:
        cobranca.status = StatusCobranca.ATRASADA


# --- Bolsas ---------------------------------------------------------------------------------


def calcular_bolsa_ativa(db: Session, aluno_id: int, data_referencia: date) -> Decimal:
    """Percentual de desconto da bolsa vigente na data informada (0 se não houver)."""
    vigentes = repository.list_bolsas_vigentes(db, aluno_id, data_referencia)
    if not vigentes:
        return Decimal("0")
    return max(b.percentual_desconto for b in vigentes)


def list_bolsas(db: Session, *, aluno_id: int | None) -> list[BolsaRead]:
    return [_bolsa_read(b) for b in repository.list_bolsas(db, aluno_id=aluno_id)]


def create_bolsa(db: Session, data: BolsaCreate) -> BolsaRead:
    pessoas_service.get_aluno_read(db, data.aluno_id)  # 404 se não existir
    bolsa = Bolsa(**data.model_dump())
    repository.add(db, bolsa)
    db.commit()
    return _bolsa_read(bolsa)


def update_bolsa(db: Session, bolsa_id: int, data: BolsaUpdate) -> BolsaRead:
    bolsa = repository.get_bolsa(db, bolsa_id)
    if bolsa is None:
        raise NotFoundError(BOLSA_NAO_ENCONTRADA)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bolsa, field, value)
    db.commit()
    return _bolsa_read(bolsa)


# --- Tabela de preços ------------------------------------------------------------------------


def list_precos(db: Session) -> list[TabelaPrecoRead]:
    return [_preco_read(p) for p in repository.list_precos(db)]


def create_preco(db: Session, data: TabelaPrecoCreate) -> TabelaPrecoRead:
    preco = TabelaPreco(**data.model_dump())
    repository.add(db, preco)
    db.commit()
    return _preco_read(preco)


def update_preco(db: Session, preco_id: int, data: TabelaPrecoUpdate) -> TabelaPrecoRead:
    preco = repository.get_preco(db, preco_id)
    if preco is None:
        raise NotFoundError(PRECO_NAO_ENCONTRADO)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(preco, field, value)
    db.commit()
    return _preco_read(preco)


# --- Cobranças --------------------------------------------------------------------------------


def criar_cobranca_avulsa(db: Session, data: CobrancaCreate) -> CobrancaRead:
    """Cria uma cobrança avulsa (MATRICULA ou TAXA_EXTRA): sem bolsa, valor_final = valor_original."""
    pessoas_service.get_aluno_read(db, data.aluno_id)  # 404 se não existir
    cobranca = Cobranca(
        aluno_id=data.aluno_id,
        matricula_id=data.matricula_id,
        tipo=data.tipo,
        competencia=data.competencia,
        valor_original=data.valor_original,
        valor_desconto=Decimal("0"),
        valor_final=data.valor_original,
        vencimento=data.vencimento,
        status=StatusCobranca.PENDENTE,
    )
    repository.add(db, cobranca)
    db.commit()
    return _cobranca_read(cobranca)


def _valor_mensalidade_do_ano(db: Session, ano_letivo: int) -> Decimal:
    preco = repository.find_preco_by_ano(db, ano_letivo)
    if preco is not None:
        return preco.valor_mensalidade
    return VALOR_MENSALIDADE_PADRAO


def _vencimento_da_competencia(competencia: str) -> date:
    ano, mes = (int(p) for p in competencia.split("-"))
    return date(ano, mes, min(settings.dia_vencimento_mensalidade, 28))


def gerar_mensalidades(db: Session, competencia: str) -> list[CobrancaRead]:
    """Gera a mensalidade do mês `competencia` (AAAA-MM) para todo aluno ativo.

    Idempotente: não duplica se já existir cobrança MENSALIDADE para aluno+competencia.
    """
    ano_letivo = int(competencia.split("-")[0])
    valor_mensalidade = _valor_mensalidade_do_ano(db, ano_letivo)
    vencimento = _vencimento_da_competencia(competencia)

    # Página grande para cobrir todos os alunos ativos cadastrados.
    pagina = pessoas_service.list_alunos(db, busca=None, limit=10_000, offset=0)

    criadas: list[CobrancaRead] = []
    for item in pagina.items:
        if repository.find_mensalidade(db, item.id, competencia) is not None:
            continue
        percentual = calcular_bolsa_ativa(db, item.id, vencimento)
        desconto = (valor_mensalidade * percentual / Decimal("100")).quantize(Decimal("0.01"))
        valor_final = valor_mensalidade - desconto
        cobranca = Cobranca(
            aluno_id=item.id,
            tipo=TipoCobranca.MENSALIDADE,
            competencia=competencia,
            valor_original=valor_mensalidade,
            valor_desconto=desconto,
            valor_final=valor_final,
            vencimento=vencimento,
            status=StatusCobranca.PENDENTE,
        )
        repository.add(db, cobranca)
        criadas.append(_cobranca_read(cobranca))
    db.commit()
    return criadas


def list_cobrancas(
    db: Session,
    *,
    aluno_id: int | None,
    aluno_ids: list[int] | None,
    status: StatusCobranca | None,
    limit: int,
    offset: int,
) -> Page[CobrancaRead]:
    rows, total = repository.list_cobrancas(
        db, aluno_id=aluno_id, aluno_ids=aluno_ids, status=status, limit=limit, offset=offset
    )
    hoje = clock.today()
    atualizadas = False
    for cobranca in rows:
        status_antes = cobranca.status
        _atualizar_atraso(cobranca, hoje)
        if cobranca.status != status_antes:
            atualizadas = True
    if atualizadas:
        db.commit()
    return Page[CobrancaRead](
        items=[_cobranca_read(c) for c in rows], total=total, limit=limit, offset=offset
    )


def marcar_cobranca_paga(db: Session, cobranca_id: int, user: CurrentUser | None = None) -> CobrancaRead:
    cobranca = _get_cobranca_or_404(db, cobranca_id)
    cobranca.status = StatusCobranca.PAGA
    cobranca.pago_em = clock.now()
    db.flush()
    events.publish(db, CobrancaPaga(cobranca_id=cobranca.id, aluno_id=cobranca.aluno_id))
    db.commit()
    return _cobranca_read(cobranca)


# --- API pública para outros módulos (não fazem commit) --------------------------------------


def is_aluno_inadimplente(db: Session, aluno_id: int) -> bool:
    """True se o aluno tem cobrança PENDENTE vencida há mais de `inadimplencia_dias_tolerancia`."""
    data_limite = _data_limite_vencida()
    return len(repository.list_pendentes_vencidas(db, aluno_id, data_limite)) > 0
