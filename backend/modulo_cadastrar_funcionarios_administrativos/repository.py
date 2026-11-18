"""Persistência relacional SQLite compatível com o schema completo do SGA-Edu."""

from datetime import datetime, timezone
import json
import os
import sqlite3
import threading
from typing import Any, Optional

try:
    from .audit_service import sanitizar_snapshot
    from .schemas import PERFIL_ID_PARA_NOME
except ImportError:
    from audit_service import sanitizar_snapshot
    from schemas import PERFIL_ID_PARA_NOME

PERFIS_INICIAIS: tuple[tuple[int, str, str], ...] = (
    (1, "Aluno", "Perfil discente"),
    (2, "Professor", "Perfil docente"),
    (3, "Secretaria", "Perfil de secretaria acadêmica e colegiado"),
    (4, "Financeiro", "Perfil de gestão financeira"),
    (5, "Admin", "Perfil de administração de TI e governança RBAC"),
)

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Perfil (
    id_perfil INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_perfil VARCHAR(50) NOT NULL UNIQUE,
    descricao VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS Usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    login VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    perfil_RBAC INTEGER NOT NULL,
    tokenMFA VARCHAR(45) NULL,
    statusCONTA INTEGER NOT NULL DEFAULT 1,
    dadosIdentificacao VARCHAR(255) NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_Usuario_Perfil
        FOREIGN KEY (perfil_RBAC)
        REFERENCES Perfil (id_perfil)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS FuncionarioAdministrativo (
    id_funcionario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(120) NULL,
    cpf VARCHAR(14) NULL UNIQUE,
    cargo VARCHAR(80) NULL,
    setor VARCHAR(100) NOT NULL,
    Usuario_id_usuario INTEGER NOT NULL UNIQUE,
    CONSTRAINT fk_FuncionarioAdministrativo_Usuario1
        FOREIGN KEY (Usuario_id_usuario)
        REFERENCES Usuario (id_usuario)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS LogAuditoriaSistema (
    id_auditoria INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NULL,
    entidade_afetada VARCHAR(80) NOT NULL,
    id_registro_afetado VARCHAR(64) NULL,
    acao VARCHAR(50) NOT NULL,
    dados_anteriores TEXT NULL,
    dados_novos TEXT NULL,
    ip_origem VARCHAR(45) NOT NULL,
    data_hora DATETIME NOT NULL,
    CONSTRAINT fk_LogAuditoriaSistema_Usuario
        FOREIGN KEY (usuario_id)
        REFERENCES Usuario (id_usuario)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
"""


def criar_conexao(db_path: str = ":memory:") -> sqlite3.Connection:
    """Abre conexão SQLite com chaves estrangeiras ativadas e suporte multi-thread."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_esquema(conn: sqlite3.Connection) -> None:
    """Cria as tabelas relacionais do domínio e semeia os 5 perfis RBAC fixos."""
    conn.executescript(SCHEMA_SQL)
    conn.executemany(
        """
        INSERT INTO Perfil (id_perfil, nome_perfil, descricao)
        VALUES (?, ?, ?)
        ON CONFLICT(id_perfil) DO UPDATE SET
            nome_perfil = excluded.nome_perfil,
            descricao = excluded.descricao;
        """,
        PERFIS_INICIAIS,
    )
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.commit()


def _parse_senha_provisoria(dados_identificacao: Optional[str]) -> bool:
    if not dados_identificacao:
        return False
    try:
        parsed = json.loads(dados_identificacao)
        return bool(parsed.get("senha_provisoria", False))
    except (ValueError, TypeError, AttributeError):
        return False


class FuncionarioAdminRepository:
    """Repositório transacional SQLite para usuários administrativos e trilha de auditoria."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = threading.RLock()
        self.conn = criar_conexao(db_path)
        inicializar_esquema(self.conn)

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def buscar_usuario_por_id(self, usuario_id: int) -> Optional[dict[str, Any]]:
        """Busca usuário por ID com nome do perfil RBAC associado."""
        with self._lock:
            row = self.conn.execute(
                """
                SELECT u.id_usuario, u.login, u.senha_hash, u.perfil_RBAC,
                       u.statusCONTA, u.dadosIdentificacao, u.criado_em,
                       p.nome_perfil
                FROM Usuario u
                JOIN Perfil p ON p.id_perfil = u.perfil_RBAC
                WHERE u.id_usuario = ?
                """,
                (usuario_id,),
            ).fetchone()
            return dict(row) if row else None

    def inserir_usuario_seed(
        self,
        login: str,
        senha_hash: str,
        perfil_id: int,
        status_conta: int = 1,
        dados_identificacao: Optional[str] = None,
    ) -> int:
        """Insere conta de usuário diretamente (útil para seed de bootstrap/testes)."""
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Usuario (login, senha_hash, perfil_RBAC, statusCONTA, dadosIdentificacao)
                VALUES (?, ?, ?, ?, ?)
                """,
                (login, senha_hash, perfil_id, status_conta, dados_identificacao),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def _inserir_auditoria_tx(
        self,
        usuario_id: Optional[int],
        entidade_afetada: str,
        id_registro_afetado: Optional[str],
        acao: str,
        dados_anteriores: Optional[str],
        dados_novos: Optional[str],
        ip_origem: str,
        data_hora: Optional[str] = None,
    ) -> int:
        timestamp = data_hora or datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO LogAuditoriaSistema (
                usuario_id, entidade_afetada, id_registro_afetado,
                acao, dados_anteriores, dados_novos, ip_origem, data_hora
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                usuario_id,
                entidade_afetada,
                id_registro_afetado,
                acao,
                dados_anteriores,
                dados_novos,
                ip_origem,
                timestamp,
            ),
        )
        return int(cur.lastrowid)

    def inserir_auditoria(
        self,
        usuario_id: Optional[int],
        entidade_afetada: str,
        id_registro_afetado: Optional[str],
        acao: str,
        dados_anteriores: Optional[str],
        dados_novos: Optional[str],
        ip_origem: str,
        data_hora: Optional[str] = None,
    ) -> dict[str, Any]:
        """Insere um evento imutável em LogAuditoriaSistema."""
        with self._lock:
            log_id = self._inserir_auditoria_tx(
                usuario_id=usuario_id,
                entidade_afetada=entidade_afetada,
                id_registro_afetado=id_registro_afetado,
                acao=acao,
                dados_anteriores=dados_anteriores,
                dados_novos=dados_novos,
                ip_origem=ip_origem,
                data_hora=data_hora,
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM LogAuditoriaSistema WHERE id_auditoria = ?",
                (log_id,),
            ).fetchone()
            return dict(row)

    @staticmethod
    def _row_para_resposta(row: sqlite3.Row) -> dict[str, Any]:
        perfil_id = int(row["perfil_RBAC"])
        return {
            "id_funcionario": int(row["id_funcionario"]),
            "usuario_id": int(row["Usuario_id_usuario"]),
            "nome": str(row["nome"]),
            "cpf": str(row["cpf"]),
            "login": str(row["login"]),
            "setor": str(row["setor"]),
            "cargo": row["cargo"],
            "perfil_id": perfil_id,
            "perfil": PERFIL_ID_PARA_NOME[perfil_id],
            "ativo": int(row["statusCONTA"]) == 1,
            "senha_provisoria": _parse_senha_provisoria(row["dadosIdentificacao"]),
            "criado_em": row["criado_em"],
        }

    def buscar_por_id(self, funcionario_id: int) -> Optional[dict[str, Any]]:
        """Busca funcionário administrativo e sua conta associada pelo ID."""
        with self._lock:
            row = self.conn.execute(
                """
                SELECT f.id_funcionario, f.nome, f.cpf, f.cargo, f.setor, f.Usuario_id_usuario,
                       u.login, u.perfil_RBAC, u.statusCONTA, u.dadosIdentificacao, u.criado_em
                FROM FuncionarioAdministrativo f
                JOIN Usuario u ON u.id_usuario = f.Usuario_id_usuario
                WHERE f.id_funcionario = ?
                """,
                (funcionario_id,),
            ).fetchone()
            return self._row_para_resposta(row) if row else None

    def buscar_por_cpf(self, cpf: str) -> Optional[dict[str, Any]]:
        """Busca funcionário administrativo pelo CPF normalizado."""
        with self._lock:
            row = self.conn.execute(
                "SELECT id_funcionario, cpf, Usuario_id_usuario FROM FuncionarioAdministrativo WHERE cpf = ?",
                (cpf,),
            ).fetchone()
            return dict(row) if row else None

    def buscar_usuario_por_login(self, login: str) -> Optional[dict[str, Any]]:
        """Busca conta de usuário pelo login exato."""
        with self._lock:
            row = self.conn.execute(
                "SELECT id_usuario, login, perfil_RBAC, statusCONTA FROM Usuario WHERE login = ?",
                (login,),
            ).fetchone()
            return dict(row) if row else None

    def criar_funcionario_e_usuario(
        self,
        nome: str,
        cpf: str,
        login: str,
        senha_hash: str,
        setor: str,
        cargo: Optional[str],
        perfil_id: int,
        operador_usuario_id: int,
        ip_origem: str,
        dados_novos_json: Optional[str],
    ) -> dict[str, Any]:
        """Cria atomicamente Usuario, FuncionarioAdministrativo e evento de auditoria CRIAR."""
        dados_id = json.dumps({"senha_provisoria": True}, ensure_ascii=False)
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                cur_user = self.conn.execute(
                    """
                    INSERT INTO Usuario (login, senha_hash, perfil_RBAC, statusCONTA, dadosIdentificacao)
                    VALUES (?, ?, ?, 1, ?)
                    """,
                    (login, senha_hash, perfil_id, dados_id),
                )
                usuario_id = int(cur_user.lastrowid)

                cur_func = self.conn.execute(
                    """
                    INSERT INTO FuncionarioAdministrativo (nome, cpf, cargo, setor, Usuario_id_usuario)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (nome, cpf, cargo, setor, usuario_id),
                )
                func_id = int(cur_func.lastrowid)

                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="FuncionarioAdministrativo",
                    id_registro_afetado=str(func_id),
                    acao="CRIAR",
                    dados_anteriores=None,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            criado = self.buscar_por_id(func_id)
            assert criado is not None
            return criado

    def contar_admins_ativos(self) -> int:
        """Retorna a quantidade de contas com perfil Admin ativas no sistema."""
        with self._lock:
            row = self.conn.execute(
                "SELECT COUNT(*) AS total FROM Usuario WHERE perfil_RBAC = 5 AND statusCONTA = 1"
            ).fetchone()
            return int(row["total"]) if row else 0

    def listar_funcionarios(
        self,
        perfil_id: Optional[int] = None,
        setor: Optional[str] = None,
        ativo: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        """Lista funcionários administrativos com filtros opcionais e ordenação alfabética."""
        clausulas: list[str] = []
        params: list[Any] = []
        if perfil_id is not None:
            clausulas.append("u.perfil_RBAC = ?")
            params.append(perfil_id)
        if setor is not None and setor.strip():
            clausulas.append("LOWER(f.setor) LIKE ?")
            params.append(f"%{setor.strip().lower()}%")
        if ativo is not None:
            clausulas.append("u.statusCONTA = ?")
            params.append(1 if ativo else 0)

        where_sql = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        with self._lock:
            rows = self.conn.execute(
                f"""
                SELECT f.id_funcionario, f.nome, f.cpf, f.cargo, f.setor, f.Usuario_id_usuario,
                       u.login, u.perfil_RBAC, u.statusCONTA, u.dadosIdentificacao, u.criado_em
                FROM FuncionarioAdministrativo f
                JOIN Usuario u ON u.id_usuario = f.Usuario_id_usuario
                {where_sql}
                """,
                params,
            ).fetchall()
            itens = [self._row_para_resposta(r) for r in rows]
            return sorted(itens, key=lambda item: (item["nome"].casefold(), item["id_funcionario"]))

    def listar_auditoria(self, id_registro_afetado: Optional[str] = None) -> list[dict[str, Any]]:
        """Consulta eventos de auditoria do módulo ordenados do mais recente para o mais antigo."""
        sql = (
            "SELECT * FROM LogAuditoriaSistema WHERE entidade_afetada = 'FuncionarioAdministrativo'"
        )
        params: list[Any] = []
        if id_registro_afetado is not None and id_registro_afetado.strip():
            sql += " AND id_registro_afetado = ?"
            params.append(id_registro_afetado.strip())
        sql += " ORDER BY id_auditoria DESC"
        with self._lock:
            rows = self.conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def atualizar_funcionario(
        self,
        funcionario_id: int,
        usuario_id: int,
        nome: str,
        cpf: str,
        login: str,
        setor: str,
        cargo: Optional[str],
        perfil_id: int,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: Optional[str],
        dados_novos_json: Optional[str],
    ) -> dict[str, Any]:
        """Atualiza atomicamente Usuario, FuncionarioAdministrativo e registra evento ATUALIZAR."""
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    """
                    UPDATE Usuario
                    SET login = ?, perfil_RBAC = ?
                    WHERE id_usuario = ?
                    """,
                    (login, perfil_id, usuario_id),
                )
                self.conn.execute(
                    """
                    UPDATE FuncionarioAdministrativo
                    SET nome = ?, cpf = ?, cargo = ?, setor = ?
                    WHERE id_funcionario = ?
                    """,
                    (nome, cpf, cargo, setor, funcionario_id),
                )
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="FuncionarioAdministrativo",
                    id_registro_afetado=str(funcionario_id),
                    acao="ATUALIZAR",
                    dados_anteriores=dados_anteriores_json,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            atualizado = self.buscar_por_id(funcionario_id)
            assert atualizado is not None
            return atualizado

    def alterar_status_funcionario(
        self,
        funcionario_id: int,
        usuario_id: int,
        ativo: bool,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: Optional[str],
        dados_novos_json: Optional[str],
    ) -> dict[str, Any]:
        """Alterna statusCONTA (1/0) e registra evento ALTERAR_STATUS em transação única."""
        novo_status = 1 if ativo else 0
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    "UPDATE Usuario SET statusCONTA = ? WHERE id_usuario = ?",
                    (novo_status, usuario_id),
                )
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="FuncionarioAdministrativo",
                    id_registro_afetado=str(funcionario_id),
                    acao="ALTERAR_STATUS",
                    dados_anteriores=dados_anteriores_json,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            atualizado = self.buscar_por_id(funcionario_id)
            assert atualizado is not None
            return atualizado

    def excluir_funcionario(
        self,
        funcionario_id: int,
        usuario_id: int,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: Optional[str],
    ) -> None:
        """Exclui Usuario (cascateando FuncionarioAdministrativo) preservando LogAuditoriaSistema."""
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                self.conn.execute("DELETE FROM Usuario WHERE id_usuario = ?", (usuario_id,))
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="FuncionarioAdministrativo",
                    id_registro_afetado=str(funcionario_id),
                    acao="EXCLUIR",
                    dados_anteriores=dados_anteriores_json,
                    dados_novos=None,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise


_DEFAULT_REPO: Optional[FuncionarioAdminRepository] = None
_DEFAULT_REPO_LOCK = threading.Lock()


def get_repository() -> FuncionarioAdminRepository:
    """Dependência FastAPI que fornece o repositório configurado para o ambiente."""
    global _DEFAULT_REPO
    with _DEFAULT_REPO_LOCK:
        if _DEFAULT_REPO is None:
            db_path = os.getenv("SGA_ADMIN_DB_PATH", ":memory:")
            _DEFAULT_REPO = FuncionarioAdminRepository(db_path=db_path)
        return _DEFAULT_REPO
