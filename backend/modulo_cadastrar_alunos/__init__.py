"""
Módulo: Cadastrar alunos (SGA-15).

Gerencia o cadastro oficial de estudantes no SGA-Edu por operadores de
Secretaria Acadêmica e Administração, unificando dados pessoais, de contato
e vínculo acadêmico com a geração de matrícula única, provisionamento atômico
da conta de acesso com perfil Aluno e registro na trilha de auditoria LGPD.
"""

from .audit_service import extrair_ip_cliente, registrar_evento_auditoria, sanitizar_snapshot
from .repository import AlunoRepository, criar_conexao, get_repository, inicializar_esquema
from .router import app, router
from .schemas import (
    PERFIL_ADMIN_ID,
    PERFIL_ALUNO_ID,
    PERFIL_ALUNO_NOME,
    PERFIL_SECRETARIA_ID,
    PERFIS_OPERADORES_AUTORIZADOS,
    AlunoCreate,
    AlunoResponse,
    AlunoStatusUpdate,
    AlunoUpdate,
    AuditoriaEventoResponse,
    MensagemResponse,
    StatusAcademicoEnum,
)
from .security import (
    OperadorAutenticado,
    criar_token_sessao,
    decodificar_token_sessao,
    hash_password,
    require_secretaria_ou_admin,
    verify_password,
)
from .service import (
    alterar_status,
    atualizar_aluno,
    cadastrar_aluno,
    consultar_auditoria,
    detalhar_aluno,
    listar_alunos,
)

__all__ = [
    "PERFIL_ADMIN_ID",
    "PERFIL_ALUNO_ID",
    "PERFIL_ALUNO_NOME",
    "PERFIL_SECRETARIA_ID",
    "PERFIS_OPERADORES_AUTORIZADOS",
    "AlunoCreate",
    "AlunoRepository",
    "AlunoResponse",
    "AlunoStatusUpdate",
    "AlunoUpdate",
    "AuditoriaEventoResponse",
    "MensagemResponse",
    "OperadorAutenticado",
    "StatusAcademicoEnum",
    "alterar_status",
    "app",
    "atualizar_aluno",
    "cadastrar_aluno",
    "consultar_auditoria",
    "criar_conexao",
    "criar_token_sessao",
    "decodificar_token_sessao",
    "detalhar_aluno",
    "extrair_ip_cliente",
    "get_repository",
    "hash_password",
    "inicializar_esquema",
    "listar_alunos",
    "registrar_evento_auditoria",
    "require_secretaria_ou_admin",
    "router",
    "sanitizar_snapshot",
    "verify_password",
]
