from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.modules.turmas.schemas import CAPACIDADE_MAXIMA
from app.shared.serie import Serie, Turno


class Turma(TimestampMixin, Base):
    """Turma = série + ano letivo + turno.

    `vagas_ocupadas` é mantido pelo service sob lock de linha (SELECT ... FOR UPDATE).
    As CHECKs do banco são uma segunda linha de defesa caso alguém esqueça o lock.
    """

    __tablename__ = "turmas"
    __table_args__ = (
        UniqueConstraint("serie", "ano_letivo", "turno"),
        CheckConstraint(
            f"capacidade BETWEEN 1 AND {CAPACIDADE_MAXIMA}", name="capacidade_maxima"
        ),
        CheckConstraint(
            "vagas_ocupadas >= 0 AND vagas_ocupadas <= capacidade", name="vagas_ocupadas_validas"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    serie: Mapped[Serie] = mapped_column(Enum(Serie, native_enum=False, length=20))
    ano_letivo: Mapped[int] = mapped_column(Integer, index=True)
    turno: Mapped[Turno] = mapped_column(Enum(Turno, native_enum=False, length=20))
    capacidade: Mapped[int] = mapped_column(Integer, default=CAPACIDADE_MAXIMA)
    vagas_ocupadas: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class TurmaProfessor(Base):
    __tablename__ = "turma_professor"

    turma_id: Mapped[int] = mapped_column(ForeignKey("turmas.id"), primary_key=True)
    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professores.id"), primary_key=True, index=True
    )
