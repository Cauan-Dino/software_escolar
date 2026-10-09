"""Regras de turmas: capacidade máxima de 30 alunos e controle de vagas com lock de linha."""

from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.core.roles import Role
from app.modules.pessoas import service as pessoas_service
from app.modules.turmas import repository
from app.modules.turmas.models import Turma, TurmaProfessor
from app.modules.turmas.schemas import (
    ProfessorResumo,
    TurmaCreate,
    TurmaRead,
    TurmaUpdate,
)
from app.shared.serie import Serie, Turno

TURMA_NAO_ENCONTRADA = "Turma não encontrada."


def _to_read(db: Session, turma: Turma) -> TurmaRead:
    professores = pessoas_service.list_professores_reads(
        db, repository.list_professor_ids(db, turma.id)
    )
    read = TurmaRead.model_validate(turma)
    read.professores = [ProfessorResumo(id=p.id, nome=p.nome) for p in professores]
    return read


def _get_or_404(db: Session, turma_id: int) -> Turma:
    turma = repository.get_turma(db, turma_id)
    if turma is None:
        raise NotFoundError(TURMA_NAO_ENCONTRADA)
    return turma


# --- Casos de uso ------------------------------------------------------------------------


def list_turmas(
    db: Session, *, ano_letivo: int | None, serie: Serie | None, ativa: bool | None
) -> list[TurmaRead]:
    turmas = repository.list_turmas(db, ano_letivo=ano_letivo, serie=serie, ativa=ativa)
    return [_to_read(db, t) for t in turmas]


def get_turma(db: Session, turma_id: int, user: CurrentUser) -> TurmaRead:
    turma = _get_or_404(db, turma_id)
    if user.role == Role.PROFESSOR and not is_professor_da_turma(db, turma_id, user.id):
        raise NotFoundError(TURMA_NAO_ENCONTRADA)
    return _to_read(db, turma)


def create_turma(db: Session, data: TurmaCreate) -> TurmaRead:
    if repository.find_turma(db, data.serie, data.ano_letivo, data.turno) is not None:
        raise ConflictError(
            "Já existe turma desta série, turno e ano letivo.", "TURMA_JA_EXISTE"
        )
    turma = Turma(**data.model_dump(), vagas_ocupadas=0, ativa=True)
    repository.add(db, turma)
    db.commit()
    return _to_read(db, turma)


def update_turma(db: Session, turma_id: int, data: TurmaUpdate) -> TurmaRead:
    turma = repository.get_turma_for_update(db, turma_id)
    if turma is None:
        raise NotFoundError(TURMA_NAO_ENCONTRADA)
    if data.capacidade is not None:
        if data.capacidade < turma.vagas_ocupadas:
            raise BusinessRuleError(
                f"A turma já tem {turma.vagas_ocupadas} alunos; a capacidade não pode ser menor.",
                "CAPACIDADE_ABAIXO_OCUPACAO",
            )
        turma.capacidade = data.capacidade
    if data.ativa is not None:
        turma.ativa = data.ativa
    db.commit()
    return _to_read(db, turma)


def add_professor(db: Session, turma_id: int, professor_id: int) -> TurmaRead:
    turma = _get_or_404(db, turma_id)
    pessoas_service.get_professor(db, professor_id)  # 404 se não existir
    if repository.get_turma_professor(db, turma_id, professor_id) is None:
        repository.add(db, TurmaProfessor(turma_id=turma_id, professor_id=professor_id))
    db.commit()
    return _to_read(db, turma)


def remove_professor(db: Session, turma_id: int, professor_id: int) -> TurmaRead:
    turma = _get_or_404(db, turma_id)
    link = repository.get_turma_professor(db, turma_id, professor_id)
    if link is None:
        raise NotFoundError("Este professor não leciona nesta turma.")
    repository.delete(db, link)
    db.commit()
    return _to_read(db, turma)


def list_minhas_turmas(db: Session, user: CurrentUser) -> list[TurmaRead]:
    professor = pessoas_service.get_professor_by_user(db, user.id)
    if professor is None:
        raise ForbiddenError("Seu usuário não está vinculado a um cadastro de professor.")
    ids = repository.list_turma_ids_do_professor(db, professor.id)
    return [_to_read(db, t) for t in repository.list_turmas(db, turma_ids=ids)]


# --- API pública para outros módulos (não fazem commit) -----------------------------------


def get_turma_read(db: Session, turma_id: int) -> TurmaRead:
    return _to_read(db, _get_or_404(db, turma_id))


def find_turma(db: Session, serie: Serie, ano_letivo: int, turno: Turno) -> TurmaRead | None:
    turma = repository.find_turma(db, serie, ano_letivo, turno)
    return _to_read(db, turma) if turma else None


def occupy_vaga(db: Session, turma_id: int) -> TurmaRead:
    """Ocupa uma vaga com lock de linha. Sem vaga → 409 VAGA_INDISPONIVEL.

    Não faz commit: participa da transação de quem chamou (o lock vale até o commit dela).
    """
    turma = repository.get_turma_for_update(db, turma_id)
    if turma is None:
        raise NotFoundError(TURMA_NAO_ENCONTRADA)
    if not turma.ativa:
        raise BusinessRuleError("Turma inativa.", "TURMA_INATIVA")
    if turma.vagas_ocupadas >= turma.capacidade:
        raise ConflictError(
            f"A turma {turma.serie.label} ({turma.ano_letivo}) está sem vagas "
            f"({turma.vagas_ocupadas}/{turma.capacidade}).",
            "VAGA_INDISPONIVEL",
        )
    turma.vagas_ocupadas += 1
    db.flush()
    return _to_read(db, turma)


def release_vaga(db: Session, turma_id: int) -> None:
    """Libera uma vaga (matrícula cancelada). Não faz commit."""
    turma = repository.get_turma_for_update(db, turma_id)
    if turma is not None and turma.vagas_ocupadas > 0:
        turma.vagas_ocupadas -= 1
        db.flush()


def is_professor_da_turma(db: Session, turma_id: int, user_id: int) -> bool:
    professor = pessoas_service.get_professor_by_user(db, user_id)
    if professor is None:
        return False
    return repository.get_turma_professor(db, turma_id, professor.id) is not None
