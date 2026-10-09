"""Regras do mural de avisos: visibilidade por perfil e controle de leitura."""

from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.roles import Role
from app.modules.comunicacao import repository
from app.modules.comunicacao.models import Aviso
from app.modules.comunicacao.schemas import (
    AvisoCreate,
    AvisoRead,
    AvisoUpdate,
    NaoLidosTotal,
    PublicoAlvo,
)
from app.modules.pessoas import service as pessoas_service
from app.modules.turmas import service as turmas_service
from app.shared.pagination import Page

AVISO_NAO_ENCONTRADO = "Aviso não encontrado."


def _ve_tudo(user: CurrentUser) -> bool:
    return user.is_staff


def _publicos_visiveis(user: CurrentUser) -> list[PublicoAlvo]:
    if user.role == Role.PROFESSOR:
        return [PublicoAlvo.TODOS, PublicoAlvo.PROFESSORES]
    if user.role == Role.RESPONSAVEL:
        return [PublicoAlvo.TODOS, PublicoAlvo.RESPONSAVEIS]
    if user.role == Role.ALUNO:
        return [PublicoAlvo.TODOS]
    return [PublicoAlvo.TODOS]


def _turma_ids_visiveis(db: Session, user: CurrentUser) -> list[int]:
    """Turmas cujos avisos TURMA o usuário pode ver.

    PROFESSOR: turmas em que leciona.
    RESPONSAVEL: simplificação — não filtramos pelas turmas dos filhos (ver nota no
    relatório da tarefa); o responsável só vê TODOS e RESPONSAVEIS, então aqui retorna [].
    """
    if user.role == Role.PROFESSOR:
        professor = pessoas_service.get_professor_by_user(db, user.id)
        if professor is None:
            return []
        return [t.id for t in turmas_service.list_minhas_turmas(db, user)]
    return []


def _to_read(aviso: Aviso, *, lido: bool) -> AvisoRead:
    read = AvisoRead.model_validate(aviso)
    read.lido = lido
    return read


def _get_or_404(db: Session, aviso_id: int) -> Aviso:
    aviso = repository.get_aviso(db, aviso_id)
    if aviso is None:
        raise NotFoundError(AVISO_NAO_ENCONTRADO)
    return aviso


def _pode_editar(user: CurrentUser, aviso: Aviso) -> bool:
    if user.role in (Role.ADMIN, Role.SECRETARIA):
        return True
    return aviso.publicado_por_user_id == user.id


# --- Casos de uso ------------------------------------------------------------------------


def list_avisos(db: Session, user: CurrentUser, *, limit: int, offset: int) -> Page[AvisoRead]:
    ve_tudo = _ve_tudo(user)
    publicos = _publicos_visiveis(user)
    turma_ids = _turma_ids_visiveis(db, user)
    avisos, total = repository.list_avisos_visiveis(
        db, ve_tudo=ve_tudo, publicos=publicos, turma_ids=turma_ids, limit=limit, offset=offset
    )
    lidos = repository.list_leituras(db, [a.id for a in avisos], user.id)
    items = [_to_read(a, lido=a.id in lidos) for a in avisos]
    return Page[AvisoRead](items=items, total=total, limit=limit, offset=offset)


def contar_nao_lidos(db: Session, user: CurrentUser) -> NaoLidosTotal:
    ve_tudo = _ve_tudo(user)
    publicos = _publicos_visiveis(user)
    turma_ids = _turma_ids_visiveis(db, user)
    total = repository.list_ids_visiveis_sem_leitura(
        db, user_id=user.id, ve_tudo=ve_tudo, publicos=publicos, turma_ids=turma_ids
    )
    return NaoLidosTotal(total=total)


def create_aviso(db: Session, data: AvisoCreate, user: CurrentUser) -> AvisoRead:
    if user.role == Role.PROFESSOR:
        if data.publico_alvo != PublicoAlvo.TURMA or data.turma_id is None:
            raise ForbiddenError(
                "Professores só podem publicar avisos para a própria turma."
            )
        if not turmas_service.is_professor_da_turma(db, data.turma_id, user.id):
            raise ForbiddenError("Você não leciona nesta turma.")
    aviso = Aviso(
        titulo=data.titulo,
        corpo=data.corpo,
        publico_alvo=data.publico_alvo,
        turma_id=data.turma_id,
        fixado=data.fixado,
        publicado_por_user_id=user.id,
    )
    repository.add(db, aviso)
    db.commit()
    return _to_read(aviso, lido=False)


def update_aviso(db: Session, aviso_id: int, data: AvisoUpdate, user: CurrentUser) -> AvisoRead:
    aviso = _get_or_404(db, aviso_id)
    if not _pode_editar(user, aviso):
        raise ForbiddenError()
    changes = data.model_dump(exclude_unset=True)
    novo_publico = changes.get("publico_alvo", aviso.publico_alvo)
    novo_turma_id = changes.get("turma_id", aviso.turma_id)
    if novo_publico == PublicoAlvo.TURMA and novo_turma_id is None:
        raise ForbiddenError("turma_id é obrigatório quando publico_alvo é TURMA.")
    for field, value in changes.items():
        setattr(aviso, field, value)
    db.commit()
    leu = aviso_id in repository.list_leituras(db, [aviso_id], user.id)
    return _to_read(aviso, lido=leu)


def delete_aviso(db: Session, aviso_id: int, user: CurrentUser) -> None:
    aviso = _get_or_404(db, aviso_id)
    if not _pode_editar(user, aviso):
        raise ForbiddenError()
    repository.delete(db, aviso)
    db.commit()


def marcar_lido(db: Session, aviso_id: int, user: CurrentUser) -> None:
    _get_or_404(db, aviso_id)
    repository.marcar_lido(db, aviso_id, user.id)
    db.commit()
