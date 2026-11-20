"""Testes unitários para o serviço de Criptografia Simétrica Autenticada AES-256-GCM."""

import base64
import os
import pytest
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.crypto_service import CryptoService


def test_encrypt_decrypt_success():
    """Valida o ciclo completo de cifragem e decifração de dados sensíveis."""
    texto_original = "Discente: Maria Silva - CPF: 123.456.789-00 - Matrícula: 20261001"
    carga_cifrada = CryptoService.encrypt(texto_original)

    assert carga_cifrada.startswith("v1:aes-256-gcm:")
    partes = carga_cifrada.split(":")
    assert len(partes) == 5

    texto_recuperado = CryptoService.decrypt(carga_cifrada)
    assert texto_recuperado == texto_original


def test_nonce_uniqueness():
    """Valida que duas cifragens do mesmo texto plano geram nonces e cargas diferentes."""
    texto = "Informação Confidencial Acadêmica"
    cifrado_1 = CryptoService.encrypt(texto)
    cifrado_2 = CryptoService.encrypt(texto)

    assert cifrado_1 != cifrado_2
    nonce_1 = cifrado_1.split(":")[2]
    nonce_2 = cifrado_2.split(":")[2]
    assert nonce_1 != nonce_2


def test_tampering_detection_ciphertext():
    """Valida que qualquer alteração de bits nos dados cifrados dispara erro de autenticação."""
    texto = "Dado Sensível Protegido pela LGPD"
    cifrado = CryptoService.encrypt(texto)
    partes = cifrado.split(":")

    ct_bytes = bytearray(base64.b64decode(partes[3]))
    ct_bytes[0] ^= 0x01
    ct_adulterado = base64.b64encode(ct_bytes).decode("utf-8")
    cifrado_corrompido = f"{partes[0]}:{partes[1]}:{partes[2]}:{ct_adulterado}:{partes[4]}"

    with pytest.raises(ValueError, match="Falha na validação de integridade"):
        CryptoService.decrypt(cifrado_corrompido)


def test_tampering_detection_tag():
    """Valida que adulteração na tag de autenticação rejeita a decifração."""
    texto = "Dado Sensível"
    cifrado = CryptoService.encrypt(texto)
    partes = cifrado.split(":")

    tag_bytes = bytearray(base64.b64decode(partes[4]))
    tag_bytes[0] ^= 0x01
    tag_adulterada = base64.b64encode(tag_bytes).decode("utf-8")
    cifrado_tag_invalida = f"{partes[0]}:{partes[1]}:{partes[2]}:{partes[3]}:{tag_adulterada}"

    with pytest.raises(ValueError, match="Falha na validação de integridade"):
        CryptoService.decrypt(cifrado_tag_invalida)


def test_wrong_key_fails_decryption():
    """Valida que decifrar com chave divergente rejeita a operação."""
    texto = "Informação Restrita"
    chave_a = "chave_institucional_a_32bytes_!"
    chave_b = "chave_institucional_b_32bytes_!"

    cifrado = CryptoService.encrypt(texto, explicit_key=chave_a)

    with pytest.raises(ValueError, match="Falha na validação de integridade"):
        CryptoService.decrypt(cifrado, explicit_key=chave_b)


def test_bytes_encryption_and_decryption(tmp_path):
    """Valida cifragem e decifração de blocos binários de arquivos."""
    conteudo_binario = b"SQL DUMP DE TESTE COM CARACTERES ESPECIAIS \x00\xff\xfe\x01\x10\x99"
    cifrado_bytes = CryptoService.encrypt_bytes(conteudo_binario)

    assert len(cifrado_bytes) > len(conteudo_binario)
    assert cifrado_bytes != conteudo_binario

    recuperado_bytes = CryptoService.decrypt_bytes(cifrado_bytes)
    assert recuperado_bytes == conteudo_binario


def test_compute_sha256(tmp_path):
    """Valida o cálculo exato do hash SHA-256 em arquivos."""
    arquivo_teste = tmp_path / "teste_hash.txt"
    arquivo_teste.write_text("SGA-Edu SHA256 Verification Test", encoding="utf-8")

    checksum = CryptoService.compute_sha256(str(arquivo_teste))
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)
