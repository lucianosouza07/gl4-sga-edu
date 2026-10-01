import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Uuid
from sqlalchemy.orm import relationship
from app.database.session import Base


class PerfilUsuario(str, Enum):
    ADMIN = "ADMIN"
    SECRETARIA = "SECRETARIA"
    PROFESSOR = "PROFESSOR"
    ALUNO = "ALUNO"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(50), nullable=False, default=PerfilUsuario.ALUNO.value)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relacionamento 1:1 com a entidade Aluno (caso este usuário seja um aluno)
    aluno = relationship(
        "Aluno",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email} perfil={self.perfil} ativo={self.ativo}>"
