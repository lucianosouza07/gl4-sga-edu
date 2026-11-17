"""Schemas Pydantic para validação estrita dos contratos de entrada e saída."""

import re
from pydantic import BaseModel, EmailStr, Field, model_validator


class SolicitarRecuperacaoRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Endereço de e-mail institucional ou cadastrado do usuário",
        examples=["professor.valido@sga.edu.br"],
    )


class SolicitarRecuperacaoResponse(BaseModel):
    mensagem: str = Field(
        default="Se os dados informados corresponderem a uma conta ativa, você receberá em instantes as instruções e o link para redefinição de senha."
    )


class ValidarTokenResponse(BaseModel):
    valido: bool = Field(..., description="Indica se o token é válido para uso")
    mensagem: str = Field(..., description="Mensagem descritiva do status do token")


class RedefinirSenhaRequest(BaseModel):
    token: str = Field(..., min_length=32, description="Token opaco recebido por e-mail")
    nova_senha: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Nova senha atendendo à política de complexidade institucional",
    )
    confirmacao_senha: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Confirmação idêntica da nova senha pretendida",
    )

    @model_validator(mode="after")
    def validar_regras_senha(self) -> "RedefinirSenhaRequest":
        senha = self.nova_senha
        if self.nova_senha != self.confirmacao_senha:
            raise ValueError("A nova senha e a confirmação de senha não coincidem.")

        # Validação de complexidade: maiúscula, minúscula, número e caractere especial
        if not re.search(r"[A-Z]", senha):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r"[a-z]", senha):
            raise ValueError("A senha deve conter pelo menos uma letra minúscula.")
        if not re.search(r"[0-9]", senha):
            raise ValueError("A senha deve conter pelo menos um dígito numérico.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", senha):
            raise ValueError("A senha deve conter pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>?).")

        return self


class RedefinirSenhaResponse(BaseModel):
    sucesso: bool = Field(default=True)
    mensagem: str = Field(
        default="Senha redefinida com sucesso. Faça login com suas novas credenciais."
    )


class ErroResponse(BaseModel):
    detail: str
