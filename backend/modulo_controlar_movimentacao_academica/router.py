from typing import List
from fastapi import APIRouter, status

try:
    from schemas import (
        CertidaoResponse,
        DiscenteCreate,
        DiscenteResponse,
        MovimentacaoResponse,
        TrancamentoRequest,
        DestrancamentoRequest,
        TransferenciaRequest,
        CancelamentoRequest,
        JubilamentoRequest,
    )
    from services import servico_movimentacao
except ImportError:
    from .schemas import (
        CertidaoResponse,
        DiscenteCreate,
        DiscenteResponse,
        MovimentacaoResponse,
        TrancamentoRequest,
        DestrancamentoRequest,
        TransferenciaRequest,
        CancelamentoRequest,
        JubilamentoRequest,
    )
    from .services import servico_movimentacao

router = APIRouter(prefix="/api/movimentacao", tags=["Movimentação Acadêmica"])


@router.post("/discentes", response_model=DiscenteResponse, status_code=status.HTTP_201_CREATED)
def criar_discente(dados: DiscenteCreate):
    return servico_movimentacao.criar_discente(dados)


@router.get("/discentes", response_model=List[DiscenteResponse])
def listar_discentes():
    return servico_movimentacao.listar_discentes()


@router.get("/discentes/{discente_id}", response_model=DiscenteResponse)
def obter_discente(discente_id: str):
    return servico_movimentacao.obter_discente(discente_id)


@router.post("/trancamento", response_model=MovimentacaoResponse)
def solicitar_trancamento(req: TrancamentoRequest):
    return servico_movimentacao.solicitar_trancamento(req)


@router.post("/destrancamento", response_model=MovimentacaoResponse)
def homologar_destrancamento(req: DestrancamentoRequest):
    return servico_movimentacao.homologar_destrancamento(req)


@router.post("/transferencia", response_model=MovimentacaoResponse)
def homologar_transferencia(req: TransferenciaRequest):
    return servico_movimentacao.homologar_transferencia(req)


@router.post("/cancelamento", response_model=MovimentacaoResponse)
def homologar_cancelamento(req: CancelamentoRequest):
    return servico_movimentacao.homologar_cancelamento(req)


@router.post("/jubilamento", response_model=MovimentacaoResponse)
def homologar_jubilamento(req: JubilamentoRequest):
    return servico_movimentacao.homologar_jubilamento(req)


@router.get("/historico/{discente_id}", response_model=List[MovimentacaoResponse])
def listar_historico_discente(discente_id: str):
    return servico_movimentacao.listar_historico_discente(discente_id)


@router.get("/certidao/{movimentacao_id}", response_model=CertidaoResponse)
def emitir_certidao(movimentacao_id: str):
    return servico_movimentacao.emitir_certidao(movimentacao_id)
