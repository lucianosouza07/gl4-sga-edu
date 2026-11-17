"""Serviço de envio de e-mails transacionais para recuperação de credenciais."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmailMensagem:
    destinatario: str
    assunto: str
    corpo_texto: str
    token: str


class EmailServiceInterface(ABC):
    """Contrato abstrato para o provedor de mensageria eletrônica."""

    @abstractmethod
    def enviar_email_recuperacao(self, destinatario: str, token: str) -> bool:
        """Despacha a mensagem contendo o link de redefinição com token de uso único."""
        pass


class MockEmailService(EmailServiceInterface):
    """Implementação em memória para testes automatizados e desenvolvimento local."""

    def __init__(self):
        self.mensagens_enviadas: List[EmailMensagem] = []

    def enviar_email_recuperacao(self, destinatario: str, token: str) -> bool:
        assunto = "SGA-EDU - Recuperação de Senha de Acesso"
        corpo = (
            f"Olá,\n\n"
            f"Recebemos uma solicitação para redefinir sua senha de acesso no SGA-EDU.\n"
            f"Para prosseguir, utilize o link abaixo ou o código de autorização:\n\n"
            f"http://localhost:3000/redefinir-senha?token={token}\n\n"
            f"Este link é válido por 30 minutos e de uso único.\n"
            f"Se você não solicitou esta alteração, ignore esta mensagem com segurança."
        )
        self.mensagens_enviadas.append(
            EmailMensagem(
                destinatario=destinatario,
                assunto=assunto,
                corpo_texto=corpo,
                token=token,
            )
        )
        return True

    def limpar(self):
        self.mensagens_enviadas.clear()


# Instância padrão utilizada no backend
_email_service_instance: EmailServiceInterface = MockEmailService()


def get_email_service() -> EmailServiceInterface:
    """Dependency provider do FastAPI para injeção do serviço de e-mail."""
    return _email_service_instance


def set_email_service(service: EmailServiceInterface):
    global _email_service_instance
    _email_service_instance = service
