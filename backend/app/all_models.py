"""Importa os models de TODOS os módulos para registrá-los em `Base.metadata`.

Usado pelo Alembic (autogenerate) e pelos testes. Ao criar um módulo com tabelas,
adicione o import do `models` dele aqui.
"""

from app.core import audit  # noqa: F401
from app.core.database import Base
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.calendario import models as calendario_models  # noqa: F401
from app.modules.comunicacao import models as comunicacao_models  # noqa: F401
from app.modules.financeiro import models as financeiro_models  # noqa: F401
from app.modules.frequencia import models as frequencia_models  # noqa: F401
from app.modules.matricula import models as matricula_models  # noqa: F401
from app.modules.notas import models as notas_models  # noqa: F401
from app.modules.pessoas import models as pessoas_models  # noqa: F401
from app.modules.turmas import models as turmas_models  # noqa: F401

metadata = Base.metadata
