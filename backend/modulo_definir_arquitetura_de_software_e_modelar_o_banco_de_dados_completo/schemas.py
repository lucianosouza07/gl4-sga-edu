"""
Contratos Pydantic v2 para a Arquitetura de Software e Modelagem Completa do Banco de Dados (SGA-18).
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CamadaArquitetural(BaseModel):
    """Representa uma camada formal da arquitetura multicamadas do SGA-Edu."""

    id_camada: str = Field(..., min_length=2, max_length=50, description="Identificador único da camada")
    nome: str = Field(..., min_length=3, max_length=120, description="Nome descritivo da camada arquitetural")
    diretorio_base: str = Field(..., min_length=2, max_length=160, description="Diretório raiz da camada no repositório")
    tecnologias: List[str] = Field(..., min_length=1, description="Tecnologias e frameworks adotados na camada")
    responsabilidades: List[str] = Field(..., min_length=1, description="Responsabilidades técnicas e funcionais")
    protocolo_comunicacao: str = Field(..., min_length=2, max_length=120, description="Protocolo ou contrato de fronteira")

    @field_validator("id_camada", "nome", "diretorio_base", "protocolo_comunicacao")
    @classmethod
    def validar_texto_nao_vazio(cls, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("O campo textual da camada arquitetural não pode ser vazio.")
        return limpo


class DominioBancoDados(BaseModel):
    """Representa um domínio funcional do esquema relacional completo."""

    codigo: str = Field(..., min_length=2, max_length=50, description="Código identificador do domínio")
    nome: str = Field(..., min_length=3, max_length=120, description="Nome do domínio funcional")
    descricao: str = Field(..., min_length=10, max_length=400, description="Objetivo funcional e regulatório do domínio")
    tabelas: List[str] = Field(..., min_length=1, description="Tabelas pertencentes ao domínio")


class EspecificacaoColuna(BaseModel):
    """Descreve uma coluna de uma tabela relacional."""

    nome: str = Field(..., min_length=1, max_length=80)
    tipo_sql: str = Field(..., min_length=2, max_length=60)
    obrigatoria: bool = Field(default=True)
    chave_primaria: bool = Field(default=False)
    unica: bool = Field(default=False)
    valor_padrao: Optional[str] = Field(default=None)


class EspecificacaoChaveEstrangeira(BaseModel):
    """Descreve uma chave estrangeira e suas políticas de integridade referencial."""

    coluna_origem: str = Field(..., min_length=1, max_length=80)
    tabela_destino: str = Field(..., min_length=1, max_length=80)
    coluna_destino: str = Field(..., min_length=1, max_length=80)
    on_delete: str = Field(..., pattern=r"^(RESTRICT|CASCADE|SET NULL|NO ACTION)$")
    on_update: str = Field(..., pattern=r"^(RESTRICT|CASCADE|SET NULL|NO ACTION)$")


class EspecificacaoTabela(BaseModel):
    """Metadados completos de uma entidade relacional do banco de dados do SGA-Edu."""

    nome_tabela: str = Field(..., min_length=2, max_length=80)
    dominio: str = Field(..., min_length=2, max_length=50)
    descricao: str = Field(..., min_length=5, max_length=300)
    chave_primaria: str = Field(..., min_length=1, max_length=80)
    colunas: List[EspecificacaoColuna] = Field(..., min_length=1)
    chaves_estrangeiras: List[EspecificacaoChaveEstrangeira] = Field(default_factory=list)
    indices: List[str] = Field(default_factory=list)


class RelatorioIntegridadeSchema(BaseModel):
    """Resultado da verificação executável do esquema completo e carga inicial."""

    sucesso: bool
    total_dominios: int = Field(..., ge=1)
    total_tabelas_esperadas: int = Field(..., ge=1)
    total_tabelas_criadas: int = Field(..., ge=0)
    perfis_rbac_carregados: int = Field(..., ge=0)
    chaves_estrangeiras_ativas: bool
    total_chaves_estrangeiras_verificadas: int = Field(..., ge=0)
    total_indices_verificados: int = Field(..., ge=0)
    violacoes_integridade: List[str] = Field(default_factory=list)


class ResumoArquiteturaSGA(BaseModel):
    """Visão consolidada da arquitetura de software e modelagem do banco de dados do SGA-Edu."""

    sistema: str = Field(default="SGA-Edu")
    tarefa_backlog: str = Field(default="SGA-18")
    padrao_arquitetural: str
    camadas: List[CamadaArquitetural]
    dominios_banco_dados: List[DominioBancoDados]
    total_dominios: int
    total_tabelas: int
    conformidade_regulatoria: List[str]
