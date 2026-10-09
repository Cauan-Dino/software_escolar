"""Factories para criar dados de teste rapidamente (gravam direto pelos models).

Os testes podem importar models de qualquer módulo; a regra de isolamento vale só para `app/`.
"""

import itertools
from datetime import date

from sqlalchemy.orm import Session

from app.core.roles import Role
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.pessoas.models import Aluno, Professor, Responsavel, ResponsavelAluno
from app.modules.pessoas.schemas import Parentesco
from tests.helpers import auth_headers

DEFAULT_PASSWORD = "Senha123"
_seq = itertools.count(1)
_PASSWORD_HASH = hash_password(DEFAULT_PASSWORD)


def valid_cpf(seed: int | None = None) -> str:
    """Gera um CPF válido (com dígitos verificadores corretos) e único na sessão de testes."""
    base = f"{(seed if seed is not None else next(_seq)) + 100_000_000:09d}"[-9:]
    digits = [int(d) for d in base]
    for size in (9, 10):
        total = sum(d * (size + 1 - i) for i, d in enumerate(digits[:size]))
        digits.append((total * 10) % 11 % 10)
    return "".join(map(str, digits))


def make_user(
    db: Session,
    role: Role = Role.RESPONSAVEL,
    *,
    email: str | None = None,
    nome: str | None = None,
    is_active: bool = True,
) -> User:
    n = next(_seq)
    user = User(
        email=email or f"usuario{n}@teste.com",
        nome=nome or f"Usuário {n}",
        password_hash=_PASSWORD_HASH,
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.flush()
    return user


def headers_of(user: User) -> dict[str, str]:
    return auth_headers(user.id, user.role, user.email)


def make_responsavel(
    db: Session, *, with_user: bool = True, nome: str | None = None, cpf: str | None = None
) -> Responsavel:
    n = next(_seq)
    user = make_user(db, Role.RESPONSAVEL) if with_user else None
    responsavel = Responsavel(
        user_id=user.id if user else None,
        nome=nome or f"Responsável {n}",
        cpf=cpf or valid_cpf(),
        email=user.email if user else f"resp{n}@teste.com",
        telefone="(79) 99999-0000",
    )
    db.add(responsavel)
    db.flush()
    return responsavel


def make_aluno(
    db: Session,
    *,
    responsaveis: list[Responsavel] | None = None,
    nome: str | None = None,
    cpf: str | None = None,
    data_nascimento: date | None = None,
) -> Aluno:
    """Cria um aluno vinculado aos responsáveis informados (o primeiro é o financeiro)."""
    n = next(_seq)
    aluno = Aluno(
        nome=nome or f"Aluno {n}",
        data_nascimento=data_nascimento or date(2019, 5, 10),
        cpf=cpf,
    )
    db.add(aluno)
    db.flush()
    for index, responsavel in enumerate(responsaveis or [make_responsavel(db)]):
        db.add(
            ResponsavelAluno(
                aluno_id=aluno.id,
                responsavel_id=responsavel.id,
                parentesco=Parentesco.MAE if index == 0 else Parentesco.PAI,
                responsavel_financeiro=index == 0,
                pode_buscar=True,
            )
        )
    db.flush()
    db.refresh(aluno)
    return aluno


def make_professor(db: Session, *, with_user: bool = True) -> Professor:
    n = next(_seq)
    user = make_user(db, Role.PROFESSOR) if with_user else None
    professor = Professor(
        user_id=user.id if user else None,
        nome=f"Professor {n}",
        cpf=valid_cpf(),
        email=user.email if user else None,
    )
    db.add(professor)
    db.flush()
    return professor


def responsavel_headers(db: Session, responsavel: Responsavel) -> dict[str, str]:
    user = db.get(User, responsavel.user_id)
    assert user is not None
    return headers_of(user)
