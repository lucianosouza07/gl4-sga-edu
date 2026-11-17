"""
Motor de inicialização, catálogo arquitetural e validação de integridade do banco de dados completo do SGA-Edu (SGA-18).
"""

from pathlib import Path
import re
import sqlite3
from typing import Dict, List, Optional

from .schemas import (
    CamadaArquitetural,
    DominioBancoDados,
    EspecificacaoChaveEstrangeira,
    EspecificacaoColuna,
    EspecificacaoTabela,
    RelatorioIntegridadeSchema,
    ResumoArquiteturaSGA,
)

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_DDL_PATH = BASE_DIR / "schema_completo_ddl.sql"
SEED_DML_PATH = BASE_DIR / "seed_inicial.sql"

CAMADAS_ARQUITETURA: List[CamadaArquitetural] = [
    CamadaArquitetural(
        id_camada="apresentacao-spa",
        nome="Apresentação (Cliente SPA)",
        diretorio_base="src/frontend",
        tecnologias=["React 18", "TypeScript 5", "Vite 6", "CSS Modular / Design Tokens"],
        responsabilidades=[
            "Renderização de dashboards e visões segmentadas pelos 5 perfis RBAC",
            "Validação em cliente e mascaramento de dados sensíveis (CPF/Telefone)",
            "Comunicação HTTP desacoplada via adaptador centralizado (api.ts) com timeout e fallback",
        ],
        protocolo_comunicacao="HTTPS / JSON REST sobre TLS 1.3 (Porta 8000 em desenvolvimento)",
    ),
    CamadaArquitetural(
        id_camada="aplicacao-api-rest",
        nome="Aplicação e Domínio (Servidor API RESTful)",
        diretorio_base="src/backend",
        tecnologias=["Python 3.11+", "FastAPI", "Pydantic v2", "Uvicorn ASGI"],
        responsabilidades=[
            "Roteamento modular por domínio funcional (APIRouter)",
            "Validação declarativa de payloads de entrada e saída com Pydantic v2",
            "Aplicação de autenticação, controle de acesso RBAC, recuperação de senha e trilha de auditoria",
            "Regras pedagógicas de pré-requisitos, choque de horário, cálculo de médias, frequência e cobrança",
        ],
        protocolo_comunicacao="Contratos Pydantic / SQL Parametrizado com Transações ACID",
    ),
    CamadaArquitetural(
        id_camada="persistencia-relacional",
        nome="Persistência e Modelagem Relacional",
        diretorio_base="src/backend/modulo_definir_arquitetura_de_software_e_modelar_o_banco_de_dados_completo",
        tecnologias=["MySQL 8.0+ (InnoDB / utf8mb4)", "SQLite 3 (PRAGMA foreign_keys = ON)"],
        responsabilidades=[
            "Guarda transacional íntegra das 33 entidades distribuídas nos 6 domínios do SGA-Edu",
            "Imposição de integridade referencial (RESTRICT, CASCADE, SET NULL), unicidade e checks de domínio",
            "Custódia de trilhas de auditoria LGPD e do Acervo Acadêmico Digital (Portarias MEC 315/2018 e 360/2022)",
        ],
        protocolo_comunicacao="DDL/DML Relacional com Chaves Estrangeiras e Índices Secundários",
    ),
]

DOMINIOS_BANCO_DADOS: List[DominioBancoDados] = [
    DominioBancoDados(
        codigo="identidade_rbac_lgpd",
        nome="1. Identidade, RBAC, Segurança e LGPD",
        descricao="Gerencia perfis de acesso, contas de usuários, especializações de atores, recuperação de senha, consentimento LGPD e auditoria.",
        tabelas=[
            "Perfil",
            "Usuario",
            "Aluno",
            "Professor",
            "FuncionarioAdministrativo",
            "TokenRecuperacao",
            "LogAuditoriaRecuperacao",
            "TermoConsentimentoLGPD",
            "LogAuditoriaSistema",
        ],
    ),
    DominioBancoDados(
        codigo="estrutura_curricular",
        nome="2. Estrutura Acadêmica e Matriz Curricular",
        descricao="Modela departamentos, cursos, matrizes curriculares (PPC), disciplinas, pré-requisitos, correquisitos e equivalências.",
        tabelas=[
            "Departamento",
            "Curso",
            "MatrizCurricular",
            "Disciplina",
            "PreRequisito",
            "EquivalenciaDisciplina",
        ],
    ),
    DominioBancoDados(
        codigo="planejamento_turmas",
        nome="3. Planejamento Letivo, Salas e Turmas",
        descricao="Estrutura o calendário de períodos letivos, espaços físicos/virtuais, oferta de turmas, vagas e horários de aula.",
        tabelas=[
            "PeriodoLetivo",
            "Sala",
            "Turma",
            "HorarioTurma",
        ],
    ),
    DominioBancoDados(
        codigo="vida_academica_diario",
        nome="4. Vida Acadêmica, Diário de Classe e Movimentação",
        descricao="Registra matrículas em turmas, avaliações/notas, frequência por aula, plano de ensino, materiais, comunicados, movimentações e requerimentos.",
        tabelas=[
            "MatriculaTurma",
            "AvaliacaoNota",
            "RegistroFrequencia",
            "PlanoEnsino",
            "MaterialAula",
            "ComunicadoTurma",
            "MovimentacaoAcademica",
            "RequerimentoAcademico",
        ],
    ),
    DominioBancoDados(
        codigo="gestao_financeira",
        nome="5. Gestão Financeira Integrada",
        descricao="Controla contratos educacionais semestrais, bolsas/descontos, cobranças de mensalidades (boleto/Pix) e conciliação de pagamentos.",
        tabelas=[
            "ContratoFinanceiro",
            "BolsaDesconto",
            "CobrancaMensalidade",
            "PagamentoConciliacao",
        ],
    ),
    DominioBancoDados(
        codigo="acervo_digital_mec",
        nome="6. Emissão Digital e Acervo Regulatório MEC",
        descricao="Garante a expedição de documentos acadêmicos com QR Code/SHA-256 e guarda permanente conforme Portarias MEC 315/2018 e 360/2022.",
        tabelas=[
            "DocumentoAcademico",
            "AcervoDigitalMEC",
        ],
    ),
]

DESCRICOES_TABELAS: Dict[str, str] = {
    "Perfil": "Papéis de controle de acesso RBAC (Aluno, Professor, Secretaria, Financeiro, Admin).",
    "Usuario": "Identidade central de autenticação, credenciais hash, MFA e status de conta.",
    "Aluno": "Especialização cadastral e acadêmica do corpo discente.",
    "Professor": "Especialização cadastral e funcional do corpo docente.",
    "FuncionarioAdministrativo": "Especialização de servidores da secretaria, setor financeiro e TI.",
    "TokenRecuperacao": "Tokens temporários com hash SHA-256 para redefinição segura de senha.",
    "LogAuditoriaRecuperacao": "Trilha de auditoria específica dos eventos de recuperação de credenciais.",
    "TermoConsentimentoLGPD": "Registro de aceite e revogação de termos de privacidade (LGPD).",
    "LogAuditoriaSistema": "Trilha de auditoria institucional para operações críticas em qualquer módulo.",
    "Departamento": "Unidades e departamentos acadêmicos aos quais cursos e docentes se vinculam.",
    "Curso": "Cursos de graduação e pós-graduação reconhecidos pelo MEC.",
    "MatrizCurricular": "Grades curriculares versionadas por ano e semestre de vigência.",
    "Disciplina": "Componentes curriculares com carga horária, créditos e semestre ideal.",
    "PreRequisito": "Regras de pré-requisito e correquisito entre disciplinas da matriz.",
    "EquivalenciaDisciplina": "Regras de equivalência entre disciplinas para aproveitamento de estudos.",
    "PeriodoLetivo": "Calendário semestral de oferta acadêmica e matrícula.",
    "Sala": "Salas de aula, laboratórios e ambientes virtuais com limite de capacidade.",
    "Turma": "Oferta de disciplina em um período letivo com docente, sala e vagas.",
    "HorarioTurma": "Alocação de dias da semana e faixas de horário de cada turma.",
    "MatriculaTurma": "Vínculo do discente em uma turma ofertada, com média final, frequência e situação.",
    "AvaliacaoNota": "Notas parciais e avaliações lançadas no diário de classe digital (0.00 a 10.00).",
    "RegistroFrequencia": "Registro diário de presença ou falta por aula ministrada.",
    "PlanoEnsino": "Plano de ensino da turma com objetivos, metodologia, avaliação e bibliografia.",
    "MaterialAula": "Materiais didáticos e recursos pedagógicos publicados para a turma.",
    "ComunicadoTurma": "Avisos e comunicados oficiais enviados pelo docente à turma.",
    "MovimentacaoAcademica": "Registros de trancamento, transferência, cancelamento, destrancamento e jubilamento.",
    "RequerimentoAcademico": "Protocolos e solicitações acadêmicas abertas pelos discentes.",
    "ContratoFinanceiro": "Contratos financeiros semestrais firmados pelos estudantes.",
    "BolsaDesconto": "Bolsas de estudo, convênios e descontos percentuais vinculados ao contrato.",
    "CobrancaMensalidade": "Boletos e cobranças Pix emitidos por parcela mensal do contrato.",
    "PagamentoConciliacao": "Registros de liquidação e conciliação bancária das mensalidades.",
    "DocumentoAcademico": "Históricos, declarações, atas e diplomas emitidos com código de verificação e QR Code.",
    "AcervoDigitalMEC": "Metadados regulatórios de guarda permanente do acervo digital (MEC).",
}

MAPA_TABELA_DOMINIO: Dict[str, str] = {
    tabela: dominio.codigo
    for dominio in DOMINIOS_BANCO_DADOS
    for tabela in dominio.tabelas
}


def adaptar_sql_mysql_para_sqlite(script_sql: str) -> str:
    """
    Converte construções específicas de sintaxe MySQL 8.0+ (SET @OLD_..., AUTO_INCREMENT,
    ENGINE=InnoDB, INDEX ... VISIBLE, ON DUPLICATE KEY UPDATE) para SQLite 3 padrão,
    preservando integralmente todas as tabelas, colunas, PKs, FKs, UNIQUEs e CHECKs.
    """
    linhas_limpas: List[str] = []
    for linha in script_sql.splitlines():
        if linha.strip().upper().startswith("SET "):
            continue
        if re.match(r"^\s*INDEX\s+`?\w+`?\s*\(", linha, flags=re.IGNORECASE):
            continue
        linhas_limpas.append(linha)

    sql = "\n".join(linhas_limpas)

    # Remover cláusulas ENGINE = InnoDB ... no final dos CREATE TABLE
    sql = re.sub(
        r"\)\s*ENGINE\s*=\s*InnoDB[^;]*;",
        ");",
        sql,
        flags=re.IGNORECASE,
    )

    # Converter colunas INT NOT NULL AUTO_INCREMENT + PRIMARY KEY (`col`) em INTEGER PRIMARY KEY AUTOINCREMENT
    def _substituir_auto_increment(match: re.Match) -> str:
        corpo = match.group(1)
        m_pk = re.search(r",\s*PRIMARY\s+KEY\s*\(\s*`?(\w+)`?\s*\)", corpo, flags=re.IGNORECASE)
        if m_pk:
            col_pk = m_pk.group(1)
            padrao_col = re.compile(
                rf"(`?{re.escape(col_pk)}`?\s+)INT(?:\s+NOT\s+NULL)?\s+AUTO_INCREMENT",
                flags=re.IGNORECASE,
            )
            if padrao_col.search(corpo):
                corpo = padrao_col.sub(r"\1INTEGER PRIMARY KEY AUTOINCREMENT", corpo, count=1)
                corpo = re.sub(r",\s*PRIMARY\s+KEY\s*\(\s*`?" + re.escape(col_pk) + r"`?\s*\)", "", corpo, flags=re.IGNORECASE)
        return f"CREATE TABLE IF NOT EXISTS { corpo });"

    sql = re.sub(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(.*?)\)\s*;",
        _substituir_auto_increment,
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Converter ON DUPLICATE KEY UPDATE do MySQL para ON CONFLICT(id_perfil) DO UPDATE SET do SQLite
    sql = re.sub(
        r"ON\s+DUPLICATE\s+KEY\s+UPDATE\s+`?nome_perfil`?\s*=\s*VALUES\(`?nome_perfil`?\)\s*,\s*`?descricao`?\s*=\s*VALUES\(`?descricao`?\)\s*;",
        "ON CONFLICT(`id_perfil`) DO UPDATE SET `nome_perfil` = excluded.`nome_perfil`, `descricao` = excluded.`descricao`;",
        sql,
        flags=re.IGNORECASE,
    )

    # Extrair todos os índices declarados no script MySQL original e recriá-los como CREATE INDEX IF NOT EXISTS
    indices_extras: List[str] = []
    for m_tabela in re.finditer(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+`?(\w+)`?\s*\((.*?)\)\s*ENGINE",
        script_sql,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        nome_tabela = m_tabela.group(1)
        corpo_tabela = m_tabela.group(2)
        for m_idx in re.finditer(
            r"^\s*INDEX\s+`?(\w+)`?\s*\(([^)]+)\)",
            corpo_tabela,
            flags=re.IGNORECASE | re.MULTILINE,
        ):
            nome_idx = m_idx.group(1)
            cols_idx = re.sub(r"\b(ASC|DESC)\b", "", m_idx.group(2), flags=re.IGNORECASE)
            indices_extras.append(
                f"CREATE INDEX IF NOT EXISTS `{nome_idx}_{nome_tabela}` ON `{nome_tabela}` ({cols_idx});"
            )

    if indices_extras:
        sql = sql + "\n" + "\n".join(indices_extras) + "\n"

    return sql


def criar_conexao_validada(caminho_sqlite: str = ":memory:") -> sqlite3.Connection:
    """
    Cria uma conexão SQLite 3 com PRAGMA foreign_keys = ON, executa o DDL completo
    das 33 tabelas e aplica a carga inicial de perfis RBAC.
    """
    conn = sqlite3.connect(caminho_sqlite)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    ddl_mysql = SCHEMA_DDL_PATH.read_text(encoding="utf-8")
    seed_mysql = SEED_DML_PATH.read_text(encoding="utf-8")

    ddl_sqlite = adaptar_sql_mysql_para_sqlite(ddl_mysql)
    seed_sqlite = adaptar_sql_mysql_para_sqlite(seed_mysql)

    conn.executescript(ddl_sqlite)
    conn.executescript(seed_sqlite)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    return conn


def _inspecionar_tabelas_conexao(conn: sqlite3.Connection) -> List[EspecificacaoTabela]:
    """Extrai os metadados reais de todas as tabelas provisionadas no banco."""
    especificacoes: List[EspecificacaoTabela] = []
    for nome_tabela, codigo_dominio in MAPA_TABELA_DOMINIO.items():
        cur_info = conn.execute(f"PRAGMA table_info(`{nome_tabela}`);").fetchall()
        if not cur_info:
            continue

        cur_idx = conn.execute(f"PRAGMA index_list(`{nome_tabela}`);").fetchall()
        colunas_unicas = set()
        nomes_indices: List[str] = []
        for idx_row in cur_idx:
            nome_idx = idx_row["name"]
            nomes_indices.append(nome_idx)
            if idx_row["unique"]:
                cols = conn.execute(f"PRAGMA index_info(`{nome_idx}`);").fetchall()
                if len(cols) == 1:
                    colunas_unicas.add(cols[0]["name"])

        colunas: List[EspecificacaoColuna] = []
        chave_primaria = ""
        for col in cur_info:
            eh_pk = bool(col["pk"])
            if eh_pk and not chave_primaria:
                chave_primaria = col["name"]
            colunas.append(
                EspecificacaoColuna(
                    nome=col["name"],
                    tipo_sql=col["type"] or "TEXT",
                    obrigatoria=bool(col["notnull"]) or eh_pk,
                    chave_primaria=eh_pk,
                    unica=eh_pk or (col["name"] in colunas_unicas),
                    valor_padrao=str(col["dflt_value"]) if col["dflt_value"] is not None else None,
                )
            )

        cur_fks = conn.execute(f"PRAGMA foreign_key_list(`{nome_tabela}`);").fetchall()
        fks: List[EspecificacaoChaveEstrangeira] = [
            EspecificacaoChaveEstrangeira(
                coluna_origem=fk["from"],
                tabela_destino=fk["table"],
                coluna_destino=fk["to"],
                on_delete=fk["on_delete"].upper(),
                on_update=fk["on_update"].upper(),
            )
            for fk in cur_fks
        ]

        especificacoes.append(
            EspecificacaoTabela(
                nome_tabela=nome_tabela,
                dominio=codigo_dominio,
                descricao=DESCRICOES_TABELAS.get(nome_tabela, nome_tabela),
                chave_primaria=chave_primaria,
                colunas=colunas,
                chaves_estrangeiras=fks,
                indices=nomes_indices,
            )
        )
    return especificacoes


def listar_tabelas_esquema(dominio: Optional[str] = None) -> List[EspecificacaoTabela]:
    """Lista todas as tabelas do esquema completo, opcionalmente filtradas por código de domínio."""
    conn = criar_conexao_validada()
    try:
        tabelas = _inspecionar_tabelas_conexao(conn)
        if dominio:
            dominio_norm = dominio.strip().lower()
            tabelas = [t for t in tabelas if t.dominio.lower() == dominio_norm]
        return tabelas
    finally:
        conn.close()


def obter_resumo_arquitetura() -> ResumoArquiteturaSGA:
    """Retorna a definição consolidada da arquitetura multicamadas e dos domínios do banco de dados."""
    total_tabelas = sum(len(d.tabelas) for d in DOMINIOS_BANCO_DADOS)
    return ResumoArquiteturaSGA(
        sistema="SGA-Edu",
        tarefa_backlog="SGA-18",
        padrao_arquitetural="Arquitetura Multicamadas Orientada a Módulos de Domínio (SPA + REST API + Persistência Relacional)",
        camadas=CAMADAS_ARQUITETURA,
        dominios_banco_dados=DOMINIOS_BANCO_DADOS,
        total_dominios=len(DOMINIOS_BANCO_DADOS),
        total_tabelas=total_tabelas,
        conformidade_regulatoria=[
            "LGPD (Lei nº 13.709/2018) - Consentimento explícito, minimização de dados e trilha de auditoria imutável",
            "Portarias MEC nº 315/2018 e nº 360/2022 - Acervo Acadêmico Digital com assinatura ICP-Brasil e QR Code SHA-256",
            "RBAC Estrito - Segregação nativa nos 5 perfis institucionais (Aluno, Professor, Secretaria, Financeiro e Admin)",
        ],
    )


def validar_esquema_completo() -> RelatorioIntegridadeSchema:
    """
    Executa o provisionamento completo do esquema e dos seeds em banco isolado
    e verifica todas as restrições estruturais e de integridade referencial.
    """
    conn = criar_conexao_validada()
    try:
        fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        fk_checks = conn.execute("PRAGMA foreign_key_check;").fetchall()
        especificacoes = _inspecionar_tabelas_conexao(conn)
        perfis_count = conn.execute("SELECT COUNT(*) FROM Perfil;").fetchone()[0]

        violacoes: List[str] = []
        tabelas_esperadas = len(MAPA_TABELA_DOMINIO)
        tabelas_criadas = len(especificacoes)

        if tabelas_criadas != tabelas_esperadas:
            violacoes.append(
                f"Número de tabelas criadas ({tabelas_criadas}) difere do esperado ({tabelas_esperadas})."
            )
        if perfis_count != 5:
            violacoes.append(f"Esperados 5 perfis RBAC, encontrados {perfis_count}.")
        if not fk_status:
            violacoes.append("PRAGMA foreign_keys não está ativo na conexão.")
        if fk_checks:
            violacoes.append(f"Encontradas {len(fk_checks)} violações em PRAGMA foreign_key_check.")

        total_fks = sum(len(t.chaves_estrangeiras) for t in especificacoes)
        total_indices = sum(len(t.indices) for t in especificacoes)

        for t in especificacoes:
            if not t.chave_primaria:
                violacoes.append(f"Tabela {t.nome_tabela} não possui chave primária definida.")

        return RelatorioIntegridadeSchema(
            sucesso=(len(violacoes) == 0),
            total_dominios=len(DOMINIOS_BANCO_DADOS),
            total_tabelas_esperadas=tabelas_esperadas,
            total_tabelas_criadas=tabelas_criadas,
            perfis_rbac_carregados=perfis_count,
            chaves_estrangeiras_ativas=bool(fk_status),
            total_chaves_estrangeiras_verificadas=total_fks,
            total_indices_verificados=total_indices,
            violacoes_integridade=violacoes,
        )
    finally:
        conn.close()


TABELAS_CATALOGO: List[EspecificacaoTabela] = listar_tabelas_esquema()
