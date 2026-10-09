"""Cria o primeiro usuário ADMIN para destravar o login (a API não tem bootstrap).

Uso:
    uv run python -m scripts.seed_admin
    # ou, dentro do container:
    docker compose exec api python -m scripts.seed_admin

Idempotente: se já existir um usuário com o e-mail abaixo, não faz nada.
"""

from app.core.database import SessionLocal
from app.core.roles import Role
from app.core.security import hash_password
from app.modules.auth.models import User

ADMIN_EMAIL = "admin@semeando.edu.br"
ADMIN_PASSWORD = "admin1234"  # noqa: S105 — só para ambiente local de desenvolvimento
ADMIN_NOME = "Admin Semeando"


def main() -> None:
    with SessionLocal() as db:
        existente = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existente:
            print(f"Usuário {ADMIN_EMAIL} já existe (id={existente.id}). Nada a fazer.")
            return

        admin = User(
            email=ADMIN_EMAIL,
            nome=ADMIN_NOME,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=Role.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin criado: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
