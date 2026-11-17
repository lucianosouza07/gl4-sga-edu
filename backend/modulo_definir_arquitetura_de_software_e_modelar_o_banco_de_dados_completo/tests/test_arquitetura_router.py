"""
Testes automatizados dos Domínios 5 (Financeiro) e 6 (Acervo Digital MEC) e dos contratos/roteador de arquitetura (US3).
"""

import pathlib
import sqlite3
import sys
import unittest

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[4]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from fastapi import HTTPException

from src.backend.modulo_definir_arquitetura_de_software_e_modelar_o_banco_de_dados_completo.database_manager import (
    criar_conexao_validada,
    listar_tabelas_esquema,
)
from src.backend.modulo_definir_arquitetura_de_software_e_modelar_o_banco_de_dados_completo.router import (
    consultar_resumo_arquitetura,
    consultar_tabelas_esquema,
    executar_validacao_integridade,
)


class TestArquiteturaRouterEDominiosUS3(unittest.TestCase):
    """Valida as regras financeiras, de acervo digital MEC e os endpoints do módulo (US3)."""

    def setUp(self) -> None:
        self.conn = criar_conexao_validada()
        self.conn.execute(
            "INSERT INTO Usuario (id_usuario, login, senha_hash, perfil_RBAC) VALUES (50, '20269999', 'hash', 1);"
        )
        self.conn.execute(
            "INSERT INTO Aluno (matricula, Usuario_id_usuario, nome) VALUES (20269999, 50, 'Aluno Financeiro');"
        )
        self.conn.execute(
            """
            INSERT INTO PeriodoLetivo (id_periodo, codigo, ano, semestre, data_inicio, data_fim)
            VALUES (10, '2026.2', 2026, 2, '2026-08-01', '2026-12-15');
            """
        )

    def tearDown(self) -> None:
        self.conn.close()

    def test_us3_dominio_financeiro_e_acervo_mec(self) -> None:
        self.conn.execute(
            """
            INSERT INTO ContratoFinanceiro (id_contrato, numero_contrato, aluno_matricula, periodo_letivo_id, valor_semestral_bruto, assinado_em)
            VALUES (1, 'CTR-2026-0001', 20269999, 10, 6000.00, '2026-07-25 11:00:00');
            """
        )

        # Desconto acima de 100% deve ser rejeitado
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO BolsaDesconto (contrato_id, tipo_beneficio, percentual_desconto)
                VALUES (1, 'BOLSA_MERITO', 120.00);
                """
            )

        self.conn.execute(
            """
            INSERT INTO BolsaDesconto (contrato_id, tipo_beneficio, percentual_desconto)
            VALUES (1, 'BOLSA_MERITO', 25.00);
            """
        )
        self.conn.execute(
            """
            INSERT INTO CobrancaMensalidade (id_cobranca, nosso_numero, contrato_id, numero_parcela, competencia, valor_nominal, valor_desconto, valor_final, data_vencimento)
            VALUES (1, 'NN-0001', 1, 1, '2026-08', 1000.00, 250.00, 750.00, '2026-08-10');
            """
        )
        self.conn.execute(
            """
            INSERT INTO PagamentoConciliacao (cobranca_id, identificador_transacao, meio_pagamento, valor_pago, data_pagamento)
            VALUES (1, 'TX-PIX-998877', 'PIX', 750.00, '2026-08-09 16:30:00');
            """
        )

        # Impedir exclusão de cobrança já conciliada (ON DELETE RESTRICT)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM CobrancaMensalidade WHERE id_cobranca = 1;")

        # Emissão e custódia no Acervo Digital MEC
        self.conn.execute(
            """
            INSERT INTO DocumentoAcademico (id_documento, aluno_matricula, tipo_documento, codigo_verificacao, hash_sha256, url_validacao_qrcode, emitido_em)
            VALUES (1, 20269999, 'HISTORICO_ESCOLAR', 'VERIF-2026-ABC', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'https://sga.uneb.br/validar/VERIF-2026-ABC', '2026-11-17 19:00:00');
            """
        )
        self.conn.execute(
            """
            INSERT INTO AcervoDigitalMEC (documento_id, assinatura_icp_brasil, carimbo_tempo)
            VALUES (1, 'ICP-BRASIL-SIG-001', '2026-11-17 19:00:02');
            """
        )

        # Impedir exclusão de DocumentoAcademico sob guarda do AcervoDigitalMEC (ON DELETE RESTRICT)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM DocumentoAcademico WHERE id_documento = 1;")

    def test_us3_endpoints_resumo_tabelas_e_validacao(self) -> None:
        resumo = consultar_resumo_arquitetura()
        self.assertEqual(resumo.sistema, "SGA-Edu")
        self.assertEqual(resumo.tarefa_backlog, "SGA-18")
        self.assertEqual(resumo.total_dominios, 6)
        self.assertEqual(resumo.total_tabelas, 33)
        self.assertEqual(len(resumo.camadas), 3)

        todas_tabelas = consultar_tabelas_esquema(dominio=None)
        self.assertEqual(len(todas_tabelas), 33)

        tabelas_fin = listar_tabelas_esquema(dominio="gestao_financeira")
        self.assertEqual(len(tabelas_fin), 4)

        with self.assertRaises(HTTPException) as ctx:
            consultar_tabelas_esquema(dominio="dominio_inexistente")
        self.assertEqual(ctx.exception.status_code, 404)

        relatorio = executar_validacao_integridade()
        self.assertTrue(relatorio.sucesso)
        self.assertEqual(relatorio.total_tabelas_criadas, 33)
        self.assertGreaterEqual(relatorio.total_chaves_estrangeiras_verificadas, 35)


if __name__ == "__main__":
    unittest.main()
