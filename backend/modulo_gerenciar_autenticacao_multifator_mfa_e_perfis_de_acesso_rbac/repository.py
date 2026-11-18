"""Persistência relacional SQLite e controle transacional para MFA, RBAC e Auditoria."""

from datetime import datetime, timezone
import sqlite3
import threading
import time
from typing import Any, Optional

try:
    from .schemas import PERFIL_ID_PARA_NOME
except ImportError:
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

CREATE TABLE IF NOT EXISTS MfaCodigoRecuperacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    codigo_hash VARCHAR(64) NOT NULL,
    usado INTEGER NOT NULL DEFAULT 0,
    data_uso DATETIME NULL,
    criado_em DATETIME NOT NULL,
    CONSTRAINT fk_MfaCodigoRecuperacao_Usuario
        FOREIGN KEY (usuario_id)
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
    """Abre conexão SQLite com chaves estrangeiras ativadas."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_esquema(conn: sqlite3.Connection) -> None:
    """Cria tabelas relacionais e popula os 5 perfis RBAC institucionais."""
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


class MfaRbacRepository:
    """Repositório transacional SQLite e cache de estados efêmeros para MFA e RBAC."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self.conn = criar_conexao(db_path)
        inicializar_esquema(self.conn)

        # Caches efêmeros em memória para segredos provisórios e controle anti-replay/força bruta
        self._segredos_provisorios: dict[int, tuple[str, float]] = {}  # usuario_id -> (segredo, expira_em)
        self._ultimos_passos_totp: dict[int, int] = {}  # usuario_id -> ultimo_passo_consumido
        self._tentativas_desafio: dict[str, int] = {}  # challenge_jti -> tentativas_falhas

    def fechar(self) -> None:
        with self._lock:
            self.conn.close()

    # --- Gestão de Usuários e Autenticação Básica ---

    def criar_usuario(
        self,
        login: str,
        senha_hash: str,
        perfil_RBAC: int,
        statusCONTA: int = 1,
        tokenMFA: Optional[str] = None,
        dadosIdentificacao: Optional[str] = None,
    ) -> int:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO Usuario (login, senha_hash, perfil_RBAC, statusCONTA, tokenMFA, dadosIdentificacao)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (login, senha_hash, perfil_RBAC, statusCONTA, tokenMFA, dadosIdentificacao),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def buscar_usuario_por_id(self, id_usuario: int) -> Optional[dict[str, Any]]:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT u.id_usuario, u.login, u.senha_hash, u.perfil_RBAC, u.tokenMFA,
                       u.statusCONTA, u.dadosIdentificacao, u.criado_em,
                       p.nome_perfil, p.descricao as perfil_descricao
                FROM Usuario u
                JOIN Perfil p ON p.id_perfil = u.perfil_RBAC
                WHERE u.id_usuario = ?;
                """,
                (id_usuario,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def buscar_usuario_por_login(self, login: str) -> Optional[dict[str, Any]]:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT u.id_usuario, u.login, u.senha_hash, u.perfil_RBAC, u.tokenMFA,
                       u.statusCONTA, u.dadosIdentificacao, u.criado_em,
                       p.nome_perfil, p.descricao as perfil_descricao
                FROM Usuario u
                JOIN Perfil p ON p.id_perfil = u.perfil_RBAC
                WHERE u.login = ?;
                """,
                (login.strip(),),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    # --- Gestão de MFA e Códigos de Recuperação ---

    def salvar_segredo_provisorio(self, usuario_id: int, segredo: str, ttl_segundos: int = 600) -> None:
        with self._lock:
            self._segredos_provisorios[usuario_id] = (segredo, time.time() + ttl_segundos)

    def obter_segredo_provisorio(self, usuario_id: int) -> Optional[str]:
        with self._lock:
            dados = self._segredos_provisorios.get(usuario_id)
            if not dados:
                return None
            segredo, expira_em = dados
            if time.time() > expira_em:
                self._segredos_provisorios.pop(usuario_id, None)
                return None
            return segredo

    def limpar_segredo_provisorio(self, usuario_id: int) -> None:
        with self._lock:
            self._segredos_provisorios.pop(usuario_id, None)

    def ativar_mfa(self, usuario_id: int, segredo: str, hashes_recuperacao: list[str]) -> bool:
        agora = datetime.now(timezone.utc).isoformat()
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    "UPDATE Usuario SET tokenMFA = ? WHERE id_usuario = ?;",
                    (segredo, usuario_id),
                )
                cur.execute(
                    "DELETE FROM MfaCodigoRecuperacao WHERE usuario_id = ?;",
                    (usuario_id,),
                )
                for h in hashes_recuperacao:
                    cur.execute(
                        """
                        INSERT INTO MfaCodigoRecuperacao (usuario_id, codigo_hash, usado, criado_em)
                        VALUES (?, ?, 0, ?);
                        """,
                        (usuario_id, h, agora),
                    )
                self.conn.commit()
                self._segredos_provisorios.pop(usuario_id, None)
                return True
            except Exception:
                self.conn.rollback()
                raise

    def desativar_mfa(self, usuario_id: int) -> bool:
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    "UPDATE Usuario SET tokenMFA = NULL WHERE id_usuario = ?;",
                    (usuario_id,),
                )
                cur.execute(
                    "DELETE FROM MfaCodigoRecuperacao WHERE usuario_id = ?;",
                    (usuario_id,),
                )
                self.conn.commit()
                self._segredos_provisorios.pop(usuario_id, None)
                self._ultimos_passos_totp.pop(usuario_id, None)
                return True
            except Exception:
                self.conn.rollback()
                raise

    # --- Prevenção Anti-Replay e Códigos de Recuperação ---

    def registrar_passo_totp_consumido(self, usuario_id: int, passo: int) -> bool:
        """Impede reuso de código TOTP no mesmo passo temporal (Anti-Replay)."""
        with self._lock:
            ultimo = self._ultimos_passos_totp.get(usuario_id, -1)
            if passo <= ultimo:
                return False  # Já utilizado nesta janela ou anterior
            self._ultimos_passos_totp[usuario_id] = passo
            return True

    def consumir_codigo_recuperacao(self, usuario_id: int, hash_codigo: str) -> bool:
        agora = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT id FROM MfaCodigoRecuperacao
                WHERE usuario_id = ? AND codigo_hash = ? AND usado = 0;
                """,
                (usuario_id, hash_codigo),
            )
            row = cur.fetchone()
            if not row:
                return False
            cod_id = row["id"]
            cur.execute(
                """
                UPDATE MfaCodigoRecuperacao
                SET usado = 1, data_uso = ?
                WHERE id = ?;
                """,
                (agora, cod_id),
            )
            self.conn.commit()
            return True

    def contar_codigos_recuperacao_restantes(self, usuario_id: int) -> int:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) as total FROM MfaCodigoRecuperacao
                WHERE usuario_id = ? AND usado = 0;
                """,
                (usuario_id,),
            )
            row = cur.fetchone()
            return int(row["total"]) if row else 0

    # --- Rastreamento de Tentativas de Desafio MFA (Força Bruta) ---

    def registrar_tentativa_desafio_falha(self, jti: str) -> int:
        with self._lock:
            count = self._tentativas_desafio.get(jti, 0) + 1
            self._tentativas_desafio[jti] = count
            return count

    def obter_tentativas_desafio_falhas(self, jti: str) -> int:
        with self._lock:
            return self._tentativas_desafio.get(jti, 0)

    def limpar_tentativas_desafio(self, jti: str) -> None:
        with self._lock:
            self._tentativas_desafio.pop(jti, None)

    # --- Governança RBAC ---

    def listar_perfis(self) -> list[dict[str, Any]]:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id_perfil, nome_perfil, descricao FROM Perfil ORDER BY id_perfil ASC;")
            return [dict(r) for r in cur.fetchall()]

    def buscar_perfil_por_id(self, id_perfil: int) -> Optional[dict[str, Any]]:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id_perfil, nome_perfil, descricao FROM Perfil WHERE id_perfil = ?;", (id_perfil,))
            row = cur.fetchone()
            return dict(row) if row else None

    def contar_admins_ativos(self) -> int:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) as total FROM Usuario WHERE perfil_RBAC = 5 AND statusCONTA = 1;")
            row = cur.fetchone()
            return int(row["total"]) if row else 0

    def atualizar_perfil_usuario(self, usuario_id: int, novo_perfil_id: int) -> bool:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE Usuario SET perfil_RBAC = ? WHERE id_usuario = ?;",
                (novo_perfil_id, usuario_id),
            )
            self.conn.commit()
            return cur.rowcount > 0

    # --- Trilha de Auditoria (LogAuditoriaSistema) ---

    def registrar_auditoria(
        self,
        usuario_id: Optional[int],
        entidade_afetada: str,
        id_registro_afetado: Optional[str],
        acao: str,
        dados_anteriores: Optional[str],
        dados_novos: Optional[str],
        ip_origem: str,
    ) -> dict[str, Any]:
        agora = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO LogAuditoriaSistema
                (usuario_id, entidade_afetada, id_registro_afetado, acao, dados_anteriores, dados_novos, ip_origem, data_hora)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    usuario_id,
                    entidade_afetada,
                    id_registro_afetado,
                    acao,
                    dados_anteriores,
                    dados_novos,
                    ip_origem,
                    agora,
                ),
            )
            self.conn.commit()
            aud_id = int(cur.lastrowid)
            return {
                "id_auditoria": aud_id,
                "usuario_id": usuario_id,
                "entidade_afetada": entidade_afetada,
                "id_registro_afetado": id_registro_afetado,
                "acao": acao,
                "dados_anteriores": dados_anteriores,
                "dados_novos": dados_novos,
                "ip_origem": ip_origem,
                "data_hora": agora,
            }

    def listar_auditoria(
        self,
        usuario_id: Optional[int] = None,
        acao: Optional[str] = None,
        limite: int = 50,
    ) -> list[dict[str, Any]]:
        with self._lock:
            query = "SELECT * FROM LogAuditoriaSistema WHERE 1=1"
            params: list[Any] = []
            if usuario_id is not None:
                query += " AND usuario_id = ?"
                params.append(usuario_id)
            if acao:
                query += " AND acao = ?"
                params.append(acao)
            query += " ORDER BY id_auditoria DESC LIMIT ?;"
            params.append(limite)

            cur = self.conn.cursor()
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
