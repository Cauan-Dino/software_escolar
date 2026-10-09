from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, require_roles
from app.modules.matricula import permissions, service
from app.modules.matricula.schemas import (
    AprovarMatricula,
    DocumentoCheck,
    MatriculaRead,
    MotivoInput,
    PreMatriculaCreate,
    StatusMatricula,
    TipoDocumento,
)
from app.shared.pagination import Page, Pagination
from app.shared.serie import Serie

router = APIRouter(prefix="/api/v1/matriculas", tags=["matricula"])


@router.post("", response_model=MatriculaRead, status_code=status.HTTP_201_CREATED)
def create_pre_matricula(
    payload: PreMatriculaCreate,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_CREATE)),
) -> MatriculaRead:
    return service.create_pre_matricula(db, payload, user)


@router.get("", response_model=Page[MatriculaRead])
def list_matriculas(
    db: DbSession,
    page: Pagination,
    status_: Annotated[StatusMatricula | None, Query(alias="status")] = None,
    ano_letivo: Annotated[int | None, Query()] = None,
    serie: Annotated[Serie | None, Query()] = None,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_READ)),
) -> Page[MatriculaRead]:
    return service.list_matriculas(
        db,
        user,
        status=status_,
        ano_letivo=ano_letivo,
        serie=serie,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{matricula_id}", response_model=MatriculaRead)
def get_matricula(
    matricula_id: int,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_READ)),
) -> MatriculaRead:
    return service.get_matricula(db, matricula_id, user)


@router.post("/{matricula_id}/analise", response_model=MatriculaRead)
def start_analise(
    matricula_id: int,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_REVIEW)),
) -> MatriculaRead:
    return service.start_analise(db, matricula_id, user)


@router.post("/{matricula_id}/aprovar", response_model=MatriculaRead)
def approve_matricula(
    matricula_id: int,
    payload: AprovarMatricula,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_REVIEW)),
) -> MatriculaRead:
    return service.approve_matricula(db, matricula_id, payload, user)


@router.post("/{matricula_id}/rejeitar", response_model=MatriculaRead)
def reject_matricula(
    matricula_id: int,
    payload: MotivoInput,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_REVIEW)),
) -> MatriculaRead:
    return service.reject_matricula(db, matricula_id, payload, user)


@router.post("/{matricula_id}/cancelar", response_model=MatriculaRead)
def cancel_matricula(
    matricula_id: int,
    payload: MotivoInput,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_CANCEL)),
) -> MatriculaRead:
    return service.cancel_matricula(db, matricula_id, payload, user)


@router.patch("/{matricula_id}/documentos/{tipo}", response_model=MatriculaRead)
def check_documento(
    matricula_id: int,
    tipo: TipoDocumento,
    payload: DocumentoCheck,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_CHECK_DOCUMENTOS)),
) -> MatriculaRead:
    return service.check_documento(db, matricula_id, tipo, payload, user)


@router.post("/{matricula_id}/documentos/{tipo}/arquivo", response_model=MatriculaRead)
def upload_documento(
    matricula_id: int,
    tipo: TipoDocumento,
    db: DbSession,
    arquivo: UploadFile = File(...),
    user: CurrentUser = Depends(require_roles(*permissions.CAN_UPLOAD_DOCUMENTOS)),
) -> MatriculaRead:
    # Lê no máximo o limite + 1 byte: o service recusa arquivos maiores.
    content = arquivo.file.read(settings.upload_max_bytes + 1)
    return service.upload_documento(
        db,
        matricula_id,
        tipo,
        filename=arquivo.filename or "documento",
        content=content,
        actor=user,
    )


@router.get("/{matricula_id}/documentos/{tipo}/arquivo", response_class=FileResponse)
def download_documento(
    matricula_id: int,
    tipo: TipoDocumento,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_READ)),
) -> FileResponse:
    arquivo = service.get_documento_arquivo(db, matricula_id, tipo, user)
    return FileResponse(arquivo.path, media_type=arquivo.content_type, filename=arquivo.filename)
