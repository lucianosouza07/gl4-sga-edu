import re
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/professores", tags=["Professores"])

# Armazenamento em memória (some ao reiniciar o servidor).
# Quando o banco de dados existir, troque esta lista por consultas ao banco.
PROFESSORES = []

TITULACOES = ["Graduação", "Especialização", "Mestrado", "Doutorado"]


class ProfessorEntrada(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: str
    cpf: str
    telefone: Optional[str] = None
    departamento: str = Field(min_length=2, max_length=80)
    titulacao: str

    @field_validator("nome", "departamento")
    @classmethod
    def sem_espacos_nas_pontas(cls, v):
        return v.strip()

    @field_validator("email")
    @classmethod
    def validar_email(cls, v):
        v = v.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("E-mail inválido.")
        return v

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v):
        digitos = re.sub(r"\D", "", v)
        if len(digitos) != 11:
            raise ValueError("CPF deve ter 11 dígitos.")
        return digitos

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, v):
        if v is None or not v.strip():
            return None
        digitos = re.sub(r"\D", "", v)
        if len(digitos) not in (10, 11):
            raise ValueError("Telefone inválido.")
        return v.strip()

    @field_validator("titulacao")
    @classmethod
    def validar_titulacao(cls, v):
        if v not in TITULACOES:
            raise ValueError("Titulação inválida.")
        return v


def _buscar(professor_id: int) -> dict:
    for p in PROFESSORES:
        if p["id"] == professor_id:
            return p
    raise HTTPException(status_code=404, detail="Professor não encontrado.")


def _checar_duplicado(dados: ProfessorEntrada, ignorar_id: Optional[int] = None):
    for p in PROFESSORES:
        if p["id"] == ignorar_id:
            continue
        if p["cpf"] == dados.cpf:
            raise HTTPException(status_code=409, detail="Já existe um professor com esse CPF.")
        if p["email"] == dados.email:
            raise HTTPException(status_code=409, detail="Já existe um professor com esse e-mail.")


# Quando o login existir, proteja estas rotas com a dependência de autenticação
# do projeto (ex.: dependencies=[Depends(...)] no APIRouter acima).

@router.post("", status_code=201)
def cadastrar(dados: ProfessorEntrada):
    _checar_duplicado(dados)
    novo_id = max((p["id"] for p in PROFESSORES), default=0) + 1
    professor = {"id": novo_id, **dados.model_dump()}
    PROFESSORES.append(professor)
    return professor


@router.get("")
def listar():
    return sorted(PROFESSORES, key=lambda p: p["nome"].lower())


@router.get("/{professor_id}")
def detalhar(professor_id: int):
    return _buscar(professor_id)


@router.put("/{professor_id}")
def atualizar(professor_id: int, dados: ProfessorEntrada):
    professor = _buscar(professor_id)
    _checar_duplicado(dados, ignorar_id=professor_id)
    professor.update(dados.model_dump())
    return professor


@router.delete("/{professor_id}")
def excluir(professor_id: int):
    professor = _buscar(professor_id)
    PROFESSORES.remove(professor)
    return {"mensagem": "Professor removido."}
