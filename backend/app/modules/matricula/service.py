"""Regras da matrícula.

Fluxo: PRE_MATRICULA → EM_ANALISE → APROVADA → AGUARDANDO_PAGAMENTO → ATIVA,
com saídas para REJEITADA ou CANCELADA (ver MATRICULA_FSM).
"""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.audit import record_audit, snapshot
from app.core.deps import CurrentUser
from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.core.roles import Role
from app.modules.matricula import permissions, repository
from app.modules.matricula.models import DocumentoMatricula, Matricula
from app.modules.matricula.schemas import (
    DOCUMENTOS_EXIGIDOS,
    STATUS_ENCERRADOS,
    STATUS_OCUPANDO_VAGA,
    AprovarMatricula,
    DocumentoCheck,
    DocumentoRead,
    MatriculaRead,
    MotivoInput,
    PreMatriculaCreate,
    ResponsavelPreMatricula,
    StatusMatricula,
    TipoDocumento,
    TipoMatricula,
)
from app.modules.pessoas import service as pessoas_service
from app.modules.turmas import service as turmas_service
from app.shared import clock, storage
from app.shared.pagination import Page
from app.shared.serie import Serie
from app.shared.state_machine import StateMachine

S = StatusMatricula
MATRICULA_FSM = StateMachine(
    {
        S.PRE_MATRICULA: {S.EM_ANALISE, S.REJEITADA, S.CANCELADA},
        S.EM_ANALISE: {S.APROVADA, S.REJEITADA, S.CANCELADA},
        S.APROVADA: {S.AGUARDANDO_PAGAMENTO, S.CANCELADA},
        S.AGUARDANDO_PAGAMENTO: {S.ATIVA, S.CANCELADA},
        S.ATIVA: {S.CANCELADA},
    }
)
AUDIT_FIELDS = ["status", "turma_id", "motivo_rejeicao", "motivo_cancelamento"]
MATRICULA_NAO_ENCONTRADA = "Matrícula não encontrada."


# --- Conversão para schema ----------------------------------------------------------------


def _to_reads(db: Session, matriculas: list[Matricula]) -> list[MatriculaRead]:
    aluno_ids = list({m.aluno_id for m in matriculas})
    nomes = {
        a.id: a.nome
        for a in pessoas_service.list_alunos_reads(db, aluno_ids, include_deleted=True)
    }
    turmas = {
        tid: turmas_service.get_turma_read(db, tid).nome
        for tid in {m.turma_id for m in matriculas if m.turma_id is not None}
    }
    return [
        MatriculaRead(
            id=m.id,
            aluno_id=m.aluno_id,
            aluno_nome=nomes.get(m.aluno_id, "—"),
            ano_letivo=m.ano_letivo,
            serie=m.serie,
            turno=m.turno,
            turma_id=m.turma_id,
            turma_nome=turmas.get(m.turma_id) if m.turma_id else None,
            tipo=m.tipo,
            status=m.status,
            tamanho_farda=m.tamanho_farda,
            farda_indisponivel=m.farda_indisponivel,
            observacoes=m.observacoes,
            motivo_rejeicao=m.motivo_rejeicao,
            motivo_cancelamento=m.motivo_cancelamento,
            created_at=m.created_at,
            decidido_em=m.decidido_em,
            documentos=[DocumentoRead.model_validate(d) for d in m.documentos],
            proximos_status=sorted(MATRICULA_FSM.targets(m.status)),
        )
        for m in matriculas
    ]


def _to_read(db: Session, matricula: Matricula) -> MatriculaRead:
    db.refresh(matricula, ["documentos"])
    return _to_reads(db, [matricula])[0]


def _get_or_404(db: Session, matricula_id: int) -> Matricula:
    matricula = repository.get_matricula(db, matricula_id)
    if matricula is None:
        raise NotFoundError(MATRICULA_NAO_ENCONTRADA)
    return matricula


def _get_for_user(db: Session, matricula_id: int, user: CurrentUser) -> Matricula:
    """Carrega a matrícula checando o vínculo: matrícula de outra família → 404."""
    matricula = _get_or_404(db, matricula_id)
    if not permissions.is_staff(user.role):
        try:
            pessoas_service.ensure_can_access_aluno(
                db, user, matricula.aluno_id, include_deleted=True
            )
        except NotFoundError as exc:
            raise NotFoundError(MATRICULA_NAO_ENCONTRADA) from exc
    return matricula


# --- Pré-matrícula ------------------------------------------------------------------------


def _validate_ano_letivo(ano_letivo: int) -> None:
    ano_atual = clock.today().year
    if not ano_atual <= ano_letivo <= ano_atual + 1:
        raise BusinessRuleError(
            f"Matrículas abertas apenas para {ano_atual} e {ano_atual + 1}.",
            "ANO_LETIVO_INVALIDO",
        )


def _resolve_aluno(
    db: Session, data: PreMatriculaCreate, actor: CurrentUser
) -> tuple[int | None, TipoMatricula]:
    """Decide se é REMATRICULA (aluno já existe) ou NOVA."""
    if data.aluno_id is not None:
        pessoas_service.ensure_can_access_aluno(db, actor, data.aluno_id)
        return data.aluno_id, TipoMatricula.REMATRICULA
    if data.aluno is not None and data.aluno.cpf:
        existing = pessoas_service.find_aluno_by_cpf(db, data.aluno.cpf)
        if existing is not None:
            if actor.role == Role.RESPONSAVEL and existing.id not in (
                pessoas_service.list_aluno_ids_do_usuario(db, actor)
            ):
                # Não revela dados do aluno de outra família; a secretaria resolve.
                raise ConflictError(
                    "Já existe um aluno com este CPF. Procure a secretaria.",
                    "ALUNO_JA_CADASTRADO",
                )
            return existing.id, TipoMatricula.REMATRICULA
    return None, TipoMatricula.NOVA


def _link_responsaveis(
    db: Session, aluno_id: int, entradas: list[ResponsavelPreMatricula], actor: CurrentUser
) -> None:
    proprio_id: int | None = None
    proprio_cpf: str | None = None
    if actor.role == Role.RESPONSAVEL:
        proprio = pessoas_service.get_responsavel_by_user(db, actor.id)
        if proprio is None:
            raise ForbiddenError("Seu usuário não possui cadastro de responsável.")
        if proprio.cpf not in {e.cpf for e in entradas}:
            raise BusinessRuleError(
                "Inclua seus próprios dados entre os responsáveis.", "RESPONSAVEL_LOGADO_AUSENTE"
            )
        proprio_id, proprio_cpf = proprio.id, proprio.cpf

    for entrada in entradas:
        if actor.role == Role.RESPONSAVEL:
            # Um responsável nunca altera dados de outra pessoa já cadastrada: só cria novos.
            if entrada.cpf == proprio_cpf:
                assert proprio_id is not None
                responsavel_id = proprio_id
            else:
                responsavel_id = pessoas_service.create_responsavel_record(db, entrada).id
        else:
            responsavel_id = pessoas_service.upsert_responsavel_record(db, entrada).id
        pessoas_service.link_responsavel_record(
            db,
            aluno_id=aluno_id,
            responsavel_id=responsavel_id,
            parentesco=entrada.parentesco,
            responsavel_financeiro=entrada.responsavel_financeiro,
            pode_buscar=entrada.pode_buscar,
        )


def create_pre_matricula(
    db: Session, data: PreMatriculaCreate, actor: CurrentUser
) -> MatriculaRead:
    _validate_ano_letivo(data.ano_letivo)
    aluno_id, tipo = _resolve_aluno(db, data, actor)

    if tipo == TipoMatricula.REMATRICULA:
        assert aluno_id is not None
        if repository.get_em_aberto(db, aluno_id, data.ano_letivo) is not None:
            raise ConflictError(
                f"O aluno já possui matrícula em aberto para {data.ano_letivo}.",
                "MATRICULA_DUPLICADA",
            )
        if data.aluno is not None:
            pessoas_service.update_aluno_record(db, aluno_id, data.aluno)
        if data.responsaveis:
            if actor.role == Role.RESPONSAVEL:
                raise BusinessRuleError(
                    "Na rematrícula, alterações de responsáveis são feitas pela secretaria.",
                    "RESPONSAVEIS_PELA_SECRETARIA",
                )
            _link_responsaveis(db, aluno_id, data.responsaveis, actor)
    else:
        if sum(1 for r in data.responsaveis if r.responsavel_financeiro) != 1:
            raise BusinessRuleError(
                "Informe os responsáveis, com exatamente 1 responsável financeiro.",
                "RESPONSAVEIS_INVALIDOS",
            )
        assert data.aluno is not None
        aluno_id = pessoas_service.create_aluno_record(db, data.aluno).id
        _link_responsaveis(db, aluno_id, data.responsaveis, actor)

    matricula = Matricula(
        aluno_id=aluno_id,
        ano_letivo=data.ano_letivo,
        serie=data.serie,
        turno=data.turno,
        tipo=tipo,
        status=S.PRE_MATRICULA,
        tamanho_farda=data.tamanho_farda,
        farda_indisponivel=False,
        observacoes=data.observacoes,
        criado_por_user_id=actor.id,
    )
    repository.add(db, matricula)
    for tipo_documento in DOCUMENTOS_EXIGIDOS[tipo]:
        repository.add(
            db, DocumentoMatricula(matricula_id=matricula.id, tipo=tipo_documento, entregue=False)
        )
    db.commit()
    return _to_read(db, matricula)


# --- Consulta -----------------------------------------------------------------------------


def list_matriculas(
    db: Session,
    actor: CurrentUser,
    *,
    status: StatusMatricula | None,
    ano_letivo: int | None,
    serie: Serie | None,
    limit: int,
    offset: int,
) -> Page[MatriculaRead]:
    """Equipe vê todas; RESPONSAVEL vê só as dos próprios filhos."""
    aluno_ids = (
        None
        if permissions.is_staff(actor.role)
        else pessoas_service.list_aluno_ids_do_usuario(db, actor, include_deleted=True)
    )
    rows, total = repository.list_matriculas(
        db,
        status=status,
        ano_letivo=ano_letivo,
        serie=serie,
        aluno_ids=aluno_ids,
        limit=limit,
        offset=offset,
    )
    return Page[MatriculaRead](items=_to_reads(db, rows), total=total, limit=limit, offset=offset)


def get_matricula(db: Session, matricula_id: int, actor: CurrentUser) -> MatriculaRead:
    return _to_read(db, _get_for_user(db, matricula_id, actor))


# --- Análise, aprovação, rejeição, cancelamento -------------------------------------------


def _transition(matricula: Matricula, target: StatusMatricula) -> None:
    MATRICULA_FSM.ensure(matricula.status, target)
    matricula.status = target


def start_analise(db: Session, matricula_id: int, actor: CurrentUser) -> MatriculaRead:
    matricula = _get_or_404(db, matricula_id)
    _transition(matricula, S.EM_ANALISE)
    db.commit()
    return _to_read(db, matricula)


def approve_matricula(
    db: Session, matricula_id: int, data: AprovarMatricula, actor: CurrentUser
) -> MatriculaRead:
    matricula = _get_or_404(db, matricula_id)
    MATRICULA_FSM.ensure(matricula.status, S.APROVADA)
    pendentes = [d.tipo.value for d in matricula.documentos if not d.entregue]
    if pendentes:
        raise BusinessRuleError(
            f"Há documentos pendentes: {', '.join(pendentes)}.", "DOCUMENTOS_PENDENTES"
        )
    turma = turmas_service.get_turma_read(db, data.turma_id)
    if turma.serie != matricula.serie or turma.ano_letivo != matricula.ano_letivo:
        raise BusinessRuleError(
            "A turma escolhida não é da mesma série e ano letivo da matrícula.",
            "TURMA_INCOMPATIVEL",
        )
    before = snapshot(matricula, AUDIT_FIELDS)

    turmas_service.occupy_vaga(db, turma.id)  # lock de linha; sem vaga → 409
    matricula.turma_id = turma.id
    _transition(matricula, S.APROVADA)
    matricula.decidido_por_user_id = actor.id
    matricula.decidido_em = clock.now()
    _transition(matricula, S.AGUARDANDO_PAGAMENTO)

    record_audit(
        db,
        actor=actor,
        action="matricula.aprovar",
        entity="matricula",
        entity_id=matricula.id,
        before=before,
        after=snapshot(matricula, AUDIT_FIELDS),
    )
    db.commit()
    return _to_read(db, matricula)


def _release_resources(db: Session, matricula: Matricula, previous: StatusMatricula) -> None:
    """Desfaz o que a matrícula ocupava: vaga na turma."""
    if previous in STATUS_OCUPANDO_VAGA and matricula.turma_id is not None:
        turmas_service.release_vaga(db, matricula.turma_id)


def reject_matricula(
    db: Session, matricula_id: int, data: MotivoInput, actor: CurrentUser
) -> MatriculaRead:
    """Rejeita e CANCELA O CADASTRO: matrícula nova → exclusão lógica do aluno."""
    matricula = _get_or_404(db, matricula_id)
    before = snapshot(matricula, AUDIT_FIELDS)
    previous = matricula.status
    _transition(matricula, S.REJEITADA)
    matricula.motivo_rejeicao = data.motivo
    matricula.decidido_por_user_id = actor.id
    matricula.decidido_em = clock.now()
    _release_resources(db, matricula, previous)
    if matricula.tipo == TipoMatricula.NOVA:
        pessoas_service.soft_delete_aluno_record(db, matricula.aluno_id)
    record_audit(
        db,
        actor=actor,
        action="matricula.rejeitar",
        entity="matricula",
        entity_id=matricula.id,
        before=before,
        after=snapshot(matricula, AUDIT_FIELDS),
    )
    db.commit()
    return _to_read(db, matricula)


def cancel_matricula(
    db: Session, matricula_id: int, data: MotivoInput, actor: CurrentUser
) -> MatriculaRead:
    matricula = _get_for_user(db, matricula_id, actor)
    if actor.role == Role.RESPONSAVEL and (
        matricula.status not in permissions.RESPONSAVEL_CAN_CANCEL_FROM
    ):
        raise ForbiddenError(
            "Depois que a análise começou, o cancelamento deve ser pedido à secretaria.",
            "CANCELAMENTO_PELA_SECRETARIA",
        )
    before = snapshot(matricula, AUDIT_FIELDS)
    previous = matricula.status
    _transition(matricula, S.CANCELADA)
    matricula.motivo_cancelamento = data.motivo
    _release_resources(db, matricula, previous)
    if matricula.tipo == TipoMatricula.NOVA and previous in (S.PRE_MATRICULA, S.EM_ANALISE):
        pessoas_service.soft_delete_aluno_record(db, matricula.aluno_id)
    record_audit(
        db,
        actor=actor,
        action="matricula.cancelar",
        entity="matricula",
        entity_id=matricula.id,
        before=before,
        after=snapshot(matricula, AUDIT_FIELDS),
    )
    db.commit()
    return _to_read(db, matricula)


# --- Documentos ---------------------------------------------------------------------------


def _get_documento_or_404(
    db: Session, matricula_id: int, tipo: TipoDocumento
) -> DocumentoMatricula:
    documento = repository.get_documento(db, matricula_id, tipo)
    if documento is None:
        raise NotFoundError("Documento não exigido para esta matrícula.")
    return documento


def check_documento(
    db: Session, matricula_id: int, tipo: TipoDocumento, data: DocumentoCheck, actor: CurrentUser
) -> MatriculaRead:
    matricula = _get_or_404(db, matricula_id)
    if matricula.status in STATUS_ENCERRADOS:
        raise ConflictError("Matrícula encerrada.", "MATRICULA_ENCERRADA")
    documento = _get_documento_or_404(db, matricula_id, tipo)
    documento.entregue = data.entregue
    documento.conferido_por_user_id = actor.id if data.entregue else None
    documento.conferido_em = clock.now() if data.entregue else None
    db.commit()
    return _to_read(db, matricula)


def upload_documento(
    db: Session,
    matricula_id: int,
    tipo: TipoDocumento,
    *,
    filename: str,
    content: bytes,
    actor: CurrentUser,
) -> MatriculaRead:
    matricula = _get_for_user(db, matricula_id, actor)
    if matricula.status not in permissions.UPLOAD_ALLOWED_IN:
        raise ConflictError(
            "Documentos só podem ser enviados antes da decisão.", "MATRICULA_ENCERRADA"
        )
    documento = _get_documento_or_404(db, matricula_id, tipo)
    stored = storage.save_file(f"matriculas/{matricula_id}", filename, content)
    old_path = documento.arquivo_path
    documento.arquivo_path = stored.path
    documento.arquivo_nome = stored.original_name
    documento.arquivo_content_type = stored.content_type
    db.commit()
    if old_path:
        storage.delete_file(old_path)
    return _to_read(db, matricula)


@dataclass(frozen=True)
class ArquivoDocumento:
    path: Path
    content_type: str
    filename: str


def get_documento_arquivo(
    db: Session, matricula_id: int, tipo: TipoDocumento, actor: CurrentUser
) -> ArquivoDocumento:
    _get_for_user(db, matricula_id, actor)
    documento = _get_documento_or_404(db, matricula_id, tipo)
    if not documento.arquivo_path:
        raise NotFoundError("Nenhum arquivo enviado para este documento.")
    return ArquivoDocumento(
        path=storage.open_file(documento.arquivo_path),
        content_type=documento.arquivo_content_type or "application/octet-stream",
        filename=documento.arquivo_nome or "documento",
    )


# --- API pública para outros módulos (não fazem commit) -----------------------------------


def get_matricula_read(db: Session, matricula_id: int) -> MatriculaRead:
    return _to_read(db, _get_or_404(db, matricula_id))


def list_matriculas_do_aluno(db: Session, aluno_id: int) -> list[MatriculaRead]:
    return _to_reads(db, repository.list_by_aluno(db, aluno_id))


def list_aluno_ids_ativos_da_turma(db: Session, turma_id: int) -> list[int]:
    return repository.list_aluno_ids_por_status_na_turma(db, turma_id, {S.ATIVA})


def is_aluno_ativo_na_turma(db: Session, aluno_id: int, turma_id: int) -> bool:
    return aluno_id in list_aluno_ids_ativos_da_turma(db, turma_id)
