"""Configuração e imposição de segurança do protocolo TLS 1.3 para dados em trânsito."""

import ssl
from typing import Optional, Tuple


# Suites de cifras modernas exigidas pelo padrão TLS 1.3
CIPHERS_TLS13 = [
    "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256",
    "TLS_AES_128_GCM_SHA256",
]

CIPHERS_TLS13_STRING = ":".join(CIPHERS_TLS13)


def create_tls13_context(certfile: Optional[str] = None, keyfile: Optional[str] = None) -> ssl.SSLContext:
    """Cria e configura um contexto SSL estritamente restrito ao protocolo TLS 1.3."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Imposição compulsória de TLS 1.3 (bloqueia TLS 1.0, 1.1 e 1.2)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    # Opções adicionais de endurecimento de segurança
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    context.options |= ssl.OP_NO_TLSv1_2
    context.options |= ssl.OP_SINGLE_ECDH_USE

    if certfile and keyfile:
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    return context


def validar_conformidade_tls(
    protocolo_negociado: Optional[str],
    cifra: Optional[str] = None,
) -> Tuple[bool, bool]:
    """Verifica se uma conexão de rede atende aos requisitos institucionais de TLS 1.3.

    Retorna:
        Tuple[bool, bool]: (versao_tls_valida, em_conformidade_tls13)
    """
    if not protocolo_negociado:
        return False, False

    proto_upper = protocolo_negociado.strip().upper()

    # TLS 1.3 confere conformidade integral
    if "TLSV1.3" in proto_upper or "TLSV1_3" in proto_upper:
        return True, True

    # TLS 1.2 é versão válida pelo padrão SSL legado, porém não atende ao requisito estrito de TLS 1.3
    if "TLSV1.2" in proto_upper or "TLSV1_2" in proto_upper:
        return True, False

    # Rejeita versões inseguras e legadas (SSLv2, SSLv3, TLS 1.0, TLS 1.1)
    return False, False
