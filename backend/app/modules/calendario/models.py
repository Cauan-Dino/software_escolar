from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.modules.calendario.schemas import TipoEvento


class EventoCalendario(TimestampMixin, Base):
    """Evento do calendário escolar.

    `turma_id` nulo significa evento geral da escola, visível a todos.
    """

    __tablename__ = "eventos_calendario"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str | None] = mapped_column(String(2000), default=None)
    data_inicio: Mapped[date] = mapped_column(Date, index=True)
    data_fim: Mapped[date | None] = mapped_column(Date, default=None)
    tipo: Mapped[TipoEvento] = mapped_column(Enum(TipoEvento, native_enum=False, length=20))
    turma_id: Mapped[int | None] = mapped_column(
        ForeignKey("turmas.id"), default=None, index=True
    )
    criado_por_user_id: Mapped[int] = mapped_column(Integer)
