"""Concede acesso de login a um professor já cadastrado (uso manual/dev)."""

from app.core.database import SessionLocal
from app.core.roles import Role
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.pessoas.models import Professor

PROFESSOR_ID = 20
EMAIL = "leticia.rodrigues@semeando.edu.br"
PASSWORD = "professor123"  # noqa: S105


def main() -> None:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == EMAIL).first()
        if user is None:
            user = User(
                email=EMAIL,
                nome="Leticia Fernandes Rodrigues",
                password_hash=hash_password(PASSWORD),
                role=Role.PROFESSOR,
                is_active=True,
            )
            db.add(user)
            db.flush()

        professor = db.get(Professor, PROFESSOR_ID)
        if professor is None:
            raise SystemExit(f"Professor {PROFESSOR_ID} não encontrado.")
        professor.user_id = user.id
        db.commit()
        print(f"Professor {PROFESSOR_ID} vinculado a {EMAIL} / {PASSWORD}")


if __name__ == "__main__":
    main()
