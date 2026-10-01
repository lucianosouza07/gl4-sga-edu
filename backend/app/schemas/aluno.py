import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AlunoCreate(BaseModel):
    """Payload recebido para criação de um novo aluno."""
    matricula: str = Field(..., min_length=4, max_length=20, description="Matrícula única do aluno")
    nome_completo: str = Field(..., min_length=3, max_length=200, description="Nome completo do aluno")
    cpf: str = Field(..., min_length=11, max_length=14, description="CPF do aluno")
    email: EmailStr = Field(..., description="E-mail que será usado para login")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone de contato")
    data_nascimento: date = Field(..., description="Data de nascimento do aluno")
    senha_inicial: Optional[str] = Field(None, min_length=6, description="Senha inicial opcional (default: Mudar@123)")


class AlunoUpdate(BaseModel):
    """Payload para atualização cadastral do aluno."""
    nome_completo: Optional[str] = Field(None, min_length=3, max_length=200)
    telefone: Optional[str] = Field(None, max_length=20)
    data_nascimento: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)


class AlunoResponse(BaseModel):
    """Dados de exibição pública e retorno da API de Alunos."""
    id: uuid.UUID
    usuario_id: uuid.UUID
    matricula: str
    nome_completo: str
    cpf: str
    email: EmailStr
    telefone: Optional[str] = None
    data_nascimento: date
    status: str
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
