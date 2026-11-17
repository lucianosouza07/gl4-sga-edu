"""
Testes automatizados de integridade do esquema relacional completo do SGA-Edu (US1 e US2).
"""

import pathlib
import sqlite3
import sys
import unittest

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[4]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.backend.modulo_definir_arquitetura_de_software_e_modelar_o_banco_de_dados_completo.database_manager import (
    criar_conexao_validada,
    validar_esquema_completo,
)


class TestSchemaIntegridadeUS1US2(unittest.TestCase):
    """Valida a criação das tabelas, seeds e restrições de integridade referencial dos Domínios 1 a 4."""

    def setUp(self) -> None:
        self.conn = criar_conexao_validada()

    def tearDown(self) -> None:
        self.conn.close()

    def test_seed_cinco_perfis_rbac_e_33_tabelas(self) -> None:
        relatorio = validar_esquema_completo()
        self.assertTrue(relatorio.sucesso)
        self.assertEqual(relatorio.total_dominios, 6)
        self.assertEqual(relatorio.total_tabelas_esperadas, 33)
        self.assertEqual(relatorio.total_tabelas_criadas, 33)
        self.assertEqual(relatorio.perfis_rbac_carregados, 5)
        self.assertEqual(relatorio.violacoes_integridade, [])

        rows = self.conn.execute("SELECT id_perfil, nome_perfil FROM Perfil ORDER BY id_perfil;").fetchall()
        perfis = [(r["id_perfil"], r["nome_perfil"]) for r in rows]
        self.assertEqual(
            perfis,
            [
                (1, "Aluno"),
                (2, "Professor"),
                (3, "Secretaria"),
                (4, "Financeiro"),
                (5, "Admin"),
            ],
        )

    def test_us1_bloqueio_exclusao_perfil_com_usuario_e_unicidade_login(self) -> None:
        self.conn.execute(
            "INSERT INTO Usuario (id_usuario, login, senha_hash, perfil_RBAC) VALUES (10, 'aluno01', 'hash_seguro', 1);"
        )
        # Login duplicado deve falhar
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO Usuario (login, senha_hash, perfil_RBAC) VALUES ('aluno01', 'outro_hash', 1);"
            )
        # Excluir Perfil em uso deve falhar (ON DELETE RESTRICT)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM Perfil WHERE id_perfil = 1;")

    def test_us1_preservacao_professor_e_auditoria_set_null_e_cascata_token(self) -> None:
        self.conn.execute(
            "INSERT INTO Usuario (id_usuario, login, senha_hash, perfil_RBAC) VALUES (20, 'prof.veras', 'hash_123', 2);"
        )
        self.conn.execute(
            """
            INSERT INTO Professor (id, nome, email, cpf, departamento, titulacao, Usuario_id_usuario)
            VALUES (1, 'Letícia Veras', 'veras@uneb.br', '12345678901', 'DCET', 'Doutorado', 20);
            """
        )
        self.conn.execute(
            """
            INSERT INTO TokenRecuperacao (usuario_id, token_hash, criado_em, expira_em, ip_solicitacao)
            VALUES (20, 'hash_token_abc', '2026-11-17 10:00:00', '2026-11-17 10:30:00', '127.0.0.1');
            """
        )
        self.conn.execute(
            """
            INSERT INTO LogAuditoriaRecuperacao (usuario_id, data_hora, ip_origem, acao, status_resultado)
            VALUES (20, '2026-11-17 10:00:00', '127.0.0.1', 'SOLICITAR_TOKEN', 'SUCESSO');
            """
        )
        self.conn.execute(
            """
            INSERT INTO LogAuditoriaSistema (usuario_id, entidade_afetada, acao, ip_origem, data_hora)
            VALUES (20, 'Professor', 'UPDATE', '127.0.0.1', '2026-11-17 10:05:00');
            """
        )

        # Remover o usuário deve:
        # 1) Manter Professor com Usuario_id_usuario = NULL
        # 2) Manter LogAuditoriaRecuperacao e LogAuditoriaSistema com usuario_id = NULL
        # 3) Excluir TokenRecuperacao em cascata
        self.conn.execute("DELETE FROM Usuario WHERE id_usuario = 20;")

        prof = self.conn.execute("SELECT nome, Usuario_id_usuario FROM Professor WHERE id = 1;").fetchone()
        self.assertIsNotNone(prof)
        self.assertIsNone(prof["Usuario_id_usuario"])

        log_rec = self.conn.execute("SELECT usuario_id, acao FROM LogAuditoriaRecuperacao;").fetchone()
        self.assertIsNotNone(log_rec)
        self.assertIsNone(log_rec["usuario_id"])

        log_sis = self.conn.execute("SELECT usuario_id, acao FROM LogAuditoriaSistema;").fetchone()
        self.assertIsNotNone(log_sis)
        self.assertIsNone(log_sis["usuario_id"])

        tokens = self.conn.execute("SELECT COUNT(*) FROM TokenRecuperacao WHERE usuario_id = 20;").fetchone()[0]
        self.assertEqual(tokens, 0)

    def test_us2_nucleo_academico_prerequisito_matricula_e_limites_nota(self) -> None:
        self.conn.execute(
            "INSERT INTO Departamento (id_departamento, codigo, nome, sigla) VALUES (1, 'DEP-01', 'Ciências Exatas', 'DCET');"
        )
        self.conn.execute(
            """
            INSERT INTO Curso (id_curso, codigo_mec, nome, grau_academico, carga_horaria_total, duracao_semestres, departamento_id)
            VALUES (1, 'MEC-SI-001', 'Sistemas de Informação', 'Bacharelado', 3000, 8, 1);
            """
        )
        self.conn.execute(
            """
            INSERT INTO MatrizCurricular (id_matriz, curso_id, codigo_matriz, ano_vigencia, semestre_vigencia, carga_horaria_minima)
            VALUES (1, 1, 'MAT-SI-2026', 2026, 1, 3000);
            """
        )
        self.conn.execute(
            """
            INSERT INTO Disciplina (id_disciplina, matriz_id, codigo, nome, semestre_ideal, carga_horaria, creditos)
            VALUES
            (1, 1, 'WEB01', 'Programação Web I', 4, 60, 4),
            (2, 1, 'WEB02', 'Programação Web II', 5, 60, 4);
            """
        )

        # Auto-dependência em PreRequisito deve ser rejeitada por CHECK (disciplina_id <> requisito_disciplina_id)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO PreRequisito (disciplina_id, requisito_disciplina_id) VALUES (1, 1);"
            )

        # Pré-requisito válido entre disciplinas distintas
        self.conn.execute(
            "INSERT INTO PreRequisito (disciplina_id, requisito_disciplina_id) VALUES (2, 1);"
        )

        self.conn.execute(
            """
            INSERT INTO PeriodoLetivo (id_periodo, codigo, ano, semestre, data_inicio, data_fim)
            VALUES (1, '2026.2', 2026, 2, '2026-08-01', '2026-12-15');
            """
        )
        self.conn.execute(
            """
            INSERT INTO Sala (id_sala, codigo_sala, bloco, capacidade)
            VALUES (1, 'LAB-03', 'Bloco B', 40);
            """
        )
        self.conn.execute(
            """
            INSERT INTO Turma (id_turma, codigo_turma, disciplina_id, periodo_letivo_id, sala_id, turno, vagas_totais)
            VALUES (1, 'WEB02-T01', 2, 1, 1, 'NOTURNO', 40);
            """
        )

        self.conn.execute(
            "INSERT INTO Usuario (id_usuario, login, senha_hash, perfil_RBAC) VALUES (30, '20261001', 'hash_aluno', 1);"
        )
        self.conn.execute(
            "INSERT INTO Aluno (matricula, Usuario_id_usuario, nome, curso_id) VALUES (20261001, 30, 'Discente Teste', 1);"
        )
        self.conn.execute(
            """
            INSERT INTO MatriculaTurma (id_matricula_turma, aluno_matricula, turma_id, data_matricula)
            VALUES (1, 20261001, 1, '2026-08-02 09:00:00');
            """
        )

        # Matrícula duplicada na mesma turma deve falhar
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO MatriculaTurma (aluno_matricula, turma_id, data_matricula)
                VALUES (20261001, 1, '2026-08-03 09:00:00');
                """
            )

        # Nota fora do intervalo 0.00 a 10.00 deve falhar
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO AvaliacaoNota (matricula_turma_id, etapa, nota, data_lancamento)
                VALUES (1, 'AV1', 10.50, '2026-09-20 14:00:00');
                """
            )

        # Nota válida dentro do intervalo 0.00 a 10.00 deve funcionar
        self.conn.execute(
            """
            INSERT INTO AvaliacaoNota (matricula_turma_id, etapa, nota, data_lancamento)
            VALUES (1, 'AV1', 9.50, '2026-09-20 14:00:00');
            """
        )


if __name__ == "__main__":
    unittest.main()
