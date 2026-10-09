from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.modules.frequencia.schemas import StatusFrequencia


class Frequencia(TimestampMixin, Base):
    """Um registro de frequência = 1 aluno em 1 dia. UNIQUE(aluno_id, data)."""

    __tablename__ = "frequencia"
    __table_args__ = (UniqueConstraint("aluno_id", "data"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), index=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turmas.id"), index=True)
    data: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[StatusFrequencia] = mapped_column(
        Enum(StatusFrequencia, native_enum=False, length=20)
    )
    observacao: Mapped[str | None] = mapped_column(String(500))
    lancado_por_user_id: Mapped[int] = mapped_column(Integer)
