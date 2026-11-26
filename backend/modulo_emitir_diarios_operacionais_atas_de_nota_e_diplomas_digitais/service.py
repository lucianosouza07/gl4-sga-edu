"""Regras de negócio para emissão de diários operacionais, atas de nota, diplomas digitais e Acervo MEC (SGA-25)."""

from datetime import datetime, timezone
import hmac
from typing import Any, Optional
from fastapi import HTTPException, status

HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

try:
    from .audit_service import serializar_snapshot_auditoria
    from .crypto_service import (
        calcular_hash_sha256,
        gerar_assinatura_icp_brasil,
        gerar_codigo_verificacao,
        gerar_url_validacao_qrcode,
        serializar_conteudo_canonico,
        verificar_assinatura_icp_brasil,
    )
    from .repository import DocumentoRepository
    from .schemas import (
        AtaNotasEntrada,
        DiarioOperacionalEntrada,
        DiplomaDigitalEntrada,
        FORMATO_ACERVO_PADRAO,
        FREQUENCIA_MINIMA_PERCENTUAL,
        PRAZO_GUARDA_PADRAO,
        RevogacaoDocumentoEntrada,
        SituacaoFinalTurmaEnum,
        StatusCustodiaEnum,
        TipoDocumentoEnum,
    )
    from .security import OperadorAutenticado
except ImportError:
    from audit_service import serializar_snapshot_auditoria
    from crypto_service import (
        calcular_hash_sha256,
        gerar_assinatura_icp_brasil,
        gerar_codigo_verificacao,
        gerar_url_validacao_qrcode,
        serializar_conteudo_canonico,
        verificar_assinatura_icp_brasil,
    )
    from repository import DocumentoRepository
    from schemas import (
        AtaNotasEntrada,
        DiarioOperacionalEntrada,
        DiplomaDigitalEntrada,
        FORMATO_ACERVO_PADRAO,
        FREQUENCIA_MINIMA_PERCENTUAL,
        PRAZO_GUARDA_PADRAO,
        RevogacaoDocumentoEntrada,
        SituacaoFinalTurmaEnum,
        StatusCustodiaEnum,
        TipoDocumentoEnum,
    )
    from security import OperadorAutenticado


def _extrair_publico_documento(doc: dict[str, Any]) -> dict[str, Any]:
    """Remove chave interna conteudo_json_bruto antes de retornar na camada de resposta."""
    return {k: v for k, v in doc.items() if k != "conteudo_json_bruto"}


class DocumentoService:
    """Orquestrador das regras de emissão documental, custódia MEC, validação pública e auditoria."""

    def __init__(self, repo: DocumentoRepository) -> None:
        self.repo = repo

    def _gerar_codigo_unico(self, tipo_documento: str) -> str:
        for _ in range(10):
            codigo = gerar_codigo_verificacao(tipo_documento)
            if not self.repo.codigo_verificacao_existe(codigo):
                return codigo
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível gerar um código de verificação único.",
        )

    @staticmethod
    def _apurar_frequencia_e_notas(matricula: dict[str, Any]) -> dict[str, Any]:
        """Calcula frequência consolidada e média ponderada validando intervalo 0.00..10.00."""
        avaliacoes_brutas: list[dict[str, Any]] = matricula["avaliacoes"]
        frequencias_brutas: list[dict[str, Any]] = matricula["frequencias"]

        avaliacoes_fmt: list[dict[str, Any]] = []
        soma_notas_ponderadas = 0.0
        soma_pesos = 0.0

        for av in avaliacoes_brutas:
            nota = float(av["nota"])
            peso = float(av["peso"])
            if nota < 0.0 or nota > 10.0:
                raise HTTPException(
                    status_code=HTTP_422,
                    detail=(
                        f"Nota fora do intervalo permitido (0.00 a 10.00) para matrícula "
                        f"{matricula['aluno_matricula']} na etapa {av['etapa']}."
                    ),
                )
            if peso <= 0.0:
                raise HTTPException(
                    status_code=HTTP_422,
                    detail=(
                        f"Peso de avaliação inválido para matrícula {matricula['aluno_matricula']} "
                        f"na etapa {av['etapa']}."
                    ),
                )
            soma_notas_ponderadas += nota * peso
            soma_pesos += peso
            avaliacoes_fmt.append(
                {
                    "etapa": str(av["etapa"]),
                    "nota": round(nota, 2),
                    "peso": round(peso, 2),
                }
            )

        media_registrada = matricula["media_final"]
        if media_registrada is not None:
            media_reg_float = float(media_registrada)
            if media_reg_float < 0.0 or media_reg_float > 10.0:
                raise HTTPException(
                    status_code=HTTP_422,
                    detail=(
                        f"Média final fora do intervalo permitido (0.00 a 10.00) para matrícula "
                        f"{matricula['aluno_matricula']}."
                    ),
                )
            media_consolidada: Optional[float] = round(media_reg_float, 2)
        elif soma_pesos > 0.0:
            media_consolidada = round(soma_notas_ponderadas / soma_pesos, 2)
        else:
            media_consolidada = None

        if frequencias_brutas:
            total_aulas = sum(int(f["quantidade_aulas"]) for f in frequencias_brutas)
            total_faltas = sum(
                int(f["quantidade_aulas"]) for f in frequencias_brutas if not bool(f["presente"])
            )
            if total_aulas > 0:
                percentual_frequencia = round(((total_aulas - total_faltas) / total_aulas) * 100.0, 2)
            else:
                percentual_frequencia = round(float(matricula["percentual_frequencia"]), 2)
        else:
            total_aulas = 0
            total_faltas = 0
            percentual_frequencia = round(float(matricula["percentual_frequencia"]), 2)

        return {
            "avaliacoes": avaliacoes_fmt,
            "media_consolidada": media_consolidada,
            "total_aulas_registradas": total_aulas,
            "total_faltas": total_faltas,
            "percentual_frequencia": percentual_frequencia,
            "alerta_infrequencia": percentual_frequencia < FREQUENCIA_MINIMA_PERCENTUAL,
        }

    def _emitir_e_custodiar(
        self,
        tipo_documento: str,
        conteudo: dict[str, Any],
        portaria_referencia: str,
        operador: OperadorAutenticado,
        ip_origem: str,
        aluno_matricula: Optional[int] = None,
        turma_id: Optional[int] = None,
        curso_id: Optional[int] = None,
        numero_registro: Optional[str] = None,
    ) -> dict[str, Any]:
        emitido_em = datetime.now(timezone.utc).isoformat()
        conteudo_json = serializar_conteudo_canonico(conteudo)
        hash_sha256 = calcular_hash_sha256(conteudo_json)
        codigo_verificacao = self._gerar_codigo_unico(tipo_documento)
        url_validacao_qrcode = gerar_url_validacao_qrcode(codigo_verificacao)
        assinatura_icp_brasil = gerar_assinatura_icp_brasil(
            hash_sha256=hash_sha256,
            carimbo_tempo=emitido_em,
            portaria_referencia=portaria_referencia,
            codigo_verificacao=codigo_verificacao,
        )

        snapshot_auditoria = serializar_snapshot_auditoria(
            {
                "tipo_documento": tipo_documento,
                "aluno_matricula": aluno_matricula,
                "turma_id": turma_id,
                "curso_id": curso_id,
                "numero_registro": numero_registro,
                "codigo_verificacao": codigo_verificacao,
                "hash_sha256": hash_sha256,
                "portaria_referencia": portaria_referencia,
                "formato_arquivo": FORMATO_ACERVO_PADRAO,
                "prazo_guarda": PRAZO_GUARDA_PADRAO,
                "status_custodia": StatusCustodiaEnum.INTEGRO.value,
                "valido": True,
            }
        )
        assert snapshot_auditoria is not None

        criado = self.repo.criar_documento_com_acervo_e_auditoria(
            tipo_documento=tipo_documento,
            aluno_matricula=aluno_matricula,
            turma_id=turma_id,
            curso_id=curso_id,
            numero_registro=numero_registro,
            codigo_verificacao=codigo_verificacao,
            hash_sha256=hash_sha256,
            url_validacao_qrcode=url_validacao_qrcode,
            conteudo_json=conteudo_json,
            emitido_por_usuario_id=operador.usuario_id,
            emitido_em=emitido_em,
            portaria_referencia=portaria_referencia,
            formato_arquivo=FORMATO_ACERVO_PADRAO,
            assinatura_icp_brasil=assinatura_icp_brasil,
            carimbo_tempo=emitido_em,
            prazo_guarda=PRAZO_GUARDA_PADRAO,
            ip_origem=ip_origem,
            dados_novos_auditoria_json=snapshot_auditoria,
        )
        return _extrair_publico_documento(criado)

    # ------------------------------------------------------------------
    # US1: Diário Operacional e Ata de Notas Finais
    # ------------------------------------------------------------------

    def emitir_diario_operacional(
        self,
        entrada: DiarioOperacionalEntrada,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        turma = self.repo.buscar_turma_completa(entrada.turma_id)
        if turma is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turma não encontrada.",
            )

        matriculas = self.repo.listar_matriculas_da_turma_com_notas_e_frequencias(entrada.turma_id)
        if not matriculas:
            raise HTTPException(
                status_code=HTTP_422,
                detail="Não é possível emitir diário operacional para turma sem estudantes matriculados.",
            )

        registros: list[dict[str, Any]] = []
        total_alerta = 0
        for mat in matriculas:
            apurado = self._apurar_frequencia_e_notas(mat)
            if apurado["alerta_infrequencia"]:
                total_alerta += 1
            registros.append(
                {
                    "matricula": int(mat["aluno_matricula"]),
                    "nome": str(mat["aluno_nome"] or ""),
                    "avaliacoes": apurado["avaliacoes"],
                    "media_calculada": apurado["media_consolidada"],
                    "total_aulas_registradas": apurado["total_aulas_registradas"],
                    "total_faltas": apurado["total_faltas"],
                    "percentual_frequencia": apurado["percentual_frequencia"],
                    "alerta_infrequencia": apurado["alerta_infrequencia"],
                    "situacao": str(mat["situacao"]),
                }
            )

        conteudo = {
            "turma": {
                "id_turma": int(turma["id_turma"]),
                "codigo_turma": str(turma["codigo_turma"]),
                "turno": str(turma["turno"]),
                "status_turma": str(turma["status_turma"]),
            },
            "periodo_letivo": {
                "codigo": str(turma["periodo_codigo"]),
                "ano": int(turma["periodo_ano"]),
                "semestre": int(turma["periodo_semestre"]),
            },
            "disciplina": {
                "codigo": str(turma["disciplina_codigo"]),
                "nome": str(turma["disciplina_nome"]),
                "carga_horaria": int(turma["disciplina_carga_horaria"]),
                "creditos": int(turma["disciplina_creditos"]),
            },
            "professor": (
                {
                    "id": int(turma["professor_id"]),
                    "nome": str(turma["professor_nome"]),
                    "titulacao": str(turma["professor_titulacao"]),
                }
                if turma["professor_id"] is not None
                else None
            ),
            "registros": registros,
            "resumo": {
                "total_matriculados": len(registros),
                "total_em_alerta_infrequencia": total_alerta,
            },
            "observacoes": entrada.observacoes,
        }

        return self._emitir_e_custodiar(
            tipo_documento=TipoDocumentoEnum.DIARIO_OPERACIONAL.value,
            conteudo=conteudo,
            portaria_referencia=entrada.portaria_referencia.value,
            operador=operador,
            ip_origem=ip_origem,
            turma_id=int(turma["id_turma"]),
        )

    def emitir_ata_notas(
        self,
        entrada: AtaNotasEntrada,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        turma = self.repo.buscar_turma_completa(entrada.turma_id)
        if turma is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turma não encontrada.",
            )

        matriculas = self.repo.listar_matriculas_da_turma_com_notas_e_frequencias(entrada.turma_id)
        if not matriculas:
            raise HTTPException(
                status_code=HTTP_422,
                detail="Não é possível emitir ata de notas finais para turma sem estudantes matriculados.",
            )

        resultados: list[dict[str, Any]] = []
        aprovados = 0
        reprovados_nota = 0
        reprovados_falta = 0
        soma_medias = 0.0

        for mat in matriculas:
            apurado = self._apurar_frequencia_e_notas(mat)
            media_final = apurado["media_consolidada"]
            if media_final is None:
                raise HTTPException(
                    status_code=HTTP_422,
                    detail=(
                        f"Pendência de fechamento: o estudante de matrícula {mat['aluno_matricula']} "
                        f"não possui avaliações ou média final consolidada."
                    ),
                )

            percentual_freq = float(apurado["percentual_frequencia"])
            if percentual_freq < FREQUENCIA_MINIMA_PERCENTUAL:
                situacao_final = SituacaoFinalTurmaEnum.REPROVADO_FALTA.value
                reprovados_falta += 1
            elif media_final >= entrada.media_minima_aprovacao:
                situacao_final = SituacaoFinalTurmaEnum.APROVADO.value
                aprovados += 1
            else:
                situacao_final = SituacaoFinalTurmaEnum.REPROVADO_NOTA.value
                reprovados_nota += 1

            soma_medias += media_final
            resultados.append(
                {
                    "matricula": int(mat["aluno_matricula"]),
                    "nome": str(mat["aluno_nome"] or ""),
                    "media_final": media_final,
                    "percentual_frequencia": percentual_freq,
                    "situacao_final": situacao_final,
                }
            )

        media_geral = round(soma_medias / len(resultados), 2)
        conteudo = {
            "turma": {
                "id_turma": int(turma["id_turma"]),
                "codigo_turma": str(turma["codigo_turma"]),
                "turno": str(turma["turno"]),
                "status_turma": str(turma["status_turma"]),
            },
            "periodo_letivo": {
                "codigo": str(turma["periodo_codigo"]),
                "ano": int(turma["periodo_ano"]),
                "semestre": int(turma["periodo_semestre"]),
            },
            "disciplina": {
                "codigo": str(turma["disciplina_codigo"]),
                "nome": str(turma["disciplina_nome"]),
                "carga_horaria": int(turma["disciplina_carga_horaria"]),
                "creditos": int(turma["disciplina_creditos"]),
            },
            "professor": (
                {
                    "id": int(turma["professor_id"]),
                    "nome": str(turma["professor_nome"]),
                    "titulacao": str(turma["professor_titulacao"]),
                }
                if turma["professor_id"] is not None
                else None
            ),
            "media_minima_aprovacao": round(float(entrada.media_minima_aprovacao), 2),
            "frequencia_minima_percentual": FREQUENCIA_MINIMA_PERCENTUAL,
            "resultados": resultados,
            "resumo": {
                "total_matriculados": len(resultados),
                "aprovados": aprovados,
                "reprovados_nota": reprovados_nota,
                "reprovados_falta": reprovados_falta,
                "media_geral_turma": media_geral,
            },
            "observacoes": entrada.observacoes,
        }

        return self._emitir_e_custodiar(
            tipo_documento=TipoDocumentoEnum.ATA_NOTAS.value,
            conteudo=conteudo,
            portaria_referencia=entrada.portaria_referencia.value,
            operador=operador,
            ip_origem=ip_origem,
            turma_id=int(turma["id_turma"]),
        )

    # ------------------------------------------------------------------
    # US2: Diploma Digital
    # ------------------------------------------------------------------

    def emitir_diploma_digital(
        self,
        entrada: DiplomaDigitalEntrada,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        if entrada.instituicao_terceira or entrada.registrar_blockchain:
            raise HTTPException(
                status_code=HTTP_422,
                detail=(
                    "Emissão e registro em blockchain de diplomas de instituições terceiras "
                    "estão fora do escopo institucional da versão inicial."
                ),
            )

        aluno = self.repo.buscar_aluno_com_curso(entrada.aluno_matricula)
        if aluno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado.",
            )

        if aluno["curso_id"] is None:
            raise HTTPException(
                status_code=HTTP_422,
                detail="Estudante inelegível: nenhum curso institucional vinculado ao cadastro.",
            )

        status_atual = str(aluno["status_academico"])
        if status_atual != "FORMADO":
            raise HTTPException(
                status_code=HTTP_422,
                detail=(
                    f"Estudante inelegível para diploma digital: situação acadêmica atual é "
                    f"'{status_atual}' (exigido 'FORMADO')."
                ),
            )

        curso_id = int(aluno["curso_id"])
        ch_curso = int(aluno["curso_carga_horaria_total"])
        ch_integralizada = (
            int(entrada.carga_horaria_integralizada)
            if entrada.carga_horaria_integralizada is not None
            else ch_curso
        )
        if ch_integralizada < ch_curso:
            raise HTTPException(
                status_code=HTTP_422,
                detail=(
                    f"Carga horária integralizada ({ch_integralizada}h) é inferior à carga horária "
                    f"total exigida pelo curso ({ch_curso}h)."
                ),
            )

        diploma_ativo = self.repo.buscar_diploma_ativo_por_aluno_e_curso(entrada.aluno_matricula, curso_id)
        if diploma_ativo is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Já existe um diploma digital válido e ativo para a matrícula "
                    f"{entrada.aluno_matricula} neste curso (código {diploma_ativo['codigo_verificacao']}). "
                    f"Revogue o documento vigente antes de emitir substituto."
                ),
            )

        if entrada.numero_registro is not None:
            if self.repo.buscar_por_numero_registro(entrada.numero_registro) is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe um documento emitido com esse número de registro.",
                )
            numero_registro = entrada.numero_registro
        else:
            numero_registro = self.repo.gerar_numero_registro_diploma(
                ano_base=entrada.data_colacao_grau.year
            )

        conteudo = {
            "diplomado": {
                "matricula": int(aluno["matricula"]),
                "nome": str(aluno["nome"] or ""),
                "status_academico": status_atual,
                "ira": round(float(aluno["ira"]), 2),
            },
            "curso": {
                "curso_id": curso_id,
                "nome": str(aluno["curso_nome"]),
                "codigo_mec": str(aluno["curso_codigo_mec"]),
                "grau_academico": str(aluno["curso_grau_academico"]),
                "modalidade": str(aluno["curso_modalidade"]),
                "carga_horaria_total": ch_curso,
                "carga_horaria_integralizada": ch_integralizada,
            },
            "expedicao": {
                "data_conclusao": entrada.data_conclusao.isoformat(),
                "data_colacao_grau": entrada.data_colacao_grau.isoformat(),
                "numero_registro": numero_registro,
                "livro_registro": entrada.livro_registro,
                "folha_registro": entrada.folha_registro,
            },
            "observacoes": entrada.observacoes,
        }

        return self._emitir_e_custodiar(
            tipo_documento=TipoDocumentoEnum.DIPLOMA_DIGITAL.value,
            conteudo=conteudo,
            portaria_referencia=entrada.portaria_referencia.value,
            operador=operador,
            ip_origem=ip_origem,
            aluno_matricula=int(aluno["matricula"]),
            curso_id=curso_id,
            numero_registro=numero_registro,
        )

    # ------------------------------------------------------------------
    # US3: Validação Pública (LGPD), Listagem, Detalhe, Integridade e Revogação
    # ------------------------------------------------------------------

    @staticmethod
    def _montar_resumo_publico_lgpd(doc: dict[str, Any]) -> dict[str, Any]:
        """Retorna somente metadados mínimos públicos sem qualquer dado pessoal sensível."""
        conteudo = doc["conteudo"]
        tipo = doc["tipo_documento"]
        if tipo == TipoDocumentoEnum.DIPLOMA_DIGITAL.value:
            diplomado = conteudo.get("diplomado", {})
            curso = conteudo.get("curso", {})
            expedicao = conteudo.get("expedicao", {})
            return {
                "titular_nome": diplomado.get("nome"),
                "curso_nome": curso.get("nome"),
                "codigo_mec": curso.get("codigo_mec"),
                "grau_academico": curso.get("grau_academico"),
                "modalidade": curso.get("modalidade"),
                "carga_horaria_integralizada": curso.get("carga_horaria_integralizada"),
                "data_conclusao": expedicao.get("data_conclusao"),
                "data_colacao_grau": expedicao.get("data_colacao_grau"),
                "numero_registro": expedicao.get("numero_registro"),
            }

        turma = conteudo.get("turma", {})
        disciplina = conteudo.get("disciplina", {})
        periodo = conteudo.get("periodo_letivo", {})
        professor = conteudo.get("professor") or {}
        resumo = conteudo.get("resumo", {})
        base = {
            "codigo_turma": turma.get("codigo_turma"),
            "disciplina_codigo": disciplina.get("codigo"),
            "disciplina_nome": disciplina.get("nome"),
            "periodo_letivo": periodo.get("codigo"),
            "professor_nome": professor.get("nome"),
            "total_matriculados": resumo.get("total_matriculados"),
        }
        if tipo == TipoDocumentoEnum.ATA_NOTAS.value:
            base.update(
                {
                    "aprovados": resumo.get("aprovados"),
                    "reprovados_nota": resumo.get("reprovados_nota"),
                    "reprovados_falta": resumo.get("reprovados_falta"),
                }
            )
        return base

    def validar_documento_publico(self, codigo_verificacao: str) -> dict[str, Any]:
        codigo_limpo = codigo_verificacao.strip()
        if not codigo_limpo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento não encontrado para o código de verificação informado.",
            )

        doc = self.repo.buscar_documento_por_codigo(codigo_limpo)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento não encontrado para o código de verificação informado.",
            )

        acervo = doc["acervo_mec"]
        hash_recalculado = calcular_hash_sha256(doc["conteudo_json_bruto"])
        hash_ok = hmac.compare_digest(hash_recalculado, doc["hash_sha256"])
        assinatura_ok = verificar_assinatura_icp_brasil(
            assinatura_armazenada=acervo["assinatura_icp_brasil"],
            hash_sha256=doc["hash_sha256"],
            carimbo_tempo=acervo["carimbo_tempo"],
            portaria_referencia=acervo["portaria_referencia"],
            codigo_verificacao=doc["codigo_verificacao"],
        )

        if not doc["valido"] or acervo["status_custodia"] == StatusCustodiaEnum.REVOGADO.value:
            autentico = False
            status_validacao = "REVOGADO"
        elif not hash_ok or not assinatura_ok or acervo["status_custodia"] == StatusCustodiaEnum.CORROMPIDO.value:
            autentico = False
            status_validacao = "CORROMPIDO"
        else:
            autentico = True
            status_validacao = "VALIDO"

        return {
            "autentico": autentico,
            "status_validacao": status_validacao,
            "codigo_verificacao": doc["codigo_verificacao"],
            "tipo_documento": doc["tipo_documento"],
            "emitido_em": doc["emitido_em"],
            "hash_sha256": doc["hash_sha256"],
            "resumo_publico": self._montar_resumo_publico_lgpd(doc),
            "custodia_mec": {
                "portaria_referencia": acervo["portaria_referencia"],
                "formato_arquivo": acervo["formato_arquivo"],
                "carimbo_tempo": acervo["carimbo_tempo"],
                "prazo_guarda": acervo["prazo_guarda"],
                "status_custodia": (
                    StatusCustodiaEnum.CORROMPIDO.value
                    if status_validacao == "CORROMPIDO"
                    else acervo["status_custodia"]
                ),
            },
            "motivo_revogacao": doc["motivo_revogacao"],
            "revogado_em": doc["revogado_em"],
        }

    def listar_documentos(
        self,
        tipo_documento: Optional[str] = None,
        aluno_matricula: Optional[int] = None,
        turma_id: Optional[int] = None,
        periodo_letivo_codigo: Optional[str] = None,
        valido: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        return self.repo.listar_documentos(
            tipo_documento=tipo_documento,
            aluno_matricula=aluno_matricula,
            turma_id=turma_id,
            periodo_letivo_codigo=periodo_letivo_codigo,
            valido=valido,
        )

    def obter_documento(self, id_documento: int) -> dict[str, Any]:
        doc = self.repo.buscar_documento_por_id(id_documento)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento acadêmico não encontrado.",
            )
        return _extrair_publico_documento(doc)

    def verificar_integridade_documento(
        self,
        id_documento: int,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        doc = self.repo.buscar_documento_por_id(id_documento)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento acadêmico não encontrado.",
            )

        acervo = doc["acervo_mec"]
        hash_recalculado = calcular_hash_sha256(doc["conteudo_json_bruto"])
        hash_ok = hmac.compare_digest(hash_recalculado, doc["hash_sha256"])
        assinatura_ok = verificar_assinatura_icp_brasil(
            assinatura_armazenada=acervo["assinatura_icp_brasil"],
            hash_sha256=doc["hash_sha256"],
            carimbo_tempo=acervo["carimbo_tempo"],
            portaria_referencia=acervo["portaria_referencia"],
            codigo_verificacao=doc["codigo_verificacao"],
        )
        integro = hash_ok and assinatura_ok

        status_anterior = str(acervo["status_custodia"])
        atualizar_custodia = False
        novo_status = status_anterior
        if not integro and status_anterior != StatusCustodiaEnum.REVOGADO.value:
            novo_status = StatusCustodiaEnum.CORROMPIDO.value
            atualizar_custodia = True

        verificado_em = datetime.now(timezone.utc).isoformat()
        dados_anteriores_json = serializar_snapshot_auditoria({"status_custodia": status_anterior})
        dados_novos_json = serializar_snapshot_auditoria(
            {
                "codigo_verificacao": doc["codigo_verificacao"],
                "integro": integro,
                "assinatura_valida": assinatura_ok,
                "status_custodia": novo_status,
            }
        )
        assert dados_novos_json is not None

        self.repo.registrar_verificacao_integridade(
            id_documento=id_documento,
            novo_status_custodia=novo_status,
            atualizar_custodia=atualizar_custodia,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            dados_anteriores_json=dados_anteriores_json,
            dados_novos_json=dados_novos_json,
            verificado_em=verificado_em,
        )

        return {
            "id_documento": id_documento,
            "codigo_verificacao": doc["codigo_verificacao"],
            "integro": integro,
            "hash_armazenado": doc["hash_sha256"],
            "hash_recalculado": hash_recalculado,
            "assinatura_valida": assinatura_ok,
            "status_custodia": novo_status,
            "verificado_em": verificado_em,
        }

    def revogar_documento(
        self,
        id_documento: int,
        entrada: RevogacaoDocumentoEntrada,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        doc = self.repo.buscar_documento_por_id(id_documento)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento acadêmico não encontrado.",
            )

        if not doc["valido"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este documento acadêmico já se encontra revogado.",
            )

        revogado_em = datetime.now(timezone.utc).isoformat()
        dados_anteriores_json = serializar_snapshot_auditoria(
            {
                "valido": True,
                "status_custodia": doc["acervo_mec"]["status_custodia"],
                "motivo_revogacao": None,
            }
        )
        dados_novos_json = serializar_snapshot_auditoria(
            {
                "valido": False,
                "status_custodia": StatusCustodiaEnum.REVOGADO.value,
                "motivo_revogacao": entrada.motivo,
                "revogado_em": revogado_em,
            }
        )
        assert dados_anteriores_json is not None and dados_novos_json is not None

        atualizado = self.repo.revogar_documento_atomico(
            id_documento=id_documento,
            motivo_revogacao=entrada.motivo,
            revogado_em=revogado_em,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            dados_anteriores_json=dados_anteriores_json,
            dados_novos_json=dados_novos_json,
        )
        return _extrair_publico_documento(atualizado)

    # ------------------------------------------------------------------
    # US4: Auditoria LGPD
    # ------------------------------------------------------------------

    def listar_auditoria(self, id_documento: Optional[str] = None) -> list[dict[str, Any]]:
        return self.repo.listar_auditoria(id_documento=id_documento)
