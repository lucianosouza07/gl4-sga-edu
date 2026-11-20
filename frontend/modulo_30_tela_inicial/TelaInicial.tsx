import React, { useEffect, useState, useCallback } from "react";
import type { ResumoMetricas } from "../professor";
import { listarProfessores } from "../api";

interface Props {
  onNavegar: (pagina: "home" | "professores" | "login") => void;
  onIrParaLogin?: () => void;
  isOnline: boolean;
}

/**
 * TelaInicial — SGA-Edu (Campus II)
 * Tela Inicial Pública institucional alinhada rigorosamente ao protótipo (DESIGN.md / prototipo v3).
 * 1. O recurso "Opções de Acesso por Perfil de Usuário" foi removido.
 * 2. O acesso se dá exclusivamente por matrícula e senha (o registro define o perfil).
 * 3. O design está 100% alinhado às demais telas baseadas no protótipo (KPIs, tabela, widgets, ondas).
 */
const TelaInicial: React.FC<Props> = ({ onNavegar, isOnline }) => {
  const [metricas, setMetricas] = useState<ResumoMetricas>({
    totalProfessores: 0,
    modulosAtivos: 1,
  });

  const carregarMetricas = useCallback(async () => {
    try {
      const professores = await listarProfessores();
      setMetricas((prev) => ({ ...prev, totalProfessores: professores.length }));
    } catch {
      // Backend offline ou erro de rede — mantém 0
    }
  }, []);

  useEffect(() => {
    carregarMetricas();
  }, [carregarMetricas]);

  return (
    <section className="content-body" aria-label="Conteúdo Principal">
      {/* 1. ÁREA DE TÍTULO DA PÁGINA (Alinhado ao protótipo) */}
      <div className="page-title-area">
        <div>
          <h1 className="greeting-title">Portal Acadêmico SGA-Edu</h1>
          <p className="greeting-subtitle">
            Universidade do Estado da Bahia · Campus II (Alagoinhas) · Semestre Letivo 2026.2
          </p>
        </div>
      </div>

      {/* 2. GRADE DE 4 CARDS KPI (Idêntica ao protótipo com paleta pastel) */}
      <section className="kpi-grid" aria-label="Indicadores Chave do Sistema">
        <div className="kpi-card kpi-green">
          <div className="kpi-info">
            <span className="kpi-label" title="Semestre Letivo">Semestre Letivo</span>
            <span className="kpi-value">2026.2</span>
          </div>
          <div className="kpi-icon-box">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
          </div>
        </div>

        <div className="kpi-card kpi-purple">
          <div className="kpi-info">
            <span className="kpi-label" title="Professores Cadastrados">Professores Cadastrados</span>
            <span className="kpi-value">{metricas.totalProfessores}</span>
          </div>
          <div className="kpi-icon-box">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
        </div>

        <div className="kpi-card kpi-yellow">
          <div className="kpi-info">
            <span className="kpi-label" title="Módulos do Sistema">Módulos do Sistema</span>
            <span className="kpi-value">6 Módulos</span>
          </div>
          <div className="kpi-icon-box">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
            </svg>
          </div>
        </div>

        <div className="kpi-card kpi-pink">
          <div className="kpi-info">
            <span className="kpi-label" title="Status da API">Status da API</span>
            <span className="kpi-value">{isOnline ? "Online" : "Operacional"}</span>
          </div>
          <div className="kpi-icon-box">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="12" x2="2" y2="12" />
              <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
              <line x1="6" y1="16" x2="6.01" y2="16" />
              <line x1="10" y1="16" x2="10.01" y2="16" />
            </svg>
          </div>
        </div>
      </section>

      {/* 3. TABELA DE MÓDULOS INTEGRADOS DO SGA-Edu */}
      <div className="card">
        <h3 className="card-title">
          <span>Módulos Integrados do SGA-Edu</span>
          <span style={{ fontSize: "12px", color: "var(--on-surface-variant)", fontWeight: 500 }}>
            Sprint 01 & Cronograma
          </span>
        </h3>

        <div className="table-wrap">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Módulo</th>
                <th>Descrição</th>
                <th>História / Requisito</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="td-main" title="Cadastro de Professores">
                  👨‍🏫 Cadastro de Professores
                </td>
                <td className="td-sub" title="Gestão completa do corpo docente">
                  Gestão completa do corpo docente
                </td>
                <td className="td-date">GL4-34 / SGA-16</td>
                <td>
                  <span className="badge badge-success">Ativo</span>
                </td>
                <td className="td-status">
                  <button
                    className="btn btn-primario btn-sm"
                    onClick={() => onNavegar("professores")}
                    style={{ padding: "6px 14px", fontSize: "12px", borderRadius: "var(--radius-sm)" }}
                  >
                    Acessar Módulo →
                  </button>
                </td>
              </tr>

              <tr>
                <td className="td-main" title="Cadastro de Alunos">
                  🎓 Cadastro de Alunos
                </td>
                <td className="td-sub" title="Base discente e matrículas">
                  Base discente e matrículas
                </td>
                <td className="td-date">SGA-15</td>
                <td>
                  <span className="badge badge-warning">Em breve</span>
                </td>
                <td className="td-status">
                  <span style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}>Sprint 01</span>
                </td>
              </tr>

              <tr>
                <td className="td-main" title="Disciplinas & Matrizes">
                  📚 Disciplinas & Matrizes
                </td>
                <td className="td-sub" title="Estrutura curricular e ementas">
                  Estrutura curricular e ementas
                </td>
                <td className="td-date">SGA-23</td>
                <td>
                  <span className="badge badge-warning">Em breve</span>
                </td>
                <td className="td-status">
                  <span style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}>Fase 2</span>
                </td>
              </tr>

              <tr>
                <td className="td-main" title="Turmas & Horários">
                  🏫 Turmas & Horários
                </td>
                <td className="td-sub" title="Alocação de salas e ensalamento">
                  Alocação de salas e ensalamento
                </td>
                <td className="td-date">Acadêmico</td>
                <td>
                  <span className="badge badge-warning">Em breve</span>
                </td>
                <td className="td-status">
                  <span style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}>Fase 2</span>
                </td>
              </tr>

              <tr>
                <td className="td-main" title="Notas & Frequência">
                  📊 Notas & Frequência
                </td>
                <td className="td-sub" title="Lançamento e diário digital">
                  Lançamento e diário digital
                </td>
                <td className="td-date">Docente</td>
                <td>
                  <span className="badge badge-warning">Em breve</span>
                </td>
                <td className="td-status">
                  <span style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}>Fase 3</span>
                </td>
              </tr>

              <tr>
                <td className="td-main" title="Relatórios & Atas">
                  📄 Relatórios & Atas
                </td>
                <td className="td-sub" title="Históricos e diplomas digitais">
                  Históricos e diplomas digitais
                </td>
                <td className="td-date">SGA-25</td>
                <td>
                  <span className="badge badge-warning">Em breve</span>
                </td>
                <td className="td-status">
                  <span style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}>Fase 2</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. RODAPÉ ORGÂNICO (ONDAS) IDÊNTICO ÀS DEMAIS TELAS */}
      <footer className="footer-waves" aria-hidden="true" style={{ left: 0, width: "100%" }}>
        <svg viewBox="0 0 1180 60" preserveAspectRatio="none" fill="none">
          <path d="M0,35 C150,10 300,55 450,30 C600,5 750,50 900,25 C1050,0 1150,30 1180,35 L1180,60 L0,60 Z" fill="#5B2333" opacity="0.08" />
          <path d="M0,45 C200,25 400,60 600,40 C800,20 1000,55 1180,42 L1180,60 L0,60 Z" fill="#5B2333" opacity="0.15" />
        </svg>
      </footer>
    </section>
  );
};

export default TelaInicial;
