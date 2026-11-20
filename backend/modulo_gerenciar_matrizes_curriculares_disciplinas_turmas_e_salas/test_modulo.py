import unittest
from fastapi import HTTPException
from pydantic import ValidationError

try:
    from schemas import (
        AlocacaoEntrada,
        DependenciaEntrada,
        DiaSemana,
        DisciplinaEntrada,
        MatrizEntrada,
        SalaEntrada,
        StatusMatriz,
        StatusSala,
        StatusTurma,
        TipoDependencia,
        TipoSala,
        TurmaEntrada,
        TurnoTurma,
    )
    import services
except ImportError:
    from .schemas import (
        AlocacaoEntrada,
        DependenciaEntrada,
        DiaSemana,
        DisciplinaEntrada,
        MatrizEntrada,
        SalaEntrada,
        StatusMatriz,
        StatusSala,
        StatusTurma,
        TipoDependencia,
        TipoSala,
        TurmaEntrada,
        TurnoTurma,
    )
    from . import services


class TestModuloGerenciamentoMatrizesTurmas(unittest.TestCase):
    def setUp(self):
        services.limpar_dados()

    # -----------------------------------------------------------------------
    # Testes US1: Matrizes e Disciplinas
    # -----------------------------------------------------------------------
    def test_us1_cadastrar_matriz_e_listar(self):
        dados_matriz = MatrizEntrada(
            codigo="MAT-CC-2026",
            curso="Ciência da Computação",
            vigencia_ano=2026,
            vigencia_semestre=1,
            carga_horaria_total=3200,
            status=StatusMatriz.vigente,
        )
        matriz = services.cadastrar_matriz(dados_matriz)
        self.assertEqual(matriz.id, 1)
        self.assertEqual(matriz.codigo, "MAT-CC-2026")

        matrizes = services.listar_matrizes()
        self.assertEqual(len(matrizes), 1)
        self.assertEqual(matrizes[0].codigo, "MAT-CC-2026")

    def test_us1_bloqueio_codigo_matriz_duplicado(self):
        dados = MatrizEntrada(
            codigo="MAT-SI-2026",
            curso="Sistemas de Informação",
            vigencia_ano=2026,
            vigencia_semestre=1,
            carga_horaria_total=3000,
        )
        services.cadastrar_matriz(dados)
        with self.assertRaises(HTTPException) as ctx:
            services.cadastrar_matriz(dados)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_us1_cadastrar_disciplina_com_soma_de_horas(self):
        matriz = services.cadastrar_matriz(
            MatrizEntrada(
                codigo="MAT-ENG-2026",
                curso="Engenharia de Software",
                vigencia_ano=2026,
                vigencia_semestre=1,
                carga_horaria_total=3600,
            )
        )
        disc_dados = DisciplinaEntrada(
            codigo="ES101",
            nome="Introdução à Engenharia de Software",
            periodo_recomendado=1,
            carga_horaria_teorica=40,
            carga_horaria_pratica=40,
            creditos=4,
            ementa="Fundamentos de ES",
        )
        disciplina = services.cadastrar_disciplina(matriz.id, disc_dados)
        self.assertEqual(disciplina.matriz_id, matriz.id)
        self.assertEqual(disciplina.carga_horaria_total, 80)
        self.assertEqual(disciplina.status, "ativa")

    def test_us1_bloqueio_disciplina_duplicada_na_mesma_matriz(self):
        matriz = services.cadastrar_matriz(
            MatrizEntrada(
                codigo="MAT-CC-2026",
                curso="Ciência da Computação",
                vigencia_ano=2026,
                vigencia_semestre=1,
                carga_horaria_total=3200,
            )
        )
        disc_dados = DisciplinaEntrada(
            codigo="CC101",
            nome="Algoritmos I",
            periodo_recomendado=1,
            carga_horaria_teorica=40,
            carga_horaria_pratica=20,
            creditos=3,
        )
        services.cadastrar_disciplina(matriz.id, disc_dados)
        with self.assertRaises(HTTPException) as ctx:
            services.cadastrar_disciplina(matriz.id, disc_dados)
        self.assertEqual(ctx.exception.status_code, 409)

    # -----------------------------------------------------------------------
    # Testes US2: Dependências Curriculares e Ciclos
    # -----------------------------------------------------------------------
    def test_us2_cadastrar_dependencia_valida(self):
        matriz = services.cadastrar_matriz(
            MatrizEntrada(
                codigo="MAT-CC-2026",
                curso="Ciência da Computação",
                vigencia_ano=2026,
                vigencia_semestre=1,
                carga_horaria_total=3200,
            )
        )
        d1 = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(
                codigo="CC101",
                nome="Algoritmos I",
                periodo_recomendado=1,
                carga_horaria_teorica=60,
                carga_horaria_pratica=0,
                creditos=4,
            ),
        )
        d2 = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(
                codigo="CC201",
                nome="Algoritmos II",
                periodo_recomendado=2,
                carga_horaria_teorica=60,
                carga_horaria_pratica=0,
                creditos=4,
            ),
        )
        dep = services.cadastrar_dependencia(
            matriz.id,
            DependenciaEntrada(
                disciplina_id=d2.id,
                disciplina_requisito_id=d1.id,
                tipo=TipoDependencia.pre_requisito,
            ),
        )
        self.assertEqual(dep.disciplina_id, d2.id)
        self.assertEqual(dep.disciplina_requisito_id, d1.id)

    def test_us2_bloqueio_auto_dependencia(self):
        with self.assertRaises(ValidationError):
            DependenciaEntrada(
                disciplina_id=1,
                disciplina_requisito_id=1,
                tipo=TipoDependencia.pre_requisito,
            )

    def test_us2_bloqueio_ciclo_direto_e_indireto(self):
        matriz = services.cadastrar_matriz(
            MatrizEntrada(
                codigo="MAT-CC-2026",
                curso="Ciência da Computação",
                vigencia_ano=2026,
                vigencia_semestre=1,
                carga_horaria_total=3200,
            )
        )
        da = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="DA", nome="Disciplina A", periodo_recomendado=1, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )
        db = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="DB", nome="Disciplina B", periodo_recomendado=2, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )
        dc = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="DC", nome="Disciplina C", periodo_recomendado=3, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )

        # B depende de A (A é pré-requisito de B)
        services.cadastrar_dependencia(
            matriz.id,
            DependenciaEntrada(disciplina_id=db.id, disciplina_requisito_id=da.id, tipo=TipoDependencia.pre_requisito)
        )
        # C depende de B (B é pré-requisito de C)
        services.cadastrar_dependencia(
            matriz.id,
            DependenciaEntrada(disciplina_id=dc.id, disciplina_requisito_id=db.id, tipo=TipoDependencia.pre_requisito)
        )

        # Tentativa de ciclo indireto: fazer A depender de C (A -> C -> B -> A cria ciclo)
        with self.assertRaises(HTTPException) as ctx:
            services.cadastrar_dependencia(
                matriz.id,
                DependenciaEntrada(disciplina_id=da.id, disciplina_requisito_id=dc.id, tipo=TipoDependencia.pre_requisito)
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("circular detectada", ctx.exception.detail)

    # -----------------------------------------------------------------------
    # Testes US3: Salas e Espaços Físicos
    # -----------------------------------------------------------------------
    def test_us3_cadastrar_e_listar_salas(self):
        sala = services.cadastrar_sala(
            SalaEntrada(
                codigo="SALA-101",
                bloco="Bloco A",
                andar=1,
                capacidade_maxima=40,
                tipo=TipoSala.teorica,
            )
        )
        self.assertEqual(sala.id, 1)
        self.assertEqual(sala.capacidade_maxima, 40)

        salas = services.listar_salas()
        self.assertEqual(len(salas), 1)

    def test_us3_bloqueio_sala_duplicada(self):
        sala_dados = SalaEntrada(
            codigo="LAB-INF-1",
            bloco="Bloco B",
            andar=2,
            capacidade_maxima=30,
            tipo=TipoSala.laboratorio_informatica,
        )
        services.cadastrar_sala(sala_dados)
        with self.assertRaises(HTTPException) as ctx:
            services.cadastrar_sala(sala_dados)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_us3_consultar_ocupacao_sala(self):
        sala = services.cadastrar_sala(
            SalaEntrada(codigo="SALA-201", bloco="Bloco B", andar=2, capacidade_maxima=50, tipo=TipoSala.teorica)
        )
        ocupacao = services.consultar_ocupacao_sala(sala.id, "2026.1")
        self.assertEqual(ocupacao.sala.id, sala.id)
        self.assertEqual(len(ocupacao.alocacoes), 0)

    # -----------------------------------------------------------------------
    # Testes US4: Turmas, Alocações e Detecção de Choques
    # -----------------------------------------------------------------------
    def test_us4_oferta_de_turma_e_alocacao_valida(self):
        matriz = services.cadastrar_matriz(
            MatrizEntrada(codigo="MAT-01", curso="Computação", vigencia_ano=2026, vigencia_semestre=1, carga_horaria_total=3000)
        )
        disc = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="D01", nome="Disciplina 1", periodo_recomendado=1, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )
        sala = services.cadastrar_sala(
            SalaEntrada(codigo="SALA-A1", bloco="A", andar=1, capacidade_maxima=50, tipo=TipoSala.teorica)
        )
        turma = services.cadastrar_turma(
            TurmaEntrada(
                codigo="2026.1-D01-T01",
                disciplina_id=disc.id,
                periodo_letivo="2026.1",
                turno=TurnoTurma.matutino,
                vagas_ofertadas=40,
                professor_id=10,
            )
        )
        aloc = services.alocar_horario_turma(
            turma.id,
            AlocacaoEntrada(
                sala_id=sala.id,
                dia_semana=DiaSemana.segunda,
                horario_inicio="08:00",
                horario_fim="10:00",
            ),
        )
        self.assertEqual(aloc.turma_id, turma.id)
        self.assertEqual(aloc.sala_id, sala.id)

    def test_us4_bloqueio_vagas_superiores_a_capacidade(self):
        matriz = services.cadastrar_matriz(
            MatrizEntrada(codigo="MAT-01", curso="Computação", vigencia_ano=2026, vigencia_semestre=1, carga_horaria_total=3000)
        )
        disc = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="D01", nome="Disciplina 1", periodo_recomendado=1, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )
        sala = services.cadastrar_sala(
            SalaEntrada(codigo="SALA-Pequena", bloco="A", andar=1, capacidade_maxima=30, tipo=TipoSala.teorica)
        )
        turma = services.cadastrar_turma(
            TurmaEntrada(
                codigo="2026.1-D01-T02",
                disciplina_id=disc.id,
                periodo_letivo="2026.1",
                turno=TurnoTurma.matutino,
                vagas_ofertadas=35, # excede 30
            )
        )
        with self.assertRaises(HTTPException) as ctx:
            services.alocar_horario_turma(
                turma.id,
                AlocacaoEntrada(
                    sala_id=sala.id,
                    dia_semana=DiaSemana.segunda,
                    horario_inicio="08:00",
                    horario_fim="10:00",
                ),
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("excedem a capacidade máxima", ctx.exception.detail)

    def test_us4_bloqueio_choque_de_salas(self):
        matriz = services.cadastrar_matriz(
            MatrizEntrada(codigo="MAT-01", curso="Computação", vigencia_ano=2026, vigencia_semestre=1, carga_horaria_total=3000)
        )
        d1 = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="D01", nome="Disciplina 1", periodo_recomendado=1, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )
        d2 = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="D02", nome="Disciplina 2", periodo_recomendado=1, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )
        sala = services.cadastrar_sala(
            SalaEntrada(codigo="SALA-COMUM", bloco="A", andar=1, capacidade_maxima=50, tipo=TipoSala.teorica)
        )

        t1 = services.cadastrar_turma(
            TurmaEntrada(codigo="TURMA-1", disciplina_id=d1.id, periodo_letivo="2026.1", turno=TurnoTurma.matutino, vagas_ofertadas=30, professor_id=1)
        )
        t2 = services.cadastrar_turma(
            TurmaEntrada(codigo="TURMA-2", disciplina_id=d2.id, periodo_letivo="2026.1", turno=TurnoTurma.matutino, vagas_ofertadas=30, professor_id=2)
        )

        # Aloca T1 das 08:00 às 10:00 na segunda-feira
        services.alocar_horario_turma(
            t1.id,
            AlocacaoEntrada(sala_id=sala.id, dia_semana=DiaSemana.segunda, horario_inicio="08:00", horario_fim="10:00")
        )

        # T2 tenta alocar na mesma sala das 09:00 às 11:00 (sobreposição)
        with self.assertRaises(HTTPException) as ctx:
            services.alocar_horario_turma(
                t2.id,
                AlocacaoEntrada(sala_id=sala.id, dia_semana=DiaSemana.segunda, horario_inicio="09:00", horario_fim="11:00")
            )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("Choque de salas detectado", ctx.exception.detail)

    def test_us4_bloqueio_choque_docente(self):
        matriz = services.cadastrar_matriz(
            MatrizEntrada(codigo="MAT-01", curso="Computação", vigencia_ano=2026, vigencia_semestre=1, carga_horaria_total=3000)
        )
        d1 = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="D01", nome="Disciplina 1", periodo_recomendado=1, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )
        d2 = services.cadastrar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="D02", nome="Disciplina 2", periodo_recomendado=1, carga_horaria_teorica=40, carga_horaria_pratica=0, creditos=2)
        )
        s1 = services.cadastrar_sala(SalaEntrada(codigo="S1", bloco="A", andar=1, capacidade_maxima=50, tipo=TipoSala.teorica))
        s2 = services.cadastrar_sala(SalaEntrada(codigo="S2", bloco="B", andar=1, capacidade_maxima=50, tipo=TipoSala.teorica))

        # Duas turmas diferentes com o MESMO professor_id = 99
        t1 = services.cadastrar_turma(
            TurmaEntrada(codigo="T1-PROF", disciplina_id=d1.id, periodo_letivo="2026.1", turno=TurnoTurma.matutino, vagas_ofertadas=30, professor_id=99)
        )
        t2 = services.cadastrar_turma(
            TurmaEntrada(codigo="T2-PROF", disciplina_id=d2.id, periodo_letivo="2026.1", turno=TurnoTurma.matutino, vagas_ofertadas=30, professor_id=99)
        )

        # Aloca T1 na sala S1 na terça das 10:00 às 12:00
        services.alocar_horario_turma(
            t1.id,
            AlocacaoEntrada(sala_id=s1.id, dia_semana=DiaSemana.terca, horario_inicio="10:00", horario_fim="12:00")
        )

        # T2 tenta alocar na sala S2 (sala diferente) no mesmo dia das 11:00 às 13:00 (sobrepõe horário docente)
        with self.assertRaises(HTTPException) as ctx:
            services.alocar_horario_turma(
                t2.id,
                AlocacaoEntrada(sala_id=s2.id, dia_semana=DiaSemana.terca, horario_inicio="11:00", horario_fim="13:00")
            )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("Choque de horário docente", ctx.exception.detail)

    # -----------------------------------------------------------------------
    # Testes de Endpoints do Router
    # -----------------------------------------------------------------------
    def test_router_fluxo_completo(self):
        try:
            import router
        except ImportError:
            from . import router

        # 1. Matriz e Disciplinas
        matriz = router.criar_matriz(
            MatrizEntrada(codigo="MAT-ROUTER", curso="Computação", vigencia_ano=2026, vigencia_semestre=1, carga_horaria_total=3200)
        )
        self.assertEqual(matriz.codigo, "MAT-ROUTER")
        lista_m = router.listar_matrizes()
        self.assertTrue(any(m.codigo == "MAT-ROUTER" for m in lista_m))

        disc = router.adicionar_disciplina(
            matriz.id,
            DisciplinaEntrada(codigo="ROUTER-101", nome="Teste Router", periodo_recomendado=1, carga_horaria_teorica=30, carga_horaria_pratica=30, creditos=4)
        )
        self.assertEqual(disc.carga_horaria_total, 60)
        lista_d = router.listar_disciplinas(matriz.id)
        self.assertEqual(len(lista_d), 1)

        detalhe_m = router.detalhar_matriz(matriz.id)
        self.assertEqual(len(detalhe_m.disciplinas), 1)

        # 2. Sala
        sala = router.criar_sala(
            SalaEntrada(codigo="SALA-ROUTER", bloco="C", andar=3, capacidade_maxima=45, tipo=TipoSala.teorica)
        )
        salas = router.listar_salas()
        self.assertTrue(any(s.codigo == "SALA-ROUTER" for s in salas))

        # 3. Turma e Alocação
        turma = router.criar_turma(
            TurmaEntrada(codigo="TURMA-ROUTER", disciplina_id=disc.id, periodo_letivo="2026.1", turno=TurnoTurma.noturno, vagas_ofertadas=40)
        )
        turmas = router.listar_turmas("2026.1")
        self.assertEqual(len(turmas), 1)

        aloc = router.alocar_horario(
            turma.id,
            AlocacaoEntrada(sala_id=sala.id, dia_semana=DiaSemana.quarta, horario_inicio="19:00", horario_fim="21:00")
        )
        self.assertEqual(aloc.sala_id, sala.id)
        alocs_turma = router.listar_alocacoes(turma.id)
        self.assertEqual(len(alocs_turma), 1)

        ocupacao = router.consultar_ocupacao_sala(sala.id, "2026.1")
        self.assertEqual(len(ocupacao.alocacoes), 1)


if __name__ == "__main__":
    unittest.main()
