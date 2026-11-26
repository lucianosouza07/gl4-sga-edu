"""Endpoints REST FastAPI para emissão de diários operacionais, atas de nota e diplomas digitais (SGA-25)."""

from typing import Optional
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status

try:
    from .audit_service import extrair_ip_origem
    from .repository import DocumentoRepository, get_repository
    from .schemas import (
        AtaNotasEntrada,
        DiarioOperacionalEntrada,
        DiplomaDigitalEntrada,
        DocumentoAcademicoResposta,
        DocumentoAcademicoResumo,
        EventoAuditoriaResposta,
        RevogacaoDocumentoEntrada,
        TipoDocumentoEnum,
        ValidacaoPublicaResposta,
        VerificacaoIntegridadeResposta,
    )
    from .security import OperadorAutenticado, require_secretaria_ou_admin
    from .service import DocumentoService
except ImportError:
    from audit_service import extrair_ip_origem
    from repository import DocumentoRepository, get_repository
    from schemas import (
        AtaNotasEntrada,
        DiarioOperacionalEntrada,
        DiplomaDigitalEntrada,
        DocumentoAcademicoResposta,
        DocumentoAcademicoResumo,
        EventoAuditoriaResposta,
        RevogacaoDocumentoEntrada,
        TipoDocumentoEnum,
        ValidacaoPublicaResposta,
        VerificacaoIntegridadeResposta,
    )
    from security import OperadorAutenticado, require_secretaria_ou_admin
    from service import DocumentoService

router = APIRouter(
    prefix="/api/documentos",
    tags=["Emissão de Diários, Atas de Nota e Diplomas Digitais (SGA-25)"],
)


def get_service(repo: DocumentoRepository = Depends(get_repository)) -> DocumentoService:
    return DocumentoService(repo)


@router.post(
    "/diarios-operacionais",
    response_model=DocumentoAcademicoResposta,
    status_code=status.HTTP_201_CREATED,
)
def emitir_diario_operacional(
    entrada: DiarioOperacionalEntrada,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: DocumentoService = Depends(get_service),
) -> DocumentoAcademicoResposta:
    """Emite Diário Operacional oficial de uma turma com custódia MEC e trilha de auditoria."""
    resultado = service.emitir_diario_operacional(
        entrada=entrada,
        operador=operador,
        ip_origem=extrair_ip_origem(request),
    )
    return DocumentoAcademicoResposta(**resultado)


@router.post(
    "/atas-notas",
    response_model=DocumentoAcademicoResposta,
    status_code=status.HTTP_201_CREATED,
)
def emitir_ata_notas(
    entrada: AtaNotasEntrada,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: DocumentoService = Depends(get_service),
) -> DocumentoAcademicoResposta:
    """Emite Ata de Notas Finais consolidada de uma turma com regra de 25% de faltas e custódia MEC."""
    resultado = service.emitir_ata_notas(
        entrada=entrada,
        operador=operador,
        ip_origem=extrair_ip_origem(request),
    )
    return DocumentoAcademicoResposta(**resultado)


@router.post(
    "/diplomas",
    response_model=DocumentoAcademicoResposta,
    status_code=status.HTTP_201_CREATED,
)
def emitir_diploma_digital(
    entrada: DiplomaDigitalEntrada,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: DocumentoService = Depends(get_service),
) -> DocumentoAcademicoResposta:
    """Emite Diploma Digital de conclusão de curso com validação de elegibilidade e custódia MEC."""
    resultado = service.emitir_diploma_digital(
        entrada=entrada,
        operador=operador,
        ip_origem=extrair_ip_origem(request),
    )
    return DocumentoAcademicoResposta(**resultado)


@router.get(
    "/validar/{codigo_verificacao}",
    response_model=ValidacaoPublicaResposta,
    status_code=status.HTTP_200_OK,
)
def validar_documento_publico(
    codigo_verificacao: str,
    service: DocumentoService = Depends(get_service),
) -> ValidacaoPublicaResposta:
    """Consulta pública (sem autenticação) de autenticidade por código verificador ou QR Code (LGPD)."""
    resultado = service.validar_documento_publico(codigo_verificacao)
    return ValidacaoPublicaResposta(**resultado)


@router.get(
    "/auditoria",
    response_model=list[EventoAuditoriaResposta],
    status_code=status.HTTP_200_OK,
)
def listar_auditoria(
    id_documento: Optional[str] = Query(default=None, description="Filtra eventos pelo ID do documento."),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: DocumentoService = Depends(get_service),
) -> list[EventoAuditoriaResposta]:
    """Consulta a trilha de auditoria institucional do módulo (restrito a Secretaria/Admin)."""
    eventos = service.listar_auditoria(id_documento=id_documento)
    return [EventoAuditoriaResposta(**ev) for ev in eventos]


@router.get(
    "",
    response_model=list[DocumentoAcademicoResumo],
    status_code=status.HTTP_200_OK,
)
def listar_documentos(
    tipo_documento: Optional[TipoDocumentoEnum] = Query(default=None),
    aluno_matricula: Optional[int] = Query(default=None, gt=0),
    turma_id: Optional[int] = Query(default=None, gt=0),
    periodo_letivo_codigo: Optional[str] = Query(default=None),
    valido: Optional[bool] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: DocumentoService = Depends(get_service),
) -> list[DocumentoAcademicoResumo]:
    """Lista documentos acadêmicos emitidos com filtros administrativos."""
    itens = service.listar_documentos(
        tipo_documento=tipo_documento.value if tipo_documento else None,
        aluno_matricula=aluno_matricula,
        turma_id=turma_id,
        periodo_letivo_codigo=periodo_letivo_codigo,
        valido=valido,
    )
    return [DocumentoAcademicoResumo(**item) for item in itens]


@router.get(
    "/{id_documento}",
    response_model=DocumentoAcademicoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_documento(
    id_documento: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: DocumentoService = Depends(get_service),
) -> DocumentoAcademicoResposta:
    """Detalha um documento acadêmico emitido e seu registro 1:1 no Acervo Digital MEC."""
    resultado = service.obter_documento(id_documento)
    return DocumentoAcademicoResposta(**resultado)


@router.post(
    "/{id_documento}/verificar-integridade",
    response_model=VerificacaoIntegridadeResposta,
    status_code=status.HTTP_200_OK,
)
def verificar_integridade(
    id_documento: int,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: DocumentoService = Depends(get_service),
) -> VerificacaoIntegridadeResposta:
    """Recalcula SHA-256 e verifica assinatura ICP-Brasil de documento custodiado no Acervo MEC."""
    resultado = service.verificar_integridade_documento(
        id_documento=id_documento,
        operador=operador,
        ip_origem=extrair_ip_origem(request),
    )
    return VerificacaoIntegridadeResposta(**resultado)


@router.patch(
    "/{id_documento}/revogar",
    response_model=DocumentoAcademicoResposta,
    status_code=status.HTTP_200_OK,
)
def revogar_documento(
    id_documento: int,
    entrada: RevogacaoDocumentoEntrada,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: DocumentoService = Depends(get_service),
) -> DocumentoAcademicoResposta:
    """Revoga/invalida um documento emitido mediante justificativa obrigatória sem exclusão física."""
    resultado = service.revogar_documento(
        id_documento=id_documento,
        entrada=entrada,
        operador=operador,
        ip_origem=extrair_ip_origem(request),
    )
    return DocumentoAcademicoResposta(**resultado)


@router.delete(
    "/{id_documento}",
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
)
def bloquear_exclusao_documento(
    id_documento: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
) -> None:
    """Impede exclusão física de documentos oficiais para cumprir a guarda permanente do MEC."""
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=(
            f"Exclusão física do documento {id_documento} e registros do Acervo Digital MEC é "
            f"proibida pela guarda permanente (Portarias MEC nº 315/2018 e nº 360/2022). "
            f"Utilize a operação de revogação."
        ),
    )


app = FastAPI(
    title="SGA-Edu | Módulo Emissão de Diários, Atas de Nota e Diplomas Digitais (SGA-25)",
    version="1.0.0",
)
app.include_router(router)


@app.get("/")
def raiz() -> dict[str, str]:
    return {
        "status": "Módulo SGA-25 operacional",
        "prefixo": "/api/documentos",
        "docs": "/docs",
    }
