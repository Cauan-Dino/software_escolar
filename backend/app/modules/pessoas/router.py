from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, get_client_ip, require_roles
from app.core.rate_limit import RateLimiter
from app.modules.pessoas import permissions, service
from app.modules.pessoas.schemas import (
    AcessoCreate,
    AlunoCreate,
    AlunoListItem,
    AlunoRead,
    AlunoUpdate,
    FuncionarioCreate,
    FuncionarioListItem,
    FuncionarioRead,
    FuncionarioUpdate,
    ProfessorCreate,
    ProfessorListItem,
    ProfessorRead,
    ProfessorUpdate,
    ResponsavelCreate,
    ResponsavelListItem,
    ResponsavelRead,
    ResponsavelRegistro,
    ResponsavelUpdate,
    VinculoCreate,
    VinculoUpdate,
)
from app.shared.pagination import Page, Pagination

router = APIRouter(prefix="/api/v1/pessoas", tags=["pessoas"])

Busca = Annotated[str | None, Query(max_length=100, description="Parte do nome ou CPF completo")]
register_limiter = RateLimiter("registro", settings.register_rate_limit_per_minute)


def _register_rate_limit(request: Request) -> None:
    register_limiter.hit(get_client_ip(request))


# --- Alunos ------------------------------------------------------------------------------


@router.get("/alunos", response_model=Page[AlunoListItem])
def list_alunos(
    db: DbSession,
    page: Pagination,
    busca: Busca = None,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_LIST_ALUNOS)),
) -> Page[AlunoListItem]:
    return service.list_alunos(db, busca=busca, limit=page.limit, offset=page.offset)


@router.post("/alunos", response_model=AlunoRead, status_code=status.HTTP_201_CREATED)
def create_aluno(
    payload: AlunoCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_ALUNOS)),
) -> AlunoRead:
    return service.create_aluno(db, payload)


@router.get("/alunos/{aluno_id}", response_model=AlunoRead)
def get_aluno(
    aluno_id: int,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_VIEW_ALUNO)),
) -> AlunoRead:
    return service.get_aluno(db, aluno_id, user)


@router.patch("/alunos/{aluno_id}", response_model=AlunoRead)
def update_aluno(
    aluno_id: int,
    payload: AlunoUpdate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_ALUNOS)),
) -> AlunoRead:
    return service.update_aluno(db, aluno_id, payload)


@router.delete("/alunos/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aluno(
    aluno_id: int,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_DELETE_ALUNO)),
) -> Response:
    service.delete_aluno(db, aluno_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/alunos/{aluno_id}/responsaveis", response_model=AlunoRead)
def add_vinculo(
    aluno_id: int,
    payload: VinculoCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_ALUNOS)),
) -> AlunoRead:
    return service.add_vinculo(db, aluno_id, payload)


@router.patch("/alunos/{aluno_id}/responsaveis/{responsavel_id}", response_model=AlunoRead)
def update_vinculo(
    aluno_id: int,
    responsavel_id: int,
    payload: VinculoUpdate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_ALUNOS)),
) -> AlunoRead:
    return service.update_vinculo(db, aluno_id, responsavel_id, payload)


@router.delete("/alunos/{aluno_id}/responsaveis/{responsavel_id}", response_model=AlunoRead)
def remove_vinculo(
    aluno_id: int,
    responsavel_id: int,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_ALUNOS)),
) -> AlunoRead:
    return service.remove_vinculo(db, aluno_id, responsavel_id)


# --- Responsáveis ------------------------------------------------------------------------


@router.post(
    "/responsaveis/registro",
    response_model=ResponsavelRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_register_rate_limit)],
    summary="Cadastro público de responsável (perfil sempre RESPONSAVEL)",
)
def register_responsavel(payload: ResponsavelRegistro, db: DbSession) -> ResponsavelRead:
    return service.register_responsavel(db, payload)


@router.get("/responsaveis", response_model=Page[ResponsavelListItem])
def list_responsaveis(
    db: DbSession,
    page: Pagination,
    busca: Busca = None,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_READ_RESPONSAVEIS)),
) -> Page[ResponsavelListItem]:
    return service.list_responsaveis(db, busca=busca, limit=page.limit, offset=page.offset)


@router.post("/responsaveis", response_model=ResponsavelRead, status_code=status.HTTP_201_CREATED)
def create_responsavel(
    payload: ResponsavelCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_RESPONSAVEIS)),
) -> ResponsavelRead:
    return service.create_responsavel(db, payload)


@router.get("/responsaveis/{responsavel_id}", response_model=ResponsavelRead)
def get_responsavel(
    responsavel_id: int,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_READ_RESPONSAVEIS)),
) -> ResponsavelRead:
    return service.get_responsavel(db, responsavel_id)


@router.patch("/responsaveis/{responsavel_id}", response_model=ResponsavelRead)
def update_responsavel(
    responsavel_id: int,
    payload: ResponsavelUpdate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_RESPONSAVEIS)),
) -> ResponsavelRead:
    return service.update_responsavel(db, responsavel_id, payload)


@router.post("/responsaveis/{responsavel_id}/acesso", response_model=ResponsavelRead)
def grant_acesso(
    responsavel_id: int,
    payload: AcessoCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_RESPONSAVEIS)),
) -> ResponsavelRead:
    return service.grant_responsavel_acesso(db, responsavel_id, payload)


# --- Professores -------------------------------------------------------------------------


@router.get("/professores", response_model=Page[ProfessorListItem])
def list_professores(
    db: DbSession,
    page: Pagination,
    busca: Busca = None,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_READ_PROFESSORES)),
) -> Page[ProfessorListItem]:
    return service.list_professores(db, busca=busca, limit=page.limit, offset=page.offset)


@router.post("/professores", response_model=ProfessorRead, status_code=status.HTTP_201_CREATED)
def create_professor(
    payload: ProfessorCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_PROFESSORES)),
) -> ProfessorRead:
    return service.create_professor(db, payload)


@router.get("/professores/{professor_id}", response_model=ProfessorRead)
def get_professor(
    professor_id: int,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_READ_PROFESSORES)),
) -> ProfessorRead:
    return service.get_professor(db, professor_id)


@router.patch("/professores/{professor_id}", response_model=ProfessorRead)
def update_professor(
    professor_id: int,
    payload: ProfessorUpdate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_PROFESSORES)),
) -> ProfessorRead:
    return service.update_professor(db, professor_id, payload)


@router.delete("/professores/{professor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professor(
    professor_id: int,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_PROFESSORES)),
) -> Response:
    service.delete_professor(db, professor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Funcionários ------------------------------------------------------------------------


@router.get("/funcionarios", response_model=Page[FuncionarioListItem])
def list_funcionarios(
    db: DbSession,
    page: Pagination,
    busca: Busca = None,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FUNCIONARIOS)),
) -> Page[FuncionarioListItem]:
    return service.list_funcionarios(db, busca=busca, limit=page.limit, offset=page.offset)


@router.post("/funcionarios", response_model=FuncionarioRead, status_code=status.HTTP_201_CREATED)
def create_funcionario(
    payload: FuncionarioCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FUNCIONARIOS)),
) -> FuncionarioRead:
    return service.create_funcionario(db, payload)


@router.get("/funcionarios/{funcionario_id}", response_model=FuncionarioRead)
def get_funcionario(
    funcionario_id: int,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FUNCIONARIOS)),
) -> FuncionarioRead:
    return service.get_funcionario(db, funcionario_id)


@router.patch("/funcionarios/{funcionario_id}", response_model=FuncionarioRead)
def update_funcionario(
    funcionario_id: int,
    payload: FuncionarioUpdate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FUNCIONARIOS)),
) -> FuncionarioRead:
    return service.update_funcionario(db, funcionario_id, payload)


@router.delete("/funcionarios/{funcionario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_funcionario(
    funcionario_id: int,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_FUNCIONARIOS)),
) -> Response:
    service.delete_funcionario(db, funcionario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
