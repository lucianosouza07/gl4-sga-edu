"""Serviço de Criptografia Simétrica Autenticada AES-256-GCM para Dados em Repouso."""

import base64
import hashlib
import os
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoService:
    """Implementa cifragem e decifração autenticada utilizando AES-256-GCM (AEAD)."""

    FORMATO_PREFIXO = "v1:aes-256-gcm"

    @classmethod
    def get_master_key(cls, explicit_key: Optional[str] = None) -> bytes:
        """Obtém a chave mestra de 256 bits (32 bytes) a partir do ambiente ou parâmetro."""
        raw_key = explicit_key or os.getenv("CRYPTO_MASTER_KEY", "sga_edu_master_aes_256_key_32bytes_sec!")
        if isinstance(raw_key, str):
            key_bytes = raw_key.encode("utf-8")
        else:
            key_bytes = raw_key

        # Garante exatos 32 bytes (256 bits) por meio de derivação SHA-256 se o tamanho diferir
        if len(key_bytes) != 32:
            key_bytes = hashlib.sha256(key_bytes).digest()

        return key_bytes

    @classmethod
    def encrypt(cls, plaintext: str, explicit_key: Optional[str] = None) -> str:
        """Criptografa texto plano com AES-256-GCM, gerando nonce aleatório e tag de integridade."""
        if plaintext is None:
            raise ValueError("O texto plano para cifragem não pode ser nulo.")

        key = cls.get_master_key(explicit_key)
        aesgcm = AESGCM(key)

        # Vetor de inicialização de 96 bits (12 bytes) exclusivo por operação
        nonce = os.urandom(12)
        plaintext_bytes = plaintext.encode("utf-8")

        # Cifragem com geração de autenticação integrada
        ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext_bytes, None)
        ciphertext = ciphertext_and_tag[:-16]
        tag = ciphertext_and_tag[-16:]

        nonce_b64 = base64.b64encode(nonce).decode("utf-8")
        ciphertext_b64 = base64.b64encode(ciphertext).decode("utf-8")
        tag_b64 = base64.b64encode(tag).decode("utf-8")

        return f"{cls.FORMATO_PREFIXO}:{nonce_b64}:{ciphertext_b64}:{tag_b64}"

    @classmethod
    def decrypt(cls, encrypted_payload: str, explicit_key: Optional[str] = None) -> str:
        """Decifra carga criptografada validando estritamente autenticidade e integridade."""
        if not encrypted_payload or not isinstance(encrypted_payload, str):
            raise ValueError("Carga criptografada inválida ou vazia.")

        parts = encrypted_payload.split(":")
        if len(parts) != 5 or f"{parts[0]}:{parts[1]}" != cls.FORMATO_PREFIXO:
            raise ValueError(f"Formato de carga criptográfica não suportado. Esperado {cls.FORMATO_PREFIXO}:nonce:dado:tag")

        try:
            nonce = base64.b64decode(parts[2])
            ciphertext = base64.b64decode(parts[3])
            tag = base64.b64decode(parts[4])
        except Exception as exc:
            raise ValueError(f"Falha ao decodificar componentes em base64: {str(exc)}") from exc

        if len(nonce) != 12:
            raise ValueError("Tamanho de nonce inválido para AES-256-GCM (esperado 12 bytes).")
        if len(tag) != 16:
            raise ValueError("Tamanho de tag de autenticação inválido (esperado 16 bytes).")

        key = cls.get_master_key(explicit_key)
        aesgcm = AESGCM(key)
        ciphertext_and_tag = ciphertext + tag

        try:
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext_and_tag, None)
            return decrypted_bytes.decode("utf-8")
        except Exception as exc:
            raise ValueError("Falha na validação de integridade ou autenticidade dos dados cifrados (tag inválida ou chave incorreta).") from exc

    @classmethod
    def encrypt_bytes(cls, data: bytes, explicit_key: Optional[str] = None) -> bytes:
        """Criptografa bytes de arquivos em streaming/bloco com nonce e tag concatenados."""
        key = cls.get_master_key(explicit_key)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext_and_tag = aesgcm.encrypt(nonce, data, None)
        # Prefixo de 12 bytes com o nonce + dados cifrados + tag
        return nonce + ciphertext_and_tag

    @classmethod
    def decrypt_bytes(cls, encrypted_bytes: bytes, explicit_key: Optional[str] = None) -> bytes:
        """Decifra bytes concatenados (nonce de 12 bytes + ciphertext + tag de 16 bytes)."""
        if len(encrypted_bytes) < 28:
            raise ValueError("Arquivo ou volume cifrado corrompido: tamanho menor que cabeçalho criptográfico mínimo.")

        nonce = encrypted_bytes[:12]
        ciphertext_and_tag = encrypted_bytes[12:]
        key = cls.get_master_key(explicit_key)
        aesgcm = AESGCM(key)

        try:
            return aesgcm.decrypt(nonce, ciphertext_and_tag, None)
        except Exception as exc:
            raise ValueError("Falha na decifração de bytes: autenticação falhou ou volume corrompido.") from exc

    @classmethod
    def compute_sha256(cls, file_path: str) -> str:
        """Calcula o resumo criptográfico SHA-256 de um arquivo físico no disco."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
