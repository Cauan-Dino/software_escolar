from datetime import date

import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.core.roles import Role
from app.modules.auth.models import User
from app.modules.pessoas import service
from app.modules.pessoas.schemas import (
    AcessoCreate,
    AlunoCreate,
    AlunoDados,
    AlunoUpdate,
    FuncionarioAcesso,
    FuncionarioCreate,
    FuncionarioUpdate,
    Parentesco,
    ProfessorCreate,
    ProfessorUpdate,
    ResponsavelCreate,
    ResponsavelDados,
    ResponsavelRegistro,
    ResponsavelUpdate,
    TipoFuncionario,
    VinculoCreate,
    VinculoUpdate,
)
from tests.factories import make_aluno, make_professor, make_responsavel, valid_cpf
from tests.helpers import current_user

NASC = date(2019, 3, 1)


def as_user(responsavel):
    return current_user(Role.RESPONSAVEL, responsavel.user_id)


# --- Propriedade --------------------------------------------------------------------------


def test_responsavel_accesses_only_own_children(db):
    mae = make_responsavel(db)
    outra = make_responsavel(db)
    filho = make_aluno(db, responsaveis=[mae])
    alheio = make_aluno(db, responsaveis=[outra])
    service.ensure_can_access_aluno(db, as_user(mae), filho.id)
    with pytest.raises(NotFoundError):
        service.ensure_can_access_aluno(db, as_user(mae), alheio.id)


def test_staff_accesses_any_aluno_but_professor_does_not(db):
    aluno = make_aluno(db)
    for role in (Role.ADMIN, Role.SECRETARIA, Role.FINANCEIRO):
        service.ensure_can_access_aluno(db, current_user(role), aluno.id)
    with pytest.raises(ForbiddenError):
        service.ensure_can_access_aluno(db, current_user(Role.PROFESSOR), aluno.id)
    with pytest.raises(NotFoundError):
        service.ensure_can_access_aluno(db, current_user(Role.ADMIN), 99_999_999)


def test_responsavel_without_profile_sees_nothing(db):
    aluno = make_aluno(db)
    assert service.list_aluno_ids_do_usuario(db, current_user(Role.RESPONSAVEL, 123)) == []
    with pytest.raises(NotFoundError):
        service.ensure_can_access_aluno(db, current_user(Role.RESPONSAVEL, 123), aluno.id)
    assert service.list_aluno_ids_do_usuario(db, current_user(Role.ADMIN)) == []


def test_responsavel_with_two_children_sees_both(db):
    mae = make_responsavel(db)
    a = make_aluno(db, responsaveis=[mae])
    b = make_aluno(db, responsaveis=[mae])
    assert sorted(service.list_aluno_ids_do_usuario(db, as_user(mae))) == sorted([a.id, b.id])


# --- Alunos -------------------------------------------------------------------------------


def test_create_aluno_with_two_responsaveis(db):
    mae = make_responsavel(db)
    pai = make_responsavel(db)
    data = AlunoCreate(
        nome="Ana Clara",
        data_nascimento=NASC,
        responsaveis=[
            VinculoCreate(
                responsavel_id=mae.id, parentesco=Parentesco.MAE, responsavel_financeiro=True
            ),
            VinculoCreate(responsavel_id=pai.id, parentesco=Parentesco.PAI, pode_buscar=False),
        ],
    )
    aluno = service.create_aluno(db, data)
    assert [r.responsavel_id for r in aluno.responsaveis] == [mae.id, pai.id]
    assert aluno.responsaveis[0].responsavel_financeiro
    assert not aluno.responsaveis[1].pode_buscar


def test_create_aluno_requires_exactly_one_financeiro():
    with pytest.raises(ValueError, match="exatamente 1"):
        AlunoCreate(
            nome="Ana Clara",
            data_nascimento=NASC,
            responsaveis=[
                VinculoCreate(responsavel_id=1, parentesco=Parentesco.MAE),
                VinculoCreate(responsavel_id=2, parentesco=Parentesco.PAI),
            ],
        )
    with pytest.raises(ValueError, match="repetido"):
        AlunoCreate(
            nome="Ana Clara",
            data_nascimento=NASC,
            responsaveis=[
                VinculoCreate(
                    responsavel_id=1, parentesco=Parentesco.MAE, responsavel_financeiro=True
                ),
                VinculoCreate(responsavel_id=1, parentesco=Parentesco.MAE),
            ],
        )


def test_create_aluno_with_unknown_responsavel_fails(db):
    data = AlunoCreate(
        nome="Ana Clara",
        data_nascimento=NASC,
        responsaveis=[
            VinculoCreate(
                responsavel_id=99_999_999, parentesco=Parentesco.MAE, responsavel_financeiro=True
            )
        ],
    )
    with pytest.raises(NotFoundError):
        service.create_aluno(db, data)


def test_aluno_cpf_must_be_unique(db):
    cpf = valid_cpf()
    make_aluno(db, cpf=cpf)
    with pytest.raises(ConflictError):
        service.create_aluno_record(
            db, AlunoDados(nome="Outro Aluno", data_nascimento=NASC, cpf=cpf)
        )


def test_update_aluno_and_cpf_conflict(db):
    aluno = make_aluno(db)
    outro = make_aluno(db, cpf=valid_cpf())
    updated = service.update_aluno(db, aluno.id, AlunoUpdate(nome="Nome Corrigido"))
    assert updated.nome == "Nome Corrigido"
    with pytest.raises(ConflictError):
        service.update_aluno(db, aluno.id, AlunoUpdate(cpf=outro.cpf))


def test_soft_deleted_aluno_disappears_but_is_kept(db):
    aluno = make_aluno(db)
    service.delete_aluno(db, aluno.id)
    with pytest.raises(NotFoundError):
        service.get_aluno(db, aluno.id, current_user(Role.ADMIN))
    assert service.get_aluno_read(db, aluno.id, include_deleted=True).id == aluno.id
    assert aluno.id not in [
        a.id for a in service.list_alunos(db, busca=None, limit=200, offset=0).items
    ]


def test_list_alunos_masks_cpf_and_searches(db):
    cpf = valid_cpf()
    make_aluno(db, nome="Zuleica Busca", cpf=cpf)
    by_name = service.list_alunos(db, busca="zuleica", limit=10, offset=0)
    assert by_name.total == 1
    assert by_name.items[0].cpf == f"***.{cpf[3:6]}.{cpf[6:9]}-**"
    by_cpf = service.list_alunos(db, busca=cpf, limit=10, offset=0)
    assert by_cpf.total == 1


def test_update_aluno_record_and_find_by_cpf(db):
    aluno = make_aluno(db)
    cpf = valid_cpf()
    updated = service.update_aluno_record(
        db, aluno.id, AlunoDados(nome="Nome Novo", data_nascimento=NASC, cpf=cpf)
    )
    assert updated.cpf == cpf
    found = service.find_aluno_by_cpf(db, cpf)
    assert found is not None
    assert found.id == aluno.id
    assert service.find_aluno_by_cpf(db, valid_cpf()) is None


# --- Vínculos -----------------------------------------------------------------------------


def test_transfer_financeiro_keeps_exactly_one(db):
    mae = make_responsavel(db)
    pai = make_responsavel(db)
    aluno = make_aluno(db, responsaveis=[mae, pai])
    result = service.update_vinculo(
        db, aluno.id, pai.id, VinculoUpdate(responsavel_financeiro=True)
    )
    financeiros = [r.responsavel_id for r in result.responsaveis if r.responsavel_financeiro]
    assert financeiros == [pai.id]
    assert service.get_responsavel_financeiro(db, aluno.id).id == pai.id


def test_add_vinculo_and_duplicate(db):
    aluno = make_aluno(db)
    avo = make_responsavel(db)
    result = service.add_vinculo(
        db, aluno.id, VinculoCreate(responsavel_id=avo.id, parentesco=Parentesco.AVO)
    )
    assert avo.id in [r.responsavel_id for r in result.responsaveis]
    assert service.is_responsavel_do_aluno(db, avo.id, aluno.id)
    with pytest.raises(ConflictError):
        service.add_vinculo(
            db, aluno.id, VinculoCreate(responsavel_id=avo.id, parentesco=Parentesco.AVO)
        )
    with pytest.raises(NotFoundError):
        service.add_vinculo(
            db, aluno.id, VinculoCreate(responsavel_id=99_999_999, parentesco=Parentesco.AVO)
        )


def test_cannot_remove_last_or_financeiro_responsavel(db):
    mae = make_responsavel(db)
    aluno = make_aluno(db, responsaveis=[mae])
    with pytest.raises(BusinessRuleError) as last:
        service.remove_vinculo(db, aluno.id, mae.id)
    assert last.value.code == "ALUNO_SEM_RESPONSAVEL"
    pai = make_responsavel(db)
    service.add_vinculo(
        db, aluno.id, VinculoCreate(responsavel_id=pai.id, parentesco=Parentesco.PAI)
    )
    with pytest.raises(BusinessRuleError) as fin:
        service.remove_vinculo(db, aluno.id, mae.id)
    assert fin.value.code == "TRANSFERIR_FINANCEIRO"
    result = service.remove_vinculo(db, aluno.id, pai.id)
    assert [r.responsavel_id for r in result.responsaveis] == [mae.id]
    with pytest.raises(NotFoundError):
        service.remove_vinculo(db, aluno.id, pai.id)


def test_update_vinculo_fields_and_missing(db):
    mae = make_responsavel(db)
    aluno = make_aluno(db, responsaveis=[mae])
    result = service.update_vinculo(
        db, aluno.id, mae.id, VinculoUpdate(parentesco=Parentesco.OUTRO, pode_buscar=False)
    )
    assert result.responsaveis[0].parentesco == Parentesco.OUTRO
    assert result.responsaveis[0].pode_buscar is False
    with pytest.raises(NotFoundError):
        service.update_vinculo(db, aluno.id, 99_999_999, VinculoUpdate(pode_buscar=True))


# --- Responsáveis -------------------------------------------------------------------------


def test_register_responsavel_always_gets_responsavel_role(db):
    data = ResponsavelRegistro(
        nome="Joana Lima",
        cpf=valid_cpf(),
        email="joana@teste.com",
        telefone="79999990000",
        password="Senha1234",
    )
    created = service.register_responsavel(db, data)
    user = db.get(User, created.user_id)
    assert user is not None
    assert user.role == Role.RESPONSAVEL


def test_register_with_existing_cpf_is_refused_to_avoid_account_takeover(db):
    existente = make_responsavel(db, with_user=False)
    data = ResponsavelRegistro(
        nome="Golpista",
        cpf=existente.cpf,
        email="golpe@teste.com",
        telefone="79999990000",
        password="Senha1234",
    )
    with pytest.raises(ConflictError) as exc:
        service.register_responsavel(db, data)
    assert exc.value.code == "CPF_JA_CADASTRADO"


def test_create_responsavel_with_acesso_and_grant_later(db):
    created = service.create_responsavel(
        db,
        ResponsavelCreate(
            nome="Carlos Souza",
            cpf=valid_cpf(),
            acesso=AcessoCreate(email="carlos@teste.com", password="Senha1234"),
        ),
    )
    assert created.user_id is not None
    sem_acesso = service.create_responsavel(
        db, ResponsavelCreate(nome="Rita Alves", cpf=valid_cpf())
    )
    assert sem_acesso.user_id is None
    granted = service.grant_responsavel_acesso(
        db, sem_acesso.id, AcessoCreate(email="rita@teste.com", password="Senha1234")
    )
    assert granted.user_id is not None
    with pytest.raises(ConflictError):
        service.grant_responsavel_acesso(
            db, sem_acesso.id, AcessoCreate(email="rita2@teste.com", password="Senha1234")
        )


def test_responsavel_cpf_unique_and_upsert(db):
    existente = make_responsavel(db)
    dados = ResponsavelDados(nome="Nome Atualizado", cpf=existente.cpf, telefone="79988887777")
    with pytest.raises(ConflictError):
        service.create_responsavel_record(db, dados)
    upserted = service.upsert_responsavel_record(db, dados)
    assert upserted.id == existente.id
    assert upserted.nome == "Nome Atualizado"
    novo = service.upsert_responsavel_record(
        db, ResponsavelDados(nome="Pessoa Nova", cpf=valid_cpf())
    )
    assert novo.id != existente.id


def test_responsavel_lookups(db):
    r = make_responsavel(db)
    assert service.get_responsavel_by_user(db, r.user_id).id == r.id
    assert service.get_responsavel_by_user(db, 99_999_999) is None
    assert service.find_responsavel_by_cpf(db, r.cpf).id == r.id
    assert service.find_responsavel_by_cpf(db, valid_cpf()) is None
    assert [x.id for x in service.list_responsaveis_reads(db, [r.id])] == [r.id]
    assert service.list_responsaveis_reads(db, []) == []
    assert service.list_responsaveis(db, busca=r.nome, limit=10, offset=0).total == 1
    updated = service.update_responsavel(db, r.id, ResponsavelUpdate(telefone="79911112222"))
    assert updated.telefone == "79911112222"
    with pytest.raises(NotFoundError):
        service.get_responsavel(db, 99_999_999)


def test_list_alunos_reads(db):
    a = make_aluno(db)
    assert [x.id for x in service.list_alunos_reads(db, [a.id])] == [a.id]
    assert service.list_alunos_reads(db, []) == []


# --- Professores e funcionários -----------------------------------------------------------


def test_professor_crud_with_acesso(db):
    created = service.create_professor(
        db,
        ProfessorCreate(
            nome="Prof Marta",
            cpf=valid_cpf(),
            formacao="Pedagogia",
            acesso=AcessoCreate(email="marta@escola.com", password="Senha1234"),
        ),
    )
    user = db.get(User, created.user_id)
    assert user is not None
    assert user.role == Role.PROFESSOR
    assert service.get_professor_by_user(db, created.user_id).id == created.id
    with pytest.raises(ConflictError):
        service.create_professor(db, ProfessorCreate(nome="Outra", cpf=created.cpf))
    assert (
        service.update_professor(db, created.id, ProfessorUpdate(formacao="Letras")).formacao
        == "Letras"
    )
    assert service.list_professores(db, busca="marta", limit=10, offset=0).total == 1
    assert [p.id for p in service.list_professores_reads(db, [created.id])] == [created.id]
    service.delete_professor(db, created.id)
    with pytest.raises(NotFoundError):
        service.get_professor(db, created.id)
    assert service.get_professor_by_user(db, 99_999_999) is None


def test_funcionario_crud_with_staff_role(db):
    created = service.create_funcionario(
        db,
        FuncionarioCreate(
            nome="Sandra Secretaria",
            cpf=valid_cpf(),
            cargo="Secretária escolar",
            tipo=TipoFuncionario.ADMINISTRATIVO,
            acesso=FuncionarioAcesso(
                email="sandra@escola.com", password="Senha1234", role=Role.SECRETARIA
            ),
        ),
    )
    user = db.get(User, created.user_id)
    assert user is not None
    assert user.role == Role.SECRETARIA
    with pytest.raises(ConflictError):
        service.create_funcionario(
            db,
            FuncionarioCreate(
                nome="Dup", cpf=created.cpf, cargo="X1", tipo=TipoFuncionario.ADMINISTRATIVO
            ),
        )
    updated = service.update_funcionario(db, created.id, FuncionarioUpdate(cargo="Coordenadora"))
    assert updated.cargo == "Coordenadora"
    assert service.get_funcionario(db, created.id).id == created.id
    assert service.list_funcionarios(db, busca=None, limit=10, offset=0).total >= 1
    service.delete_funcionario(db, created.id)
    with pytest.raises(NotFoundError):
        service.get_funcionario(db, created.id)


def test_funcionario_acesso_cannot_be_responsavel_or_professor():
    with pytest.raises(ValueError):
        FuncionarioAcesso(email="x@escola.com", password="Senha1234", role=Role.RESPONSAVEL)


def test_professor_factory_without_user(db):
    professor = make_professor(db, with_user=False)
    assert service.get_professor(db, professor.id).user_id is None


def test_include_deleted_keeps_history_visible_to_family(db):
    mae = make_responsavel(db)
    aluno = make_aluno(db, responsaveis=[mae])
    service.soft_delete_aluno_record(db, aluno.id)
    with pytest.raises(NotFoundError):
        service.ensure_can_access_aluno(db, as_user(mae), aluno.id)
    service.ensure_can_access_aluno(db, as_user(mae), aluno.id, include_deleted=True)
    service.ensure_can_access_aluno(db, current_user(Role.SECRETARIA), aluno.id, include_deleted=True)
    assert service.list_alunos_reads(db, [aluno.id]) == []
    assert [a.id for a in service.list_alunos_reads(db, [aluno.id], include_deleted=True)] == [aluno.id]
