"""Mecanismo de controle de taxa (Rate Limiting) em memória para mitigar abusos."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List


class InMemoryRateLimiter:
    """Controlador de frequência de requisições por chave de identificação (IP ou e-mail)."""

    def __init__(self, limite_maximo: int = 5, janela_segundos: int = 300):
        self.limite_maximo = limite_maximo
        self.janela_segundos = janela_segundos
        self.registros: Dict[str, List[datetime]] = defaultdict(list)

    def is_allowed(self, chave: str) -> bool:
        agora = datetime.now(timezone.utc)
        limite_tempo = agora - timedelta(seconds=self.janela_segundos)

        # Filtra registros anteriores à janela de tempo
        timestamps = [t for t in self.registros[chave] if t > limite_tempo]
        self.registros[chave] = timestamps

        if len(timestamps) >= self.limite_maximo:
            return False

        self.registros[chave].append(agora)
        return True

    def reset(self):
        self.registros.clear()


# Instância global para proteção das rotas de recuperação
solicitacao_rate_limiter = InMemoryRateLimiter(limite_maximo=5, janela_segundos=300)
