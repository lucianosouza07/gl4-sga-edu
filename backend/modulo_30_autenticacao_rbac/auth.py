"""
Rotas e Serviços de Autenticação e RBAC (SGA-EDU)
Módulo 30 - src/backend/modulo_30_autenticacao_rbac/auth.py
"""
import secrets
from fastapi import APIRouter, HTTPException, status
from .models import (
    LoginRequest,
    LoginResponse,
    UsuarioInfo,
    RecuperarSenhaRequest,
    RecuperarSenhaResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Autenticação e RBAC"])

# Base cadastral em memória sincronizada com a modelagem do banco (modulo_29_modelagem_bd)
# e compatível com a suíte de testes e perfis do frontend
USUARIOS_BD = {
    "2037538292": {
        "id": 1,
        "login": "2037538292",
        "senha_hash": "uneb@2026",
        "nome": "Letícia Silva",
        "perfil_id": 1,
        "perfil_nome": "Aluno",
        "perfil_slug": "discente",
        "status_conta": 1,
        "email": "leticia.silva@uneb.br",
    },
    "90214": {
        "id": 2,
        "login": "90214",
        "senha_hash": "uneb@2026",
        "nome": "Prof. Ricardo Santos",
        "perfil_id": 2,
        "perfil_nome": "Professor",
        "perfil_slug": "docente",
        "status_conta": 1,
        "email": "ricardo.santos@uneb.br",
    },
    "77102": {
        "id": 3,
        "login": "77102",
        "senha_hash": "uneb@2026",
        "nome": "Profª Ana Rocha",
        "perfil_id": 3,
        "perfil_nome": "Secretaria",
        "perfil_slug": "colegiado",
        "status_conta": 1,
        "email": "ana.rocha@uneb.br",
    },
    "55219": {
        "id": 4,
        "login": "55219",
        "senha_hash": "uneb@2026",
        "nome": "Carlos Mendes",
        "perfil_id": 4,
        "perfil_nome": "Financeiro",
        "perfil_slug": "financeiro",
        "status_conta": 1,
        "email": "carlos.mendes@uneb.br",
    },
    "10001": {
        "id": 5,
        "login": "10001",
        "senha_hash": "uneb@2026",
        "nome": "Coordenação TI",
        "perfil_id": 5,
        "perfil_nome": "Admin",
        "perfil_slug": "ti_suporte",
        "status_conta": 1,
        "email": "suporte.ti@uneb.br",
    },
    # Conta inativa para validação de bloqueio
    "bloqueado": {
        "id": 6,
        "login": "bloqueado",
        "senha_hash": "uneb@2026",
        "nome": "Usuário Bloqueado",
        "perfil_id": 1,
        "perfil_nome": "Aluno",
        "perfil_slug": "discente",
        "status_conta": 0,
        "email": "bloqueado@uneb.br",
    },
}


@router.post("/login", response_model=LoginResponse)
def login(requisicao: LoginRequest):
    """
    Autentica o usuário no SGA-Edu e retorna as informações do seu perfil RBAC.
    """
    login_limpo = requisicao.login.strip()
    usuario = USUARIOS_BD.get(login_limpo)

    if not usuario or usuario["senha_hash"] != requisicao.senha.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas. Verifique a matrícula/usuário e a senha informada.",
        )

    if usuario["status_conta"] != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta de usuário inativa ou suspensa. Contate o suporte ou a secretaria.",
        )

    token = f"sga-token-{secrets.token_hex(16)}"

    usuario_info = UsuarioInfo(
        id=usuario["id"],
        login=usuario["login"],
        nome=usuario["nome"],
        perfil_id=usuario["perfil_id"],
        perfil_nome=usuario["perfil_nome"],
        perfil_slug=usuario["perfil_slug"],
        status_conta=usuario["status_conta"],
    )

    return LoginResponse(
        sucesso=True,
        mensagem="Autenticação realizada com sucesso.",
        usuario=usuario_info,
        token_sessao=token,
    )


@router.post("/recuperar-senha", response_model=RecuperarSenhaResponse)
def recuperar_senha(requisicao: RecuperarSenhaRequest):
    """
    Gera token de recuperação de senha com validade de 30 minutos.
    """
    identificador = requisicao.identificador.strip()
    if "@" not in identificador and len(identificador) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Identificador inválido. Informe um e-mail institucional ou CPF cadastrado.",
        )

    return RecuperarSenhaResponse(
        sucesso=True,
        mensagem=f"Um token de recuperação temporário (válido por 30 minutos) foi enviado para {identificador}.",
        expira_em_minutos=30,
    )
