from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, SoftDeleteMixin, TimestampMixin
from app.modules.pessoas.schemas import Parentesco, TipoFuncionario

_ATIVO = text("deleted_at IS NULL")


class Aluno(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "alunos"
    __table_args__ = (
        Index(
            "uq_alunos_cpf_ativo",
            "cpf",
            unique=True,
            postgresql_where=text("cpf IS NOT NULL AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    nome: Mapped[str] = mapped_column(String(150), index=True)
    data_nascimento: Mapped[date] = mapped_column(Date)
    cpf: Mapped[str | None] = mapped_column(String(11))

    vinculos: Mapped[list["ResponsavelAluno"]] = relationship(back_populates="aluno")


class Responsavel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "responsaveis"
    __table_args__ = (
        Index("uq_responsaveis_cpf_ativo", "cpf", unique=True, postgresql_where=_ATIVO),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    nome: Mapped[str] = mapped_column(String(150), index=True)
    cpf: Mapped[str] = mapped_column(String(11))
    email: Mapped[str | None] = mapped_column(String(255))
    telefone: Mapped[str | None] = mapped_column(String(20))

    vinculos: Mapped[list["ResponsavelAluno"]] = relationship(back_populates="responsavel")


class ResponsavelAluno(Base):
    """Vínculo N:N entre responsável e aluno.

    Regras: todo aluno tem pelo menos 1 responsável e exatamente 1 responsável financeiro
    (o índice parcial abaixo garante no banco que nunca haverá dois financeiros).
    """

    __tablename__ = "responsavel_aluno"
    __table_args__ = (
        Index(
            "uq_responsavel_aluno_um_financeiro",
            "aluno_id",
            unique=True,
            postgresql_where=text("responsavel_financeiro"),
        ),
    )

    responsavel_id: Mapped[int] = mapped_column(ForeignKey("responsaveis.id"), primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), primary_key=True, index=True)
    parentesco: Mapped[Parentesco] = mapped_column(Enum(Parentesco, native_enum=False, length=20))
    responsavel_financeiro: Mapped[bool] = mapped_column(Boolean, default=False)
    pode_buscar: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    aluno: Mapped[Aluno] = relationship(back_populates="vinculos")
    responsavel: Mapped[Responsavel] = relationship(back_populates="vinculos")


class Professor(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "professores"
    __table_args__ = (
        Index("uq_professores_cpf_ativo", "cpf", unique=True, postgresql_where=_ATIVO),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    nome: Mapped[str] = mapped_column(String(150))
    cpf: Mapped[str] = mapped_column(String(11))
    email: Mapped[str | None] = mapped_column(String(255))
    telefone: Mapped[str | None] = mapped_column(String(20))
    formacao: Mapped[str | None] = mapped_column(String(150))


class Funcionario(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "funcionarios"
    __table_args__ = (
        Index("uq_funcionarios_cpf_ativo", "cpf", unique=True, postgresql_where=_ATIVO),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    nome: Mapped[str] = mapped_column(String(150))
    cpf: Mapped[str] = mapped_column(String(11))
    email: Mapped[str | None] = mapped_column(String(255))
    telefone: Mapped[str | None] = mapped_column(String(20))
    cargo: Mapped[str] = mapped_column(String(100))
    tipo: Mapped[TipoFuncionario] = mapped_column(
        Enum(TipoFuncionario, native_enum=False, length=20)
    )
