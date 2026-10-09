"""Regras de negócio de pessoas: alunos, responsáveis (vínculo N:N), professores, funcionários.

Invariantes garantidas aqui:
- Todo aluno tem pelo menos 1 responsável e exatamente 1 responsável financeiro.
- Um RESPONSAVEL só enxerga alunos aos quais está vinculado (`ensure_can_access_aluno`).
- CPF é único entre registros ativos de cada tipo.
"""

from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.core.roles import Role
from app.modules.auth import service as auth_service
from app.modules.pessoas import permissions, repository
from app.modules.pessoas.models import Aluno, Funcionario, Professor, Responsavel, ResponsavelAluno
from app.modules.pessoas.schemas import (
    AcessoCreate,
    AlunoCreate,
    AlunoDados,
    AlunoListItem,
    AlunoRead,
    AlunoUpdate,
    FuncionarioCreate,
    FuncionarioListItem,
    FuncionarioRead,
    FuncionarioUpdate,
    Parentesco,
    ProfessorCreate,
    ProfessorListItem,
    ProfessorRead,
    ProfessorUpdate,
    ResponsavelCreate,
    ResponsavelDados,
    ResponsavelListItem,
    ResponsavelRead,
    ResponsavelRegistro,
    ResponsavelUpdate,
    VinculoCreate,
    VinculoRead,
    VinculoUpdate,
)
from app.shared import clock
from app.shared.pagination import Page

ALUNO_NAO_ENCONTRADO = "Aluno não encontrado."


def _aluno_read(aluno: Aluno) -> AlunoRead:
    vinculos = sorted(
        aluno.vinculos, key=lambda v: (not v.responsavel_financeiro, v.responsavel_id)
    )
    return AlunoRead(
        id=aluno.id,
        user_id=aluno.user_id,
        nome=aluno.nome,
        data_nascimento=aluno.data_nascimento,
        cpf=aluno.cpf,
        responsaveis=[
            VinculoRead(
                responsavel_id=v.responsavel_id,
                nome=v.responsavel.nome,
                parentesco=v.parentesco,
                responsavel_financeiro=v.responsavel_financeiro,
                pode_buscar=v.pode_buscar,
            )
            for v in vinculos
        ],
    )


def _get_aluno_or_404(db: Session, aluno_id: int) -> Aluno:
    aluno = repository.get_aluno(db, aluno_id)
    if aluno is None:
        raise NotFoundError(ALUNO_NAO_ENCONTRADO)
    return aluno


# --- Propriedade (anti-IDOR) -------------------------------------------------------------


def list_aluno_ids_do_usuario(
    db: Session, user: CurrentUser, *, include_deleted: bool = False
) -> list[int]:
    """IDs dos alunos vinculados ao usuário RESPONSAVEL (lista vazia se não for responsável).

    `include_deleted=True` inclui alunos com cadastro cancelado (ex.: pré-matrícula rejeitada),
    para a família ainda conseguir ver o histórico e o motivo.
    """
    if user.role != Role.RESPONSAVEL:
        return []
    responsavel = repository.get_responsavel_by_user_id(db, user.id)
    if responsavel is None:
        return []
    return repository.list_aluno_ids_do_responsavel(
        db, responsavel.id, include_deleted=include_deleted
    )


def ensure_can_access_aluno(
    db: Session, user: CurrentUser, aluno_id: int, *, include_deleted: bool = False
) -> None:
    """Equipe acessa qualquer aluno; RESPONSAVEL só os vinculados (senão 404); demais, 403.

    Não faz commit. Use em TODO service que recebe um `aluno_id` em nome de um usuário.
    """
    if permissions.sees_any_aluno(user.role):
        if repository.get_aluno(db, aluno_id, include_deleted=include_deleted) is None:
            raise NotFoundError(ALUNO_NAO_ENCONTRADO)
        return
    if user.role == Role.RESPONSAVEL:
        ids = list_aluno_ids_do_usuario(db, user, include_deleted=include_deleted)
        if aluno_id not in ids:
            raise NotFoundError(ALUNO_NAO_ENCONTRADO)
        return
    if user.role == Role.ALUNO:
        aluno = repository.get_aluno_by_user_id(db, user.id)
        if aluno is None or aluno.id != aluno_id:
            raise NotFoundError(ALUNO_NAO_ENCONTRADO)
        return
    raise ForbiddenError()


# --- Alunos: casos de uso ----------------------------------------------------------------


def list_alunos(db: Session, *, busca: str | None, limit: int, offset: int) -> Page[AlunoListItem]:
    rows, total = repository.list_alunos(db, busca=busca, limit=limit, offset=offset)
    return Page[AlunoListItem](
        items=[AlunoListItem.model_validate(a) for a in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_aluno(db: Session, aluno_id: int, user: CurrentUser) -> AlunoRead:
    ensure_can_access_aluno(db, user, aluno_id)
    return _aluno_read(_get_aluno_or_404(db, aluno_id))


def create_aluno(db: Session, data: AlunoCreate) -> AlunoRead:
    aluno = create_aluno_record(db, data)
    for vinculo in data.responsaveis:
        if repository.get_responsavel(db, vinculo.responsavel_id) is None:
            raise NotFoundError(f"Responsável {vinculo.responsavel_id} não encontrado.")
        link_responsavel_record(
            db,
            aluno_id=aluno.id,
            responsavel_id=vinculo.responsavel_id,
            parentesco=vinculo.parentesco,
            responsavel_financeiro=vinculo.responsavel_financeiro,
            pode_buscar=vinculo.pode_buscar,
        )
    db.commit()
    return get_aluno_read(db, aluno.id)


def update_aluno(db: Session, aluno_id: int, data: AlunoUpdate) -> AlunoRead:
    aluno = _get_aluno_or_404(db, aluno_id)
    if data.cpf and data.cpf != aluno.cpf:
        _ensure_aluno_cpf_free(db, data.cpf)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(aluno, field, value)
    db.commit()
    return _aluno_read(aluno)


def delete_aluno(db: Session, aluno_id: int) -> None:
    soft_delete_aluno_record(db, aluno_id)
    db.commit()


def add_vinculo(db: Session, aluno_id: int, data: VinculoCreate) -> AlunoRead:
    _get_aluno_or_404(db, aluno_id)
    if repository.get_responsavel(db, data.responsavel_id) is None:
        raise NotFoundError("Responsável não encontrado.")
    if repository.get_vinculo(db, aluno_id, data.responsavel_id) is not None:
        raise ConflictError("Este responsável já está vinculado ao aluno.", "VINCULO_EXISTENTE")
    link_responsavel_record(
        db,
        aluno_id=aluno_id,
        responsavel_id=data.responsavel_id,
        parentesco=data.parentesco,
        responsavel_financeiro=data.responsavel_financeiro,
        pode_buscar=data.pode_buscar,
    )
    _ensure_has_financeiro(db, aluno_id)
    db.commit()
    return get_aluno_read(db, aluno_id)


def update_vinculo(
    db: Session, aluno_id: int, responsavel_id: int, data: VinculoUpdate
) -> AlunoRead:
    vinculo = repository.get_vinculo(db, aluno_id, responsavel_id)
    if vinculo is None:
        raise NotFoundError("Vínculo não encontrado.")
    if data.parentesco is not None:
        vinculo.parentesco = data.parentesco
    if data.pode_buscar is not None:
        vinculo.pode_buscar = data.pode_buscar
    if data.responsavel_financeiro:
        _set_financeiro(db, aluno_id, responsavel_id)
    db.commit()
    return get_aluno_read(db, aluno_id)


def remove_vinculo(db: Session, aluno_id: int, responsavel_id: int) -> AlunoRead:
    vinculo = repository.get_vinculo(db, aluno_id, responsavel_id)
    if vinculo is None:
        raise NotFoundError("Vínculo não encontrado.")
    if len(repository.list_vinculos_do_aluno(db, aluno_id)) == 1:
        raise BusinessRuleError(
            "O aluno precisa ter pelo menos um responsável.", "ALUNO_SEM_RESPONSAVEL"
        )
    if vinculo.responsavel_financeiro:
        raise BusinessRuleError(
            "Transfira a responsabilidade financeira antes de remover este responsável.",
            "TRANSFERIR_FINANCEIRO",
        )
    repository.delete_vinculo(db, vinculo)
    db.commit()
    return get_aluno_read(db, aluno_id)


# --- Alunos: API pública para outros módulos (sem commit) ---------------------------------


def get_aluno_read(db: Session, aluno_id: int, *, include_deleted: bool = False) -> AlunoRead:
    aluno = repository.get_aluno(db, aluno_id, include_deleted=include_deleted)
    if aluno is None:
        raise NotFoundError(ALUNO_NAO_ENCONTRADO)
    db.refresh(aluno, ["vinculos"])
    return _aluno_read(aluno)


def list_alunos_reads(
    db: Session, aluno_ids: list[int], *, include_deleted: bool = False
) -> list[AlunoRead]:
    alunos = repository.list_alunos_by_ids(db, aluno_ids, include_deleted=include_deleted)
    return [_aluno_read(a) for a in alunos]


def list_meus_alunos(db: Session, user: CurrentUser) -> list[AlunoRead]:
    """Alunos vinculados ao RESPONSAVEL logado (inclui cadastros cancelados, p/ histórico)."""
    aluno_ids = list_aluno_ids_do_usuario(db, user, include_deleted=True)
    return list_alunos_reads(db, aluno_ids, include_deleted=True)


def find_aluno_by_cpf(db: Session, cpf: str) -> AlunoRead | None:
    aluno = repository.get_aluno_by_cpf(db, cpf)
    return get_aluno_read(db, aluno.id) if aluno else None


def get_aluno_by_user(db: Session, user_id: int) -> AlunoRead | None:
    """API pública: aluno ligado a uma conta de usuário (ou None)."""
    aluno = repository.get_aluno_by_user_id(db, user_id)
    return _aluno_read(aluno) if aluno else None


def grant_aluno_acesso(db: Session, aluno_id: int, data: AcessoCreate) -> AlunoRead:
    aluno = _get_aluno_or_404(db, aluno_id)
    if aluno.user_id is not None:
        raise ConflictError("Este aluno já possui acesso.", "ACESSO_EXISTENTE")
    user = auth_service.create_user_account(
        db, email=data.email, nome=aluno.nome, password=data.password, role=Role.ALUNO
    )
    aluno.user_id = user.id
    db.commit()
    return _aluno_read(aluno)


def _ensure_aluno_cpf_free(db: Session, cpf: str) -> None:
    if repository.get_aluno_by_cpf(db, cpf) is not None:
        raise ConflictError("Já existe um aluno com este CPF.", "ALUNO_JA_CADASTRADO")


def create_aluno_record(db: Session, dados: AlunoDados) -> AlunoRead:
    """Cria o aluno (sem vínculos). Não faz commit: participa da transação de quem chamou."""
    if dados.cpf:
        _ensure_aluno_cpf_free(db, dados.cpf)
    aluno = Aluno(nome=dados.nome, data_nascimento=dados.data_nascimento, cpf=dados.cpf)
    repository.add(db, aluno)
    return AlunoRead(
        id=aluno.id, nome=aluno.nome, data_nascimento=aluno.data_nascimento, cpf=aluno.cpf
    )


def update_aluno_record(db: Session, aluno_id: int, dados: AlunoDados) -> AlunoRead:
    """Atualiza os dados do aluno (rematrícula). Não faz commit."""
    aluno = _get_aluno_or_404(db, aluno_id)
    if dados.cpf and dados.cpf != aluno.cpf:
        _ensure_aluno_cpf_free(db, dados.cpf)
        aluno.cpf = dados.cpf
    aluno.nome = dados.nome
    aluno.data_nascimento = dados.data_nascimento
    db.flush()
    return _aluno_read(aluno)


def soft_delete_aluno_record(db: Session, aluno_id: int) -> None:
    """Exclusão lógica (o histórico é preservado). Não faz commit."""
    aluno = _get_aluno_or_404(db, aluno_id)
    aluno.deleted_at = clock.now()
    db.flush()


# --- Vínculos: API pública (sem commit) ----------------------------------------------------


def link_responsavel_record(
    db: Session,
    *,
    aluno_id: int,
    responsavel_id: int,
    parentesco: Parentesco,
    responsavel_financeiro: bool,
    pode_buscar: bool,
) -> None:
    """Cria (ou atualiza) o vínculo. Se for financeiro, tira o papel de quem tinha antes.

    Não faz commit: participa da transação de quem chamou.
    """
    vinculo = repository.get_vinculo(db, aluno_id, responsavel_id)
    if vinculo is None:
        vinculo = ResponsavelAluno(
            aluno_id=aluno_id,
            responsavel_id=responsavel_id,
            parentesco=parentesco,
            responsavel_financeiro=False,
            pode_buscar=pode_buscar,
        )
        repository.add(db, vinculo)
    else:
        vinculo.parentesco = parentesco
        vinculo.pode_buscar = pode_buscar
    if responsavel_financeiro:
        _set_financeiro(db, aluno_id, responsavel_id)
    db.flush()


def _set_financeiro(db: Session, aluno_id: int, responsavel_id: int) -> None:
    vinculos = repository.list_vinculos_do_aluno(db, aluno_id)
    # Primeiro desmarca o atual e grava (o índice único parcial não aceita dois ao mesmo tempo).
    for v in vinculos:
        if v.responsavel_financeiro and v.responsavel_id != responsavel_id:
            v.responsavel_financeiro = False
    db.flush()
    for v in vinculos:
        if v.responsavel_id == responsavel_id:
            v.responsavel_financeiro = True
    db.flush()


def _ensure_has_financeiro(db: Session, aluno_id: int) -> None:
    if not any(v.responsavel_financeiro for v in repository.list_vinculos_do_aluno(db, aluno_id)):
        raise BusinessRuleError(
            "O aluno precisa ter exatamente um responsável financeiro.", "SEM_FINANCEIRO"
        )


def get_responsavel_financeiro(db: Session, aluno_id: int) -> ResponsavelRead | None:
    for v in repository.list_vinculos_do_aluno(db, aluno_id):
        if v.responsavel_financeiro:
            return ResponsavelRead.model_validate(v.responsavel)
    return None


def is_responsavel_do_aluno(db: Session, responsavel_id: int, aluno_id: int) -> bool:
    return repository.get_vinculo(db, aluno_id, responsavel_id) is not None


# --- Responsáveis ------------------------------------------------------------------------


def _get_responsavel_or_404(db: Session, responsavel_id: int) -> Responsavel:
    responsavel = repository.get_responsavel(db, responsavel_id)
    if responsavel is None:
        raise NotFoundError("Responsável não encontrado.")
    return responsavel


def list_responsaveis(
    db: Session, *, busca: str | None, limit: int, offset: int
) -> Page[ResponsavelListItem]:
    rows, total = repository.list_responsaveis(db, busca=busca, limit=limit, offset=offset)
    return Page[ResponsavelListItem](
        items=[ResponsavelListItem.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_responsavel(db: Session, responsavel_id: int) -> ResponsavelRead:
    return ResponsavelRead.model_validate(_get_responsavel_or_404(db, responsavel_id))


def create_responsavel(db: Session, data: ResponsavelCreate) -> ResponsavelRead:
    responsavel = create_responsavel_record(db, data)
    if data.acesso:
        _grant_responsavel_acesso(db, responsavel.id, data.nome, data.acesso)
    db.commit()
    return get_responsavel(db, responsavel.id)


def register_responsavel(db: Session, data: ResponsavelRegistro) -> ResponsavelRead:
    """Cadastro público. O perfil é sempre RESPONSAVEL e um CPF já existente NÃO é assumido
    (senão qualquer pessoa que soubesse o CPF ganharia acesso aos filhos de outra família)."""
    if repository.get_responsavel_by_cpf(db, data.cpf) is not None:
        raise ConflictError(
            "Este CPF já está cadastrado. Procure a secretaria para liberar seu acesso.",
            "CPF_JA_CADASTRADO",
        )
    user = auth_service.create_user_account(
        db, email=data.email, nome=data.nome, password=data.password, role=Role.RESPONSAVEL
    )
    responsavel = Responsavel(
        user_id=user.id, nome=data.nome, cpf=data.cpf, email=data.email, telefone=data.telefone
    )
    repository.add(db, responsavel)
    db.commit()
    return ResponsavelRead.model_validate(responsavel)


def grant_responsavel_acesso(
    db: Session, responsavel_id: int, data: AcessoCreate
) -> ResponsavelRead:
    responsavel = _get_responsavel_or_404(db, responsavel_id)
    _grant_responsavel_acesso(db, responsavel_id, responsavel.nome, data)
    db.commit()
    return ResponsavelRead.model_validate(responsavel)


def _grant_responsavel_acesso(
    db: Session, responsavel_id: int, nome: str, acesso: AcessoCreate
) -> None:
    responsavel = _get_responsavel_or_404(db, responsavel_id)
    if responsavel.user_id is not None:
        raise ConflictError("Este responsável já possui acesso.", "ACESSO_EXISTENTE")
    user = auth_service.create_user_account(
        db, email=acesso.email, nome=nome, password=acesso.password, role=Role.RESPONSAVEL
    )
    responsavel.user_id = user.id
    db.flush()


def update_responsavel(
    db: Session, responsavel_id: int, data: ResponsavelUpdate
) -> ResponsavelRead:
    responsavel = _get_responsavel_or_404(db, responsavel_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(responsavel, field, value)
    db.commit()
    return ResponsavelRead.model_validate(responsavel)


# --- Responsáveis: API pública (sem commit) ------------------------------------------------


def get_responsavel_by_user(db: Session, user_id: int) -> ResponsavelRead | None:
    responsavel = repository.get_responsavel_by_user_id(db, user_id)
    return ResponsavelRead.model_validate(responsavel) if responsavel else None


def find_responsavel_by_cpf(db: Session, cpf: str) -> ResponsavelRead | None:
    responsavel = repository.get_responsavel_by_cpf(db, cpf)
    return ResponsavelRead.model_validate(responsavel) if responsavel else None


def list_responsaveis_reads(db: Session, ids: list[int]) -> list[ResponsavelRead]:
    return [ResponsavelRead.model_validate(r) for r in repository.list_responsaveis_by_ids(db, ids)]


def create_responsavel_record(db: Session, dados: ResponsavelDados) -> ResponsavelRead:
    """Cria um responsável novo; CPF já cadastrado → 409. Não faz commit."""
    if repository.get_responsavel_by_cpf(db, dados.cpf) is not None:
        raise ConflictError("Já existe um responsável com este CPF.", "RESPONSAVEL_JA_CADASTRADO")
    responsavel = Responsavel(
        nome=dados.nome, cpf=dados.cpf, email=dados.email, telefone=dados.telefone
    )
    repository.add(db, responsavel)
    return ResponsavelRead.model_validate(responsavel)


def upsert_responsavel_record(db: Session, dados: ResponsavelDados) -> ResponsavelRead:
    """Atualiza o responsável com este CPF ou cria um novo. Uso exclusivo da EQUIPE
    (secretaria), nunca em nome de um responsável. Não faz commit."""
    existing = repository.get_responsavel_by_cpf(db, dados.cpf)
    if existing is None:
        return create_responsavel_record(db, dados)
    existing.nome = dados.nome
    if dados.email:
        existing.email = dados.email
    if dados.telefone:
        existing.telefone = dados.telefone
    db.flush()
    return ResponsavelRead.model_validate(existing)


# --- Professores -------------------------------------------------------------------------


def _get_professor_or_404(db: Session, professor_id: int) -> Professor:
    professor = repository.get_professor(db, professor_id)
    if professor is None:
        raise NotFoundError("Professor não encontrado.")
    return professor


def list_professores(
    db: Session, *, busca: str | None, limit: int, offset: int
) -> Page[ProfessorListItem]:
    rows, total = repository.list_professores(db, busca=busca, limit=limit, offset=offset)
    return Page[ProfessorListItem](
        items=[ProfessorListItem.model_validate(p) for p in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_professor(db: Session, professor_id: int) -> ProfessorRead:
    return ProfessorRead.model_validate(_get_professor_or_404(db, professor_id))


def create_professor(db: Session, data: ProfessorCreate) -> ProfessorRead:
    if repository.get_professor_by_cpf(db, data.cpf) is not None:
        raise ConflictError("Já existe um professor com este CPF.", "PROFESSOR_JA_CADASTRADO")
    professor = Professor(**data.model_dump(exclude={"acesso"}))
    if data.acesso:
        user = auth_service.create_user_account(
            db,
            email=data.acesso.email,
            nome=data.nome,
            password=data.acesso.password,
            role=Role.PROFESSOR,
        )
        professor.user_id = user.id
    repository.add(db, professor)
    db.commit()
    return ProfessorRead.model_validate(professor)


def update_professor(db: Session, professor_id: int, data: ProfessorUpdate) -> ProfessorRead:
    professor = _get_professor_or_404(db, professor_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(professor, field, value)
    db.commit()
    return ProfessorRead.model_validate(professor)


def delete_professor(db: Session, professor_id: int) -> None:
    professor = _get_professor_or_404(db, professor_id)
    professor.deleted_at = clock.now()
    db.commit()


def get_professor_by_user(db: Session, user_id: int) -> ProfessorRead | None:
    """API pública: professor ligado a uma conta de usuário (ou None)."""
    professor = repository.get_professor_by_user_id(db, user_id)
    return ProfessorRead.model_validate(professor) if professor else None


def list_professores_reads(db: Session, ids: list[int]) -> list[ProfessorRead]:
    return [ProfessorRead.model_validate(p) for p in repository.list_professores_by_ids(db, ids)]


# --- Funcionários ------------------------------------------------------------------------


def _get_funcionario_or_404(db: Session, funcionario_id: int) -> Funcionario:
    funcionario = repository.get_funcionario(db, funcionario_id)
    if funcionario is None:
        raise NotFoundError("Funcionário não encontrado.")
    return funcionario


def list_funcionarios(
    db: Session, *, busca: str | None, limit: int, offset: int
) -> Page[FuncionarioListItem]:
    rows, total = repository.list_funcionarios(db, busca=busca, limit=limit, offset=offset)
    return Page[FuncionarioListItem](
        items=[FuncionarioListItem.model_validate(f) for f in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_funcionario(db: Session, funcionario_id: int) -> FuncionarioRead:
    return FuncionarioRead.model_validate(_get_funcionario_or_404(db, funcionario_id))


def create_funcionario(db: Session, data: FuncionarioCreate) -> FuncionarioRead:
    if repository.get_funcionario_by_cpf(db, data.cpf) is not None:
        raise ConflictError("Já existe um funcionário com este CPF.", "FUNCIONARIO_JA_CADASTRADO")
    funcionario = Funcionario(**data.model_dump(exclude={"acesso"}))
    if data.acesso:
        user = auth_service.create_user_account(
            db,
            email=data.acesso.email,
            nome=data.nome,
            password=data.acesso.password,
            role=data.acesso.role,
        )
        funcionario.user_id = user.id
    repository.add(db, funcionario)
    db.commit()
    return FuncionarioRead.model_validate(funcionario)


def update_funcionario(
    db: Session, funcionario_id: int, data: FuncionarioUpdate
) -> FuncionarioRead:
    funcionario = _get_funcionario_or_404(db, funcionario_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(funcionario, field, value)
    db.commit()
    return FuncionarioRead.model_validate(funcionario)


def delete_funcionario(db: Session, funcionario_id: int) -> None:
    funcionario = _get_funcionario_or_404(db, funcionario_id)
    funcionario.deleted_at = clock.now()
    db.commit()
