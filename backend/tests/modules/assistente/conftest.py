from collections.abc import Callable
from datetime import date

import pytest
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.core.roles import Role
from app.modules.assistente import service
from app.modules.assistente.llm import LLMResponse
from app.modules.auth.models import User
from app.modules.turmas.models import Turma, TurmaProfessor
from app.shared.serie import Serie, Turno
from tests.factories import make_aluno, make_professor, make_user
from tests.modules.assistente.fakes import FakeLLM


@pytest.fixture
def usar_llm(app: FastAPI) -> Callable[..., FakeLLM]:
    """`usar_llm(texto("oi"), chamar(...))` instala um LLM falso com essas respostas."""

    def _usar(*respostas: LLMResponse) -> FakeLLM:
        fake = FakeLLM(list(respostas))
        app.dependency_overrides[service.get_llm_client] = lambda: fake
        return fake

    return _usar


@pytest.fixture
def admin(db: Session) -> User:
    return make_user(db, Role.ADMIN)


@pytest.fixture
def turma(db: Session) -> Turma:
    t = Turma(
        serie=Serie.ANO_3,
        ano_letivo=date.today().year,
        turno=Turno.MANHA,
        capacidade=30,
        vagas_ocupadas=0,
        ativa=True,
    )
    db.add(t)
    db.flush()
    return t


@pytest.fixture
def aluno(db: Session):
    return make_aluno(db, nome="Joana Souza")


@pytest.fixture
def professor_da_turma(db: Session, turma: Turma):
    prof = make_professor(db)
    db.add(TurmaProfessor(turma_id=turma.id, professor_id=prof.id))
    db.flush()
    return prof


@pytest.fixture
def matricula_ativa(db: Session, aluno, turma: Turma):
    from app.modules.matricula.models import Matricula
    from app.modules.matricula.schemas import StatusMatricula, TipoMatricula

    m = Matricula(
        aluno_id=aluno.id,
        ano_letivo=turma.ano_letivo,
        serie=turma.serie,
        turno=turma.turno,
        turma_id=turma.id,
        tipo=TipoMatricula.NOVA,
        status=StatusMatricula.ATIVA,
        criado_por_user_id=1,
    )
    db.add(m)
    db.flush()
    return m
