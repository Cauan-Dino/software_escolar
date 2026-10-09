from datetime import UTC, datetime

from app.modules.pessoas import repository
from tests.factories import make_aluno, make_professor, make_responsavel, valid_cpf


def test_get_aluno_hides_soft_deleted_unless_asked(db):
    aluno = make_aluno(db)
    aluno.deleted_at = datetime.now(UTC)
    db.flush()
    assert repository.get_aluno(db, aluno.id) is None
    assert repository.get_aluno(db, aluno.id, include_deleted=True) is not None


def test_aluno_ids_do_responsavel_ignores_deleted_children(db):
    mae = make_responsavel(db)
    ativo = make_aluno(db, responsaveis=[mae])
    removido = make_aluno(db, responsaveis=[mae])
    removido.deleted_at = datetime.now(UTC)
    db.flush()
    assert repository.list_aluno_ids_do_responsavel(db, mae.id) == [ativo.id]


def test_soft_deleted_cpf_can_be_reused(db):
    cpf = valid_cpf()
    antigo = make_aluno(db, cpf=cpf)
    antigo.deleted_at = datetime.now(UTC)
    db.flush()
    novo = make_aluno(db, cpf=cpf)  # índice único parcial ignora excluídos
    assert repository.get_aluno_by_cpf(db, cpf) == novo


def test_list_alunos_search_by_name_and_cpf(db):
    cpf = valid_cpf()
    make_aluno(db, nome="Bernardo Pesquisa", cpf=cpf)
    rows, total = repository.list_alunos(db, busca="pesquisa", limit=10, offset=0)
    assert total == 1
    assert rows[0].nome == "Bernardo Pesquisa"
    _, by_cpf = repository.list_alunos(
        db, busca=f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}", limit=10, offset=0
    )
    assert by_cpf == 1


def test_vinculos_queries(db):
    mae = make_responsavel(db)
    pai = make_responsavel(db)
    aluno = make_aluno(db, responsaveis=[mae, pai])
    vinculos = repository.list_vinculos_do_aluno(db, aluno.id)
    assert {v.responsavel_id for v in vinculos} == {mae.id, pai.id}
    vinculo = repository.get_vinculo(db, aluno.id, pai.id)
    assert vinculo is not None
    repository.delete_vinculo(db, vinculo)
    assert repository.get_vinculo(db, aluno.id, pai.id) is None


def test_responsavel_and_professor_lookups(db):
    r = make_responsavel(db)
    assert repository.get_responsavel_by_cpf(db, r.cpf) == r
    assert repository.get_responsavel_by_user_id(db, r.user_id) == r
    assert repository.list_responsaveis_by_ids(db, [r.id]) == [r]
    p = make_professor(db)
    assert repository.get_professor_by_user_id(db, p.user_id) == p
    assert repository.get_professor_by_cpf(db, p.cpf) == p
    assert repository.list_professores_by_ids(db, []) == []
    assert repository.list_alunos_by_ids(db, []) == []
