"""Reseta a senha de contas de teste já existentes pra valores conhecidos (uso manual/dev)."""

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.auth.models import User

RESETS = {
    "teste.responsavel39@semeando.edu.br": "resp12345",
    "aluno720@semeando.edu.br": "aluno12345",
}


def main() -> None:
    with SessionLocal() as db:
        for email, password in RESETS.items():
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                print(f"AVISO: {email} não encontrado.")
                continue
            user.password_hash = hash_password(password)
            print(f"{email} -> senha redefinida: {password}")
        db.commit()


if __name__ == "__main__":
    main()
