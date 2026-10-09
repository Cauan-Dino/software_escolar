from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.modules.matricula.schemas import StatusMatricula, TipoDocumento, TipoMatricula
from app.shared.serie import Serie, Turno


class Matricula(TimestampMixin, Base):
    __tablename__ = "matriculas"
    __table_args__ = (
        # Um aluno só pode ter UMA matrícula em aberto por ano letivo.
        Index(
            "uq_matriculas_aluno_ano_em_aberto",
            "aluno_id",
            "ano_letivo",
            unique=True,
            postgresql_where=text("status NOT IN ('REJEITADA', 'CANCELADA')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), index=True)
    ano_letivo: Mapped[int] = mapped_column(Integer, index=True)
    serie: Mapped[Serie] = mapped_column(Enum(Serie, native_enum=False, length=20))
    turno: Mapped[Turno] = mapped_column(Enum(Turno, native_enum=False, length=20))
    turma_id: Mapped[int | None] = mapped_column(ForeignKey("turmas.id"), index=True)
    tipo: Mapped[TipoMatricula] = mapped_column(Enum(TipoMatricula, native_enum=False, length=20))
    status: Mapped[StatusMatricula] = mapped_column(
        Enum(StatusMatricula, native_enum=False, length=30), index=True
    )
    tamanho_farda: Mapped[str | None] = mapped_column(String(10))
    farda_indisponivel: Mapped[bool] = mapped_column(Boolean, default=False)
    observacoes: Mapped[str | None] = mapped_column(Text)
    motivo_rejeicao: Mapped[str | None] = mapped_column(Text)
    motivo_cancelamento: Mapped[str | None] = mapped_column(Text)
    criado_por_user_id: Mapped[int] = mapped_column(Integer)
    decidido_por_user_id: Mapped[int | None] = mapped_column(Integer)
    decidido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    documentos: Mapped[list["DocumentoMatricula"]] = relationship(
        back_populates="matricula", order_by="DocumentoMatricula.id"
    )


class DocumentoMatricula(Base):
    """Checklist de documentos: a secretaria marca `entregue` e/ou o responsável envia arquivo."""

    __tablename__ = "documentos_matricula"
    __table_args__ = (UniqueConstraint("matricula_id", "tipo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    matricula_id: Mapped[int] = mapped_column(ForeignKey("matriculas.id"), index=True)
    tipo: Mapped[TipoDocumento] = mapped_column(Enum(TipoDocumento, native_enum=False, length=30))
    entregue: Mapped[bool] = mapped_column(Boolean, default=False)
    arquivo_path: Mapped[str | None] = mapped_column(String(255))
    arquivo_nome: Mapped[str | None] = mapped_column(String(100))
    arquivo_content_type: Mapped[str | None] = mapped_column(String(50))
    conferido_por_user_id: Mapped[int | None] = mapped_column(Integer)
    conferido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    matricula: Mapped[Matricula] = relationship(back_populates="documentos")
