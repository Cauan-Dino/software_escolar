import pytest

from app.core.config import settings
from app.core.roles import Role
from tests.factories import make_aluno, make_responsavel, responsavel_headers, valid_cpf

BASE = "/api/v1/pessoas"


def aluno_payload(responsavel_id: int) -> dict:
    return {
        "nome": "Pedro Henrique",
        "data_nascimento": "2018-07-20",
        "responsaveis": [
            {"responsavel_id": responsavel_id, "parentesco": "MAE", "responsavel_financeiro": True}
        ],
    }


# --- Alunos -------------------------------------------------------------------------------


def test_list_alunos_requires_auth_and_staff(client, headers_for):
    assert client.get(f"{BASE}/alunos").status_code == 401
    assert client.get(f"{BASE}/alunos", headers=headers_for(Role.RESPONSAVEL)).status_code == 403
    assert client.get(f"{BASE}/alunos", headers=headers_for(Role.PROFESSOR)).status_code == 403


def test_list_alunos_returns_masked_cpf(client, db, headers_for):
    cpf = valid_cpf()
    make_aluno(db, nome="Lara Mascarada", cpf=cpf)
    response = client.get(
        f"{BASE}/alunos", params={"busca": "Mascarada"}, headers=headers_for(Role.SECRETARIA)
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["cpf"].startswith("***.")
    assert cpf not in response.text


def test_create_aluno_happy_path_and_validation(client, db, headers_for):
    mae = make_responsavel(db)
    headers = headers_for(Role.SECRETARIA)
    created = client.post(f"{BASE}/alunos", json=aluno_payload(mae.id), headers=headers)
    assert created.status_code == 201
    assert created.json()["responsaveis"][0]["responsavel_financeiro"] is True
    invalid = aluno_payload(mae.id)
    invalid["responsaveis"][0]["responsavel_financeiro"] = False
    assert client.post(f"{BASE}/alunos", json=invalid, headers=headers).status_code == 422
    future = aluno_payload(mae.id) | {"data_nascimento": "2999-01-01"}
    assert client.post(f"{BASE}/alunos", json=future, headers=headers).status_code == 422


def test_create_aluno_forbidden_for_responsavel_and_financeiro(client, db, headers_for):
    mae = make_responsavel(db)
    for role in (Role.RESPONSAVEL, Role.FINANCEIRO, Role.PROFESSOR):
        response = client.post(
            f"{BASE}/alunos", json=aluno_payload(mae.id), headers=headers_for(role)
        )
        assert response.status_code == 403


def test_responsavel_sees_own_child_but_not_other_family(client, db):
    mae = make_responsavel(db)
    filho = make_aluno(db, responsaveis=[mae])
    alheio = make_aluno(db)
    headers = responsavel_headers(db, mae)
    own = client.get(f"{BASE}/alunos/{filho.id}", headers=headers)
    assert own.status_code == 200
    assert own.json()["id"] == filho.id
    other = client.get(f"{BASE}/alunos/{alheio.id}", headers=headers)
    assert other.status_code == 404
    assert other.json()["code"] == "NOT_FOUND"


def test_professor_cannot_read_aluno_detail(client, db, headers_for):
    aluno = make_aluno(db)
    assert (
        client.get(f"{BASE}/alunos/{aluno.id}", headers=headers_for(Role.PROFESSOR)).status_code
        == 403
    )


def test_update_and_delete_aluno(client, db, headers_for):
    aluno = make_aluno(db)
    updated = client.patch(
        f"{BASE}/alunos/{aluno.id}",
        json={"nome": "Nome Novo"},
        headers=headers_for(Role.SECRETARIA),
    )
    assert updated.status_code == 200
    assert updated.json()["nome"] == "Nome Novo"
    assert (
        client.delete(f"{BASE}/alunos/{aluno.id}", headers=headers_for(Role.SECRETARIA)).status_code
        == 403
    )
    assert (
        client.delete(f"{BASE}/alunos/{aluno.id}", headers=headers_for(Role.ADMIN)).status_code
        == 204
    )
    assert (
        client.get(f"{BASE}/alunos/{aluno.id}", headers=headers_for(Role.ADMIN)).status_code == 404
    )


def test_vinculo_endpoints(client, db, headers_for):
    mae = make_responsavel(db)
    pai = make_responsavel(db)
    aluno = make_aluno(db, responsaveis=[mae])
    headers = headers_for(Role.SECRETARIA)
    added = client.post(
        f"{BASE}/alunos/{aluno.id}/responsaveis",
        json={"responsavel_id": pai.id, "parentesco": "PAI"},
        headers=headers,
    )
    assert added.status_code == 200
    moved = client.patch(
        f"{BASE}/alunos/{aluno.id}/responsaveis/{pai.id}",
        json={"responsavel_financeiro": True},
        headers=headers,
    )
    assert moved.status_code == 200
    financeiros = [r for r in moved.json()["responsaveis"] if r["responsavel_financeiro"]]
    assert [r["responsavel_id"] for r in financeiros] == [pai.id]
    refuse_false = client.patch(
        f"{BASE}/alunos/{aluno.id}/responsaveis/{pai.id}",
        json={"responsavel_financeiro": False},
        headers=headers,
    )
    assert refuse_false.status_code == 422
    removed = client.delete(f"{BASE}/alunos/{aluno.id}/responsaveis/{mae.id}", headers=headers)
    assert removed.status_code == 200
    last = client.delete(f"{BASE}/alunos/{aluno.id}/responsaveis/{pai.id}", headers=headers)
    assert last.status_code == 422
    assert last.json()["code"] == "ALUNO_SEM_RESPONSAVEL"


# --- Responsáveis -------------------------------------------------------------------------


def registro_payload(**overrides) -> dict:
    return {
        "nome": "Mariana Costa",
        "cpf": valid_cpf(),
        "email": "mariana@teste.com",
        "telefone": "(79) 99999-1234",
        "password": "Senha1234",
    } | overrides


def test_public_registration_creates_responsavel(client):
    response = client.post(f"{BASE}/responsaveis/registro", json=registro_payload())
    assert response.status_code == 201
    login = client.post(
        "/api/v1/auth/login", json={"email": "mariana@teste.com", "password": "Senha1234"}
    )
    assert login.json()["user"]["role"] == "RESPONSAVEL"


@pytest.mark.parametrize("field", [{"role": "ADMIN"}, {"user_id": 1}, {"is_active": True}])
def test_registration_rejects_privileged_fields(client, field):
    response = client.post(f"{BASE}/responsaveis/registro", json=registro_payload(**field))
    assert response.status_code == 422


def test_registration_rejects_invalid_cpf_and_weak_password(client):
    assert (
        client.post(
            f"{BASE}/responsaveis/registro", json=registro_payload(cpf="111.111.111-11")
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"{BASE}/responsaveis/registro", json=registro_payload(password="123")
        ).status_code
        == 422
    )


def test_registration_with_existing_cpf_returns_409(client, db):
    existente = make_responsavel(db, with_user=False)
    response = client.post(
        f"{BASE}/responsaveis/registro", json=registro_payload(cpf=existente.cpf)
    )
    assert response.status_code == 409


def test_registration_is_rate_limited(client):
    for i in range(settings.register_rate_limit_per_minute):
        client.post(f"{BASE}/responsaveis/registro", json=registro_payload(email=f"r{i}@teste.com"))
    response = client.post(
        f"{BASE}/responsaveis/registro", json=registro_payload(email="ultimo@teste.com")
    )
    assert response.status_code == 429


def test_responsaveis_crud_and_permissions(client, db, headers_for):
    headers = headers_for(Role.SECRETARIA)
    payload = {"nome": "Paulo Ramos", "cpf": valid_cpf(), "telefone": "79999990000"}
    assert (
        client.post(
            f"{BASE}/responsaveis", json=payload, headers=headers_for(Role.RESPONSAVEL)
        ).status_code
        == 403
    )
    created = client.post(f"{BASE}/responsaveis", json=payload, headers=headers)
    assert created.status_code == 201
    rid = created.json()["id"]
    listed = client.get(f"{BASE}/responsaveis", headers=headers_for(Role.FINANCEIRO))
    item = next(i for i in listed.json()["items"] if i["id"] == rid)
    assert item["cpf"].startswith("***.")
    assert item["tem_acesso"] is False
    assert client.get(f"{BASE}/responsaveis/{rid}", headers=headers).json()["cpf"] == payload["cpf"]
    patched = client.patch(
        f"{BASE}/responsaveis/{rid}", json={"telefone": "79988887777"}, headers=headers
    )
    assert patched.json()["telefone"] == "79988887777"
    acesso = client.post(
        f"{BASE}/responsaveis/{rid}/acesso",
        json={"email": "paulo@teste.com", "password": "Senha1234"},
        headers=headers,
    )
    assert acesso.status_code == 200
    assert acesso.json()["user_id"] is not None


# --- Professores e funcionários -----------------------------------------------------------


def test_professores_endpoints(client, headers_for):
    headers = headers_for(Role.SECRETARIA)
    created = client.post(
        f"{BASE}/professores",
        json={
            "nome": "Prof Helena",
            "cpf": valid_cpf(),
            "acesso": {"email": "helena@escola.com", "password": "Senha1234"},
        },
        headers=headers,
    )
    assert created.status_code == 201
    pid = created.json()["id"]
    assert client.get(f"{BASE}/professores", headers=headers).json()["total"] >= 1
    assert client.get(f"{BASE}/professores/{pid}", headers=headers).status_code == 200
    assert (
        client.patch(
            f"{BASE}/professores/{pid}", json={"formacao": "Letras"}, headers=headers
        ).status_code
        == 200
    )
    assert client.get(f"{BASE}/professores", headers=headers_for(Role.PROFESSOR)).status_code == 403
    assert client.delete(f"{BASE}/professores/{pid}", headers=headers).status_code == 204


def test_funcionarios_are_admin_only(client, headers_for):
    payload = {
        "nome": "Joaquim Porteiro",
        "cpf": valid_cpf(),
        "cargo": "Porteiro",
        "tipo": "PRESTADOR_SERVICO",
    }
    assert (
        client.post(
            f"{BASE}/funcionarios", json=payload, headers=headers_for(Role.SECRETARIA)
        ).status_code
        == 403
    )
    headers = headers_for(Role.ADMIN)
    created = client.post(f"{BASE}/funcionarios", json=payload, headers=headers)
    assert created.status_code == 201
    fid = created.json()["id"]
    assert client.get(f"{BASE}/funcionarios", headers=headers).status_code == 200
    assert client.get(f"{BASE}/funcionarios/{fid}", headers=headers).status_code == 200
    assert (
        client.patch(f"{BASE}/funcionarios/{fid}", json={"cargo": "Vigia"}, headers=headers).json()[
            "cargo"
        ]
        == "Vigia"
    )
    assert client.delete(f"{BASE}/funcionarios/{fid}", headers=headers).status_code == 204


def test_funcionario_acesso_cannot_create_responsavel_role(client, headers_for):
    payload = {
        "nome": "Tentativa Errada",
        "cpf": valid_cpf(),
        "cargo": "Auxiliar",
        "tipo": "ADMINISTRATIVO",
        "acesso": {"email": "tent@escola.com", "password": "Senha1234", "role": "RESPONSAVEL"},
    }
    assert (
        client.post(
            f"{BASE}/funcionarios", json=payload, headers=headers_for(Role.ADMIN)
        ).status_code
        == 422
    )
