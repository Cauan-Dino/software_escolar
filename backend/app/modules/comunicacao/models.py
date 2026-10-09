from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.comunicacao.schemas import PublicoAlvo


class Aviso(Base):
    __tablename__ = "avisos"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(Text)
    corpo: Mapped[str] = mapped_column(Text)
    publico_alvo: Mapped[PublicoAlvo] = mapped_column(
        Enum(PublicoAlvo, native_enum=False, length=20)
    )
    turma_id: Mapped[int | None] = mapped_column(ForeignKey("turmas.id"), nullable=True)
    fixado: Mapped[bool] = mapped_column(default=False, server_default="false")
    publicado_por_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    publicado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LeituraAviso(Base):
    __tablename__ = "leituras_aviso"

    aviso_id: Mapped[int] = mapped_column(ForeignKey("avisos.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, index=True)
    lido_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
