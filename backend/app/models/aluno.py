import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.database.session import Base


class StatusAluno(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    TRANCADO = "TRANCADO"
    FORMADO = "FORMADO"


class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    usuario_id = Column(
        Uuid,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    matricula = Column(String, unique=True, nullable=False, index=True)
    nome_completo = Column(String(255), nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=True)
    data_nascimento = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default=StatusAluno.ATIVO.value)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    atualizado_em = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relacionamento 1:1 inverso com Usuario
    usuario = relationship("Usuario", back_populates="aluno")

    def __repr__(self) -> str:
        return f"<Aluno id={self.id} matricula={self.matricula} nome={self.nome_completo} status={self.status}>"
