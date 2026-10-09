"""Regras do boletim: upsert de notas por (aluno, turma, disciplina, período) e cálculo
de média/situação do boletim."""

from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.roles import Role
from app.modules.matricula import service as matricula_service
from app.modules.notas import repository
from app.modules.notas.models import Nota
from app.modules.notas.schemas import (
    DISCIPLINAS,
    BoletimDisciplina,
    BoletimRead,
    GradeCelula,
    NotaPeriodo,
    NotaRead,
    NotaUpsert,
    Periodo,
    TurmaGradeRead,
)
from app.modules.pessoas import service as pessoas_service
from app.modules.turmas import service as turmas_service


def _ensure_pode_lancar(db: Session, turma_id: int, user: CurrentUser) -> None:
    """ADMIN/SECRETARIA sempre podem; PROFESSOR só se leciona nesta turma."""
    if user.role == Role.PROFESSOR and not turmas_service.is_professor_da_turma(
        db, turma_id, user.id
    ):
        raise ForbiddenError("Você não leciona nesta turma.")


def _to_read(nota: Nota) -> NotaRead:
    return NotaRead.model_validate(nota)


def list_grade(db: Session, turma_id: int, periodo: Periodo, user: CurrentUser) -> TurmaGradeRead:
    _ensure_pode_lancar(db, turma_id, user)

    aluno_ids = matricula_service.list_aluno_ids_ativos_da_turma(db, turma_id)
    alunos = {a.id: a for a in pessoas_service.list_alunos_reads(db, aluno_ids)}
    notas = repository.list_notas_turma(db, turma_id, periodo)
    notas_por_chave = {(n.aluno_id, n.disciplina): n for n in notas}

    celulas: list[GradeCelula] = []
    for aluno_id in aluno_ids:
        aluno = alunos.get(aluno_id)
        if aluno is None:
            continue
        for disciplina in DISCIPLINAS:
            nota = notas_por_chave.get((aluno_id, disciplina))
            celulas.append(
                GradeCelula(
                    nota_id=nota.id if nota else None,
                    aluno_id=aluno_id,
                    aluno_nome=aluno.nome,
                    disciplina=disciplina,
                    periodo=periodo,
                    valor=float(nota.valor) if nota else None,
                    observacao=nota.observacao if nota else None,
                )
            )
    return TurmaGradeRead(turma_id=turma_id, periodo=periodo, disciplinas=DISCIPLINAS, celulas=celulas)


def upsert_nota(
    db: Session, turma_id: int, aluno_id: int, data: NotaUpsert, user: CurrentUser
) -> NotaRead:
    _ensure_pode_lancar(db, turma_id, user)
    pessoas_service.get_aluno_read(db, aluno_id)  # 404 se o aluno não existir

    nota = repository.get_nota(db, aluno_id, turma_id, data.disciplina, data.periodo)
    if nota is None:
        nota = Nota(
            aluno_id=aluno_id,
            turma_id=turma_id,
            disciplina=data.disciplina,
            periodo=data.periodo,
            valor=data.valor,
            observacao=data.observacao,
            lancado_por_user_id=user.id,
        )
        repository.add(db, nota)
    else:
        nota.valor = data.valor
        nota.observacao = data.observacao
        nota.lancado_por_user_id = user.id

    db.commit()
    return _to_read(nota)


def find_nota(
    db: Session, aluno_id: int, turma_id: int, disciplina: str, periodo: Periodo
) -> NotaRead | None:
    """API pública: nota já lançada para aluno+turma+disciplina+período (ou None)."""
    nota = repository.get_nota(db, aluno_id, turma_id, disciplina, periodo)
    return _to_read(nota) if nota else None


def _situacao(media: float | None) -> str:
    if media is None:
        return "SEM_NOTA"
    if media >= 6:
        return "APROVADO"
    if media >= 4:
        return "RECUPERACAO"
    return "REPROVADO"


def get_boletim(db: Session, aluno_id: int, user: CurrentUser) -> BoletimRead:
    if user.role in (Role.RESPONSAVEL, Role.ALUNO):
        pessoas_service.ensure_can_access_aluno(db, user, aluno_id)
    else:
        pessoas_service.get_aluno_read(db, aluno_id)  # 404 se não existir

    notas = repository.list_notas_aluno(db, aluno_id)
    notas_por_disciplina: dict[str, list[Nota]] = {}
    for nota in notas:
        notas_por_disciplina.setdefault(nota.disciplina, []).append(nota)

    disciplinas: list[BoletimDisciplina] = []
    for disciplina, lista in notas_por_disciplina.items():
        valores = [float(n.valor) for n in lista]
        media = round(sum(valores) / len(valores), 1) if valores else None
        disciplinas.append(
            BoletimDisciplina(
                disciplina=disciplina,
                notas=[
                    NotaPeriodo(periodo=n.periodo, valor=float(n.valor), observacao=n.observacao)
                    for n in sorted(lista, key=lambda n: n.periodo)
                ],
                media=media,
                situacao=_situacao(media),
            )
        )
    disciplinas.sort(key=lambda d: d.disciplina)
    return BoletimRead(aluno_id=aluno_id, disciplinas=disciplinas)


def list_disciplinas() -> list[str]:
    return DISCIPLINAS
