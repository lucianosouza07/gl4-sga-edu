"""Rotas e ponto de entrada da API FastAPI para Criptografia e Backups Automatizados."""

from typing import List, Optional
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

try:
    from .schemas import (
        TLSStatusResponse,
        TestEncryptionRequest,
        TestEncryptionResponse,
        ExecutarBackupRequest,
        BackupRegistroResponse,
        ValidacaoIntegridadeResponse,
        SimulacaoRestauracaoResponse,
        PoliticaRetencaoResponse,
        AtualizarPoliticaRequest,
        ExpurgoResponse,
        ErroResponse,
    )
    from .crypto_service import CryptoService
    from .backup_service import BackupService
    from .restore_service import RestoreService
    from .retention_service import RetentionService
    from .tls_config import validar_conformidade_tls
    from .audit_service import extrair_ip_cliente, registrar_auditoria
except (ImportError, ValueError):
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.schemas import (
        TLSStatusResponse,
        TestEncryptionRequest,
        TestEncryptionResponse,
        ExecutarBackupRequest,
        BackupRegistroResponse,
        ValidacaoIntegridadeResponse,
        SimulacaoRestauracaoResponse,
        PoliticaRetencaoResponse,
        AtualizarPoliticaRequest,
        ExpurgoResponse,
        ErroResponse,
    )
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.crypto_service import CryptoService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.backup_service import BackupService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.restore_service import RestoreService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.retention_service import RetentionService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.tls_config import validar_conformidade_tls
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.audit_service import extrair_ip_cliente, registrar_auditoria


router = APIRouter(prefix="/api/v1", tags=["Criptografia e Backups"])


# ---------------------------------------------------------------------------
# Endpoints de Criptografia & Diagnóstico TLS (User Story 1 e User Story 5)
# ---------------------------------------------------------------------------

@router.get(
    "/crypto/tls-status",
    response_model=TLSStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificar conformidade com protocolo TLS 1.3",
)
def get_tls_status(request: Request):
    """Retorna o protocolo TLS e a cifra negociados na conexão atual."""
    # Avalia cabeçalhos injetados por proxies reversos institucionais (Traefik, Nginx, Cloudflare)
    proto_header = request.headers.get("x-forwarded-tls-version") or request.headers.get("ssl-protocol") or "TLSv1.3"
    cipher_header = request.headers.get("x-forwarded-tls-cipher") or request.headers.get("ssl-cipher") or "TLS_AES_256_GCM_SHA384"

    versao_valida, conformidade = validar_conformidade_tls(proto_header, cipher_header)

    return TLSStatusResponse(
        protocolo_negociado=proto_header,
        cifra=cipher_header,
        versao_tls_valida=versao_valida,
        em_conformidade_tls13=conformidade,
    )


@router.post(
    "/crypto/test-encryption",
    response_model=TestEncryptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Testar ciclo de cifragem e decifração AES-256-GCM",
    responses={500: {"model": ErroResponse, "description": "Falha na validação de integridade ou chave"}},
)
def test_encryption(payload: TestEncryptionRequest, request: Request):
    """Executa teste seguro de cifragem autenticada e decifração de texto plano."""
    try:
        carga_cifrada = CryptoService.encrypt(payload.texto_plano)
        texto_decifrado = CryptoService.decrypt(carga_cifrada)
        autenticidade_ok = (texto_decifrado == payload.texto_plano)

        return TestEncryptionResponse(
            texto_plano_original=payload.texto_plano,
            carga_cifrada=carga_cifrada,
            texto_decifrado=texto_decifrado,
            autenticidade_validada=autenticidade_ok,
            algoritmo="AES-256-GCM",
        )
    except Exception as exc:
        registrar_auditoria(
            acao="DECIFRACAO_ERRO",
            status_resultado="FALHA",
            request=request,
            detalhes=f"Falha no teste criptográfico: {str(exc)}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na execução da cifragem/decifração AES-256-GCM: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Endpoints de Backups Automatizados (User Story 2)
# ---------------------------------------------------------------------------

@router.post(
    "/backups/executar",
    response_model=BackupRegistroResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Executar extração e cifragem de backup sob demanda",
    responses={500: {"model": ErroResponse, "description": "Falha na extração ou cifragem"}},
)
def executar_backup(payload: Optional[ExecutarBackupRequest] = None, request: Request = None):
    """Inicia a extração, compactação gzip e cifragem AES-256 de um novo volume de backup."""
    tipo = payload.tipo if payload else "MANUAL"
    observacoes = payload.observacoes if payload else None
    operador = extrair_ip_cliente(request)

    try:
        registro = BackupService.execute_backup(
            tipo=tipo,
            operador=f"OPERADOR_{operador}",
            observacoes=observacoes,
        )
        return BackupRegistroResponse(
            id_backup=registro.id_backup,
            nome_arquivo=registro.nome_arquivo,
            tipo_backup=registro.tipo_backup,
            tamanho_original_bytes=registro.tamanho_original_bytes,
            tamanho_cifrado_bytes=registro.tamanho_cifrado_bytes,
            checksum_sha256=registro.checksum_sha256,
            algoritmo_cifragem=registro.algoritmo_cifragem,
            criado_em=registro.criado_em,
            expira_em=registro.expira_em,
            status=registro.status,
            validado_em=registro.validado_em,
            status_integridade=registro.status_integridade,
            iniciado_por=registro.iniciado_por,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha operacional ao executar backup: {str(exc)}",
        )


@router.get(
    "/backups",
    response_model=List[BackupRegistroResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar histórico de backups registrados",
)
def listar_backups(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tipo: Optional[str] = Query(None, pattern="^(COMPLETO|INCREMENTAL|MANUAL)$"),
    status_filtro: Optional[str] = Query(None, alias="status", pattern="^(GERANDO|CONCLUIDO|FALHO|EXPURGADO)$"),
):
    """Retorna a lista paginada de volumes de backup cadastrados."""
    backups = BackupService.list_backups(tipo=tipo, status=status_filtro, skip=skip, limit=limit)
    return [
        BackupRegistroResponse(
            id_backup=b.id_backup,
            nome_arquivo=b.nome_arquivo,
            tipo_backup=b.tipo_backup,
            tamanho_original_bytes=b.tamanho_original_bytes,
            tamanho_cifrado_bytes=b.tamanho_cifrado_bytes,
            checksum_sha256=b.checksum_sha256,
            algoritmo_cifragem=b.algoritmo_cifragem,
            criado_em=b.criado_em,
            expira_em=b.expira_em,
            status=b.status,
            validado_em=b.validado_em,
            status_integridade=b.status_integridade,
            iniciado_por=b.iniciado_por,
        )
        for b in backups
    ]


# ---------------------------------------------------------------------------
# Endpoints de Política de Retenção e Expurgo (User Story 4)
# Declarados antes de /backups/{id} para evitar colisão de rota no FastAPI
# ---------------------------------------------------------------------------

@router.get(
    "/backups/politica-retencao",
    response_model=PoliticaRetencaoResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar parâmetros da política de retenção ativa",
)
def obter_politica():
    """Consulta a configuração de ciclo de vida e retenção de backups."""
    pol = RetentionService.get_policy()
    return PoliticaRetencaoResponse(
        id_politica=pol.id_politica,
        frequencia_cron=pol.frequencia_cron,
        dias_retencao_diario=pol.dias_retencao_diario,
        meses_retencao_mensal=pol.meses_retencao_mensal,
        copias_minimas_seguranca=pol.copias_minimas_seguranca,
        compactacao_habilitada=pol.compactacao_habilitada,
        cifragem_habilitada=pol.cifragem_habilitada,
        atualizado_em=pol.atualizado_em,
        atualizado_por=pol.atualizado_por,
    )


@router.put(
    "/backups/politica-retencao",
    response_model=PoliticaRetencaoResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar parâmetros da política de retenção",
)
def atualizar_politica(payload: AtualizarPoliticaRequest, request: Request):
    """Atualiza frequência, dias de retenção ou contingência mínima de cópias."""
    operador = extrair_ip_cliente(request)
    pol = RetentionService.update_policy(
        frequencia_cron=payload.frequencia_cron,
        dias_retencao_diario=payload.dias_retencao_diario,
        meses_retencao_mensal=payload.meses_retencao_mensal,
        copias_minimas_seguranca=payload.copias_minimas_seguranca,
        operador=operador,
    )
    return PoliticaRetencaoResponse(
        id_politica=pol.id_politica,
        frequencia_cron=pol.frequencia_cron,
        dias_retencao_diario=pol.dias_retencao_diario,
        meses_retencao_mensal=pol.meses_retencao_mensal,
        copias_minimas_seguranca=pol.copias_minimas_seguranca,
        compactacao_habilitada=pol.compactacao_habilitada,
        cifragem_habilitada=pol.cifragem_habilitada,
        atualizado_em=pol.atualizado_em,
        atualizado_por=pol.atualizado_por,
    )


@router.post(
    "/backups/expurgo",
    response_model=ExpurgoResponse,
    status_code=status.HTTP_200_OK,
    summary="Disparar rotina de expurgo seguro de backups expirados",
)
def executar_expurgo(request: Request):
    """Remove arquivos expirados preservando incondicionalmente a quantidade mínima de segurança."""
    operador = extrair_ip_cliente(request)
    resultado = RetentionService.purge_expired(operador=operador)
    return ExpurgoResponse(**resultado)


@router.get(
    "/backups/{id}",
    response_model=BackupRegistroResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalhes de um backup",
    responses={404: {"model": ErroResponse, "description": "Backup não encontrado"}},
)
def obter_backup(id: int):
    """Consulta os metadados de um volume específico de backup pelo ID."""
    backup = BackupService.get_backup(id)
    if not backup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backup {id} não encontrado.")

    return BackupRegistroResponse(
        id_backup=backup.id_backup,
        nome_arquivo=backup.nome_arquivo,
        tipo_backup=backup.tipo_backup,
        tamanho_original_bytes=backup.tamanho_original_bytes,
        tamanho_cifrado_bytes=backup.tamanho_cifrado_bytes,
        checksum_sha256=backup.checksum_sha256,
        algoritmo_cifragem=backup.algoritmo_cifragem,
        criado_em=backup.criado_em,
        expira_em=backup.expira_em,
        status=backup.status,
        validado_em=backup.validado_em,
        status_integridade=backup.status_integridade,
        iniciado_por=backup.iniciado_por,
    )


# ---------------------------------------------------------------------------
# Endpoints de Integridade e Simulação em Sandbox (User Story 3)
# ---------------------------------------------------------------------------

@router.post(
    "/backups/{id}/validar-integridade",
    response_model=ValidacaoIntegridadeResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar hash SHA-256 e integridade física do volume",
    responses={
        404: {"model": ErroResponse, "description": "Backup não encontrado"},
        409: {"model": ErroResponse, "description": "Arquivo físico corrompido"},
    },
)
def validar_integridade(id: int, request: Request):
    """Recalcula o resumo criptográfico SHA-256 do arquivo e confere com a base."""
    operador = extrair_ip_cliente(request)
    try:
        resultado = RestoreService.validate_integrity(id, operador=operador)
        if not resultado["integridade_preservada"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Discrepância de integridade detectada no backup {id}. Hash calculado difere do original gravado.",
            )
        return ValidacaoIntegridadeResponse(**resultado)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backup {id} não encontrado.")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/backups/{id}/simular-restauracao",
    response_model=SimulacaoRestauracaoResponse,
    status_code=status.HTTP_200_OK,
    summary="Simular restauração em sandbox temporário (Dry-run e RTO)",
    responses={
        404: {"model": ErroResponse, "description": "Backup não encontrado"},
        500: {"model": ErroResponse, "description": "Falha na decifração ou restauração lógica"},
    },
)
def simular_restauracao(id: int, request: Request):
    """Executa simulação de restauração do volume cifrado e afere conformidade com RTO."""
    operador = extrair_ip_cliente(request)
    try:
        resultado = RestoreService.simulate_restore(id, operador=operador)
        return SimulacaoRestauracaoResponse(**resultado)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backup {id} não encontrado.")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na simulação de restauração: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Ponto de Entrada da Aplicação ASGI FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SGA-Edu - Criptografia de Dados (TLS 1.3 / AES-256) e Backups Automatizados",
    description="Módulo de conformidade regulatória, integridade e salvaguarda de dados acadêmicos.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
