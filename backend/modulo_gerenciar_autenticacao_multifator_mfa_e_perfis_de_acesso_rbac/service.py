"""Regras de negócio para MFA (setup, ativação, desafio, contingência) e governança RBAC."""

from typing import Any, Optional
from fastapi import HTTPException, Request, status

from .audit_service import registrar_evento_auditoria
from .repository import MfaRbacRepository
from .schemas import (
    AuditoriaItemResponse,
    MfaActivateResponse,
    MfaAdminResetResponse,
    MfaChallengeResponse,
    MfaSetupResponse,
    MfaStatusResponse,
    PERFIL_ID_PARA_NOME,
    PerfilResponse,
    SimpleMessageResponse,
    UsuarioRbacResponse,
)
from .security import (
    decodificar_token_desafio_mfa,
    gerar_token_sessao,
    verificar_senha,
)
from .totp_service import (
    gerar_codigos_recuperacao,
    gerar_segredo_base32,
    gerar_uri_otpauth,
    hash_codigo_recuperacao,
    validar_codigo_totp,
)


class MfaRbacService:
    """Serviço orquestrador de operações de MFA e administração RBAC."""

    def __init__(self, repo: MfaRbacRepository) -> None:
        self.repo = repo

    # --- User Story 1: Ativação e Configuração de MFA pelo Titular ---

    def iniciar_setup_mfa(
        self,
        usuario_id: int,
        request: Optional[Request] = None,
    ) -> MfaSetupResponse:
        usuario = self.repo.buscar_usuario_por_id(usuario_id)
        if not usuario or int(usuario.get("statusCONTA", 0)) != 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido ou inativo.",
            )

        segredo = gerar_segredo_base32()
        login = str(usuario["login"])
        uri = gerar_uri_otpauth(login=login, segredo=segredo, emissor="SGA-Edu")

        # Salva o segredo temporário com validade de 10 minutos (600s)
        self.repo.salvar_segredo_provisorio(usuario_id=usuario_id, segredo=segredo, ttl_segundos=600)

        registrar_evento_auditoria(
            repo=self.repo,
            acao="MFA_SETUP_INICIADO",
            usuario_id=usuario_id,
            id_registro_afetado=usuario_id,
            dados_novos={"mfa_setup": "iniciado", "login": login},
            request=request,
        )

        return MfaSetupResponse(
            secret=segredo,
            otpauth_uri=uri,
            validade_segundos=600,
        )

    def ativar_mfa(
        self,
        usuario_id: int,
        codigo: str,
        request: Optional[Request] = None,
    ) -> MfaActivateResponse:
        usuario = self.repo.buscar_usuario_por_id(usuario_id)
        if not usuario or int(usuario.get("statusCONTA", 0)) != 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido ou inativo.",
            )

        segredo_provisorio = self.repo.obter_segredo_provisorio(usuario_id)
        if not segredo_provisorio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma configuração de MFA pendente ou prazo de validação expirado.",
            )

        valido, passo = validar_codigo_totp(segredo=segredo_provisorio, codigo_submetido=codigo, drift_passos=1)
        if not valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de verificação incorreto ou expirado.",
            )

        codigos_recuperacao = gerar_codigos_recuperacao(8)
        hashes = [hash_codigo_recuperacao(c) for c in codigos_recuperacao]

        self.repo.ativar_mfa(
            usuario_id=usuario_id,
            segredo=segredo_provisorio,
            hashes_recuperacao=hashes,
        )

        registrar_evento_auditoria(
            repo=self.repo,
            acao="MFA_ATIVADO",
            usuario_id=usuario_id,
            id_registro_afetado=usuario_id,
            dados_novos={"mfa_ativo": True, "total_codigos_contingencia": 8},
            request=request,
        )

        return MfaActivateResponse(
            mfa_ativo=True,
            backup_codes=codigos_recuperacao,
        )

    def consultar_status_mfa(self, usuario_id: int) -> MfaStatusResponse:
        usuario = self.repo.buscar_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        token_mfa = usuario.get("tokenMFA")
        mfa_ativo = bool(token_mfa)
        return MfaStatusResponse(
            mfa_ativo=mfa_ativo,
            token_mfa_configurado=mfa_ativo,
        )

    def desativar_mfa_usuario(
        self,
        usuario_id: int,
        senha: str,
        codigo: str,
        request: Optional[Request] = None,
    ) -> SimpleMessageResponse:
        usuario = self.repo.buscar_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        if not usuario.get("tokenMFA"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA não está ativo nesta conta.",
            )

        # 1. Validar senha primária
        if not verificar_senha(senha, str(usuario.get("senha_hash", ""))):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha incorreta.",
            )

        # 2. Validar código TOTP ou código de recuperação
        segredo = str(usuario["tokenMFA"])
        valido_totp, _ = validar_codigo_totp(segredo=segredo, codigo_submetido=codigo, drift_passos=1)
        valido_backup = False

        if not valido_totp:
            h = hash_codigo_recuperacao(codigo)
            valido_backup = self.repo.consumir_codigo_recuperacao(usuario_id=usuario_id, hash_codigo=h)

        if not valido_totp and not valido_backup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de verificação incorreto ou inválido.",
            )

        self.repo.desativar_mfa(usuario_id)

        registrar_evento_auditoria(
            repo=self.repo,
            acao="MFA_DESATIVADO",
            usuario_id=usuario_id,
            id_registro_afetado=usuario_id,
            dados_anteriores={"mfa_ativo": True},
            dados_novos={"mfa_ativo": False},
            request=request,
        )

        return SimpleMessageResponse(mensagem="MFA desativado com sucesso.")

    # --- User Story 2: Desafio de Autenticação Multifator no Login ---

    def processar_desafio_mfa(
        self,
        challenge_token: str,
        codigo: str,
        request: Optional[Request] = None,
    ) -> MfaChallengeResponse:
        try:
            payload = decodificar_token_desafio_mfa(challenge_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de desafio inválido ou expirado.",
            )

        jti = str(payload.get("jti", ""))
        tentativas = self.repo.obter_tentativas_desafio_falhas(jti)
        if tentativas >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limite de tentativas excedido para este desafio. Realize novo login.",
            )

        usuario_id = int(payload.get("sub", 0))
        usuario = self.repo.buscar_usuario_por_id(usuario_id)
        if not usuario or int(usuario.get("statusCONTA", 0)) != 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido ou inativo.",
            )

        segredo = usuario.get("tokenMFA")
        if not segredo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA não configurado nesta conta.",
            )

        codigo_limpo = codigo.strip()
        valido_totp = False
        valido_backup = False

        # 1. Tentativa de validação como TOTP de 6 dígitos
        if len(codigo_limpo) == 6 and codigo_limpo.isdigit():
            valido_totp, passo = validar_codigo_totp(segredo=str(segredo), codigo_submetido=codigo_limpo, drift_passos=1)
            if valido_totp and passo is not None:
                # Checagem Anti-Replay
                if not self.repo.registrar_passo_totp_consumido(usuario_id=usuario_id, passo=passo):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Código TOTP já utilizado nesta janela temporal. Aguarde o próximo código.",
                    )

        # 2. Se não foi TOTP, tentar como código de recuperação
        if not valido_totp:
            h = hash_codigo_recuperacao(codigo_limpo)
            valido_backup = self.repo.consumir_codigo_recuperacao(usuario_id=usuario_id, hash_codigo=h)

        if not valido_totp and not valido_backup:
            novas_tentativas = self.repo.registrar_tentativa_desafio_falha(jti)
            restantes = max(0, 5 - novas_tentativas)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Código de segundo fator incorreto ou inválido. Tentativas restantes: {restantes}.",
            )

        # Sucesso: limpa tentativas e emite sessão
        self.repo.limpar_tentativas_desafio(jti)
        acao_audit = "MFA_DESAFIO_SUCESSO" if valido_totp else "MFA_CODIGO_RECUPERACAO_USADO"

        registrar_evento_auditoria(
            repo=self.repo,
            acao=acao_audit,
            usuario_id=usuario_id,
            id_registro_afetado=usuario_id,
            dados_novos={"metodo": "totp" if valido_totp else "backup_code"},
            request=request,
        )

        perfil_id = int(usuario["perfil_RBAC"])
        login = str(usuario["login"])
        access_token = gerar_token_sessao(usuario_id=usuario_id, login=login, perfil_id=perfil_id)

        return MfaChallengeResponse(
            access_token=access_token,
            token_type="bearer",
            perfil_RBAC=perfil_id,
            usuario_id=usuario_id,
            login=login,
        )

    # --- User Story 3: Governança RBAC e Redefinição Emergencial de MFA ---

    def listar_perfis(self) -> list[PerfilResponse]:
        perfis = self.repo.listar_perfis()
        return [PerfilResponse.model_validate(p) for p in perfis]

    def consultar_usuario_rbac(self, usuario_id: int) -> UsuarioRbacResponse:
        usuario = self.repo.buscar_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        return UsuarioRbacResponse(
            id_usuario=int(usuario["id_usuario"]),
            login=str(usuario["login"]),
            perfil_RBAC=int(usuario["perfil_RBAC"]),
            nome_perfil=str(usuario["nome_perfil"]),
            statusCONTA=int(usuario["statusCONTA"]),
            mfa_ativo=bool(usuario.get("tokenMFA")),
            criado_em=str(usuario.get("criado_em")) if usuario.get("criado_em") else None,
        )

    def alterar_perfil_usuario(
        self,
        usuario_id: int,
        novo_perfil_id: int,
        admin_executor_id: int,
        request: Optional[Request] = None,
    ) -> UsuarioRbacResponse:
        if novo_perfil_id not in PERFIL_ID_PARA_NOME:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identificador de perfil RBAC inválido.",
            )

        usuario = self.repo.buscar_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        perfil_atual = int(usuario["perfil_RBAC"])
        if perfil_atual == novo_perfil_id:
            # Sem alteração necessária
            return self.consultar_usuario_rbac(usuario_id)

        # Salvaguarda mandatória: não permitir rebaixar o único Admin ativo do sistema
        if perfil_atual == 5 and novo_perfil_id != 5:
            total_admins_ativos = self.repo.contar_admins_ativos()
            if total_admins_ativos <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Não é permitido alterar o perfil do único administrador ativo do sistema.",
                )

        self.repo.atualizar_perfil_usuario(usuario_id=usuario_id, novo_perfil_id=novo_perfil_id)

        registrar_evento_auditoria(
            repo=self.repo,
            acao="RBAC_PERFIL_ALTERADO",
            usuario_id=admin_executor_id,
            id_registro_afetado=usuario_id,
            dados_anteriores={"perfil_RBAC": perfil_atual, "nome_perfil": PERFIL_ID_PARA_NOME.get(perfil_atual)},
            dados_novos={"perfil_RBAC": novo_perfil_id, "nome_perfil": PERFIL_ID_PARA_NOME.get(novo_perfil_id)},
            request=request,
        )

        return self.consultar_usuario_rbac(usuario_id)

    def redefinir_mfa_admin(
        self,
        usuario_id: int,
        admin_executor_id: int,
        request: Optional[Request] = None,
    ) -> MfaAdminResetResponse:
        usuario = self.repo.buscar_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        tinha_mfa = bool(usuario.get("tokenMFA"))
        self.repo.desativar_mfa(usuario_id)

        registrar_evento_auditoria(
            repo=self.repo,
            acao="MFA_REDEFINIDO_ADMIN",
            usuario_id=admin_executor_id,
            id_registro_afetado=usuario_id,
            dados_anteriores={"mfa_ativo": tinha_mfa},
            dados_novos={"mfa_ativo": False, "motivo": "Redefinição emergencial executada por administrador"},
            request=request,
        )

        return MfaAdminResetResponse(
            mensagem="MFA desativado com sucesso pelo administrador.",
            mfa_ativo=False,
        )

    def consultar_auditoria(
        self,
        usuario_id: Optional[int] = None,
        acao: Optional[str] = None,
        limite: int = 50,
    ) -> list[AuditoriaItemResponse]:
        rows = self.repo.listar_auditoria(usuario_id=usuario_id, acao=acao, limite=limite)
        return [
            AuditoriaItemResponse(
                id_auditoria=int(r["id_auditoria"]),
                usuario_id=r["usuario_id"],
                entidade_afetada=str(r["entidade_afetada"]),
                id_registro_afetado=str(r["id_registro_afetado"]) if r["id_registro_afetado"] else None,
                acao=str(r["acao"]),
                dados_anteriores=r["dados_anteriores"],
                dados_novos=r["dados_novos"],
                ip_origem=str(r["ip_origem"]),
                data_hora=str(r["data_hora"]),
            )
            for r in rows
        ]
