from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.modules.notas.schemas import Periodo


class Nota(TimestampMixin, Base):
    """Nota de um aluno em uma disciplina/período de uma turma.

    Upsert pela chave (aluno_id, turma_id, disciplina, periodo): o service decide
    criar ou atualizar conforme já exista uma linha para essa combinação.
    """

    __tablename__ = "notas"
    __table_args__ = (
        UniqueConstraint("aluno_id", "turma_id", "disciplina", "periodo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), index=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turmas.id"), index=True)
    disciplina: Mapped[str] = mapped_column(String(100))
    periodo: Mapped[Periodo] = mapped_column(Enum(Periodo, native_enum=False, length=20))
    valor: Mapped[float] = mapped_column(Numeric(3, 1))
    observacao: Mapped[str | None] = mapped_column(String(500), default=None)
    lancado_por_user_id: Mapped[int] = mapped_column()
    lancado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
