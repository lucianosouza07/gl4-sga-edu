"""Camada de serviços e regras de negócio para recuperação de senhas."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

try:
    from .models import Database, TokenRecuperacao, Usuario
    from .security import (
        generate_secure_token,
        hash_password,
        hash_token,
        verify_password,
    )
    from .email_service import EmailServiceInterface
except (ImportError, ValueError):
    from models import Database, TokenRecuperacao, Usuario
    from security import (
        generate_secure_token,
        hash_password,
        hash_token,
        verify_password,
    )
    from email_service import EmailServiceInterface


TOKEN_EXPIRACAO_MINUTOS = 30


class PasswordRecoveryService:
    """Implementa as regras de emissão, expiração, validação e redefinição de credenciais."""

    @staticmethod
    def processar_solicitacao(
        email: str,
        ip_solicitacao: str,
        email_service: EmailServiceInterface,
    ) -> Tuple[bool, Optional[int]]:
        """
        Processa o pedido de recuperação com neutralidade para evitar enumeração de contas.
        Retorna (sucesso_processamento, usuario_id_ou_none).
        """
        usuario = Database.buscar_usuario_por_email(email)
        if not usuario:
            # Timing attack mitigation: simula geração de hash e retorna sem enviar e-mail
            _ = hash_token("dummy_token_para_tempo_constante")
            return True, None

        # Invalida quaisquer tokens pendentes anteriores para o mesmo usuário
        Database.revogar_tokens_pendentes(usuario.id_usuario)

        # Gera token criptograficamente seguro e calcula hash SHA-256
        token_bruto = generate_secure_token(32)
        token_digest = hash_token(token_bruto)

        agora = datetime.now(timezone.utc)
        expira_em = agora + timedelta(minutes=TOKEN_EXPIRACAO_MINUTOS)

        Database.salvar_token(
            usuario_id=usuario.id_usuario,
            token_hash=token_digest,
            criado_em=agora,
            expira_em=expira_em,
            ip_solicitacao=ip_solicitacao,
        )

        # Despacha mensagem com o token bruto via e-mail transacional
        email_service.enviar_email_recuperacao(usuario.email, token_bruto)
        return True, usuario.id_usuario

    @staticmethod
    def validar_token(token_bruto: str) -> Tuple[bool, str, Optional[TokenRecuperacao]]:
        """Verifica a integridade, vigência e uso único do token informado."""
        if not token_bruto or len(token_bruto.strip()) < 32:
            return False, "O link de recuperação é inválido, expirou ou já foi utilizado.", None

        digest = hash_token(token_bruto)
        token_registro = Database.buscar_token_por_hash(digest)

        if not token_registro:
            return False, "O link de recuperação é inválido, expirou ou já foi utilizado.", None

        if token_registro.utilizado:
            return False, "O link de recuperação é inválido, expirou ou já foi utilizado.", None

        if token_registro.revogado:
            return False, "O link de recuperação é inválido, expirou ou já foi utilizado.", None

        agora = datetime.now(timezone.utc)
        # Garante timezone aware para comparação
        expira_em = token_registro.expira_em
        if expira_em.tzinfo is None:
            expira_em = expira_em.replace(tzinfo=timezone.utc)

        if agora > expira_em:
            return False, "O link de recuperação é inválido, expirou ou já foi utilizado.", None

        return True, "Token válido para redefinição de senha.", token_registro

    @staticmethod
    def redefinir_senha(
        token_bruto: str,
        nova_senha: str,
        ip_utilizacao: str,
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Executa a troca definitiva da credencial de acesso,
        invalidando o token e revogando sessões ativas do usuário.
        """
        valido, msg_erro, token_registro = PasswordRecoveryService.validar_token(token_bruto)
        if not valido or not token_registro:
            return False, msg_erro, None

        usuario = Database.buscar_usuario_por_id(token_registro.usuario_id)
        if not usuario:
            return False, "Usuário associado ao token não foi localizado.", None

        # Rejeita reuso da mesma senha anterior
        if verify_password(nova_senha, usuario.senha_hash):
            return False, "A nova senha não pode ser idêntica à senha atual utilizada.", usuario.id_usuario

        # Gera novo hash bcrypt e atualiza credencial (incrementando token_versao)
        novo_hash = hash_password(nova_senha)
        Database.atualizar_senha(usuario.id_usuario, novo_hash)

        # Consome o token para impedir qualquer reutilização
        agora = datetime.now(timezone.utc)
        Database.consumir_token(token_registro.id_token, ip_utilizacao, agora)

        return True, "Senha redefinida com sucesso. Faça login com suas novas credenciais.", usuario.id_usuario
