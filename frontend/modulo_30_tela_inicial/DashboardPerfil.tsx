import React from "react";
import { PERFIS, PerfilId } from "./perfisDados";

interface Props {
  perfilId: PerfilId;
  onNavegar: (pagina: "home" | "professores" | "login") => void;
  onLogout: () => void;
}

export const DashboardPerfil: React.FC<Props> = ({ perfilId, onNavegar, onLogout }) => {
  const profile = PERFIS[perfilId] || PERFIS.discente;

  // Render SVG icons helper
  const renderIcon = (iconName: string) => {
    switch (iconName) {
      case "home":
        return <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>;
      case "book-open":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /></svg>;
      case "user-x":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="8.5" cy="7" r="4" /><line x1="18" y1="8" x2="23" y2="13" /><line x1="23" y1="8" x2="18" y2="13" /></svg>;
      case "award":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="7" /><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88" /></svg>;
      case "alert-circle":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>;
      case "users":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>;
      case "user-check":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="8.5" cy="7" r="4" /><polyline points="17 11 19 13 23 9" /></svg>;
      case "edit-3":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" /></svg>;
      case "user":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>;
      case "folder":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>;
      case "check-circle":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>;
      case "user-minus":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="8.5" cy="7" r="4" /><line x1="23" y1="11" x2="17" y2="11" /></svg>;
      case "message-circle":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" /></svg>;
      case "clock":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>;
      case "hard-drive":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="12" x2="2" y2="12" /><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /><line x1="6" y1="16" x2="6.01" y2="16" /><line x1="10" y1="16" x2="10.01" y2="16" /></svg>;
      case "alert-triangle":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>;
      case "dollar-sign":
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>;
      default:
        return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg>;
    }
  };

  return (
    <div className="app-container">
      {/* SIDEBAR NAVEGAÇÃO LATERAL (260px) */}
      <aside className="sidebar" aria-label="Navegação Lateral">
        <div>
          {/* BRAND IDENTIFIER */}
          <div className="sidebar-brand" onClick={() => onNavegar("home")}>
            <div className="brand-icon" aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                <path d="M6 12v5c3 3 9 3 12 0v-5" />
              </svg>
            </div>
            <div className="brand-info">
              <span className="brand-name">SGA-Edu</span>
              <span className="brand-subtitle">PORTAL ACADÊMICO</span>
            </div>
          </div>

          {/* MENU ITENS DO PERFIL */}
          <nav className="sidebar-nav" aria-label="Menu Principal">
            {profile.navItems.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${item.active ? "active" : ""}`}
                onClick={() => {
                  if (item.id === "professores" || item.id === "corpo") {
                    onNavegar("professores");
                  }
                }}
              >
                {renderIcon(item.icon)}
                <span className="nav-label">{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* USUÁRIO LOGADO */}
        <div className="sidebar-user">
          <div className="user-avatar" aria-hidden="true">
            {profile.avatarText}
          </div>
          <div className="user-meta">
            <div className="user-name" title={profile.name}>{profile.name}</div>
            <div className="user-role" title={profile.role}>{profile.role}</div>
          </div>
          <button
            className="btn-logout"
            title="Sair / Trocar de perfil"
            aria-label="Sair"
            onClick={onLogout}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </aside>

      {/* MAIN WRAPPER */}
      <main className="main-wrapper">
        {/* CABEÇALHO */}
        <header className="app-header">
          <div className="header-actions" style={{ marginLeft: "auto" }}>
            <div className="search-box">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="text"
                placeholder="Buscar disciplinas, avisos, processos, notas..."
                aria-label="Campo de busca"
              />
            </div>

            <button className="notif-btn" title="Notificações" aria-label="Notificações">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </button>
            {profile.id === "ti_suporte" ? (
              <span className="status-pill">
                <span className="dot" />
                Status: Operacional • Tempo Real
              </span>
            ) : (
              <span className="semester-badge">
                Semestre Ativo: <strong>2026.2</strong>
              </span>
            )}
          </div>
        </header>

        {/* CORPO PRINCIPAL */}
        <section className="content-body">
          <div className="page-title-area">
            <div>
              <h1 className="greeting-title">{profile.title}</h1>
              <p className="greeting-subtitle">{profile.subtitle}</p>
            </div>
            {(profile.id === "docente" || profile.id === "colegiado") && (
              <button
                className="btn btn-primario btn-sm"
                onClick={() => onNavegar("professores")}
              >
                👨‍🏫 Gerenciar Professores (GL4-34)
              </button>
            )}
          </div>

          {/* GRADE KPI (4 CARDS) */}
          <section className="kpi-grid" aria-label="Indicadores Chave">
            {profile.kpis.map((kpi, idx) => (
              <div key={idx} className={`kpi-card ${kpi.colorClass}`}>
                <div className="kpi-info">
                  <span className="kpi-label" title={kpi.label}>{kpi.label}</span>
                  <span className="kpi-value" title={kpi.value}>{kpi.value}</span>
                </div>
                <div className="kpi-icon-box">
                  {renderIcon(kpi.icon)}
                </div>
              </div>
            ))}
          </section>

          {/* CONTEÚDO ESPECÍFICO DE CADA DASHBOARD */}
          {profile.id === "discente" && (
            <div className="main-dashboard-grid">
              <div className="center-column">
                <div className="two-card-row">
                  {/* Desempenho por Disciplina */}
                  <div className="card">
                    <h3 className="card-title">Desempenho por Disciplina</h3>
                    <div className="progress-list">
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Eng. Requisitos</span><strong>92%</strong></div>
                        <div className="progress-track"><div className="progress-fill verde" style={{ width: "92%" }} /></div>
                      </div>
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Arq. Software</span><strong>85%</strong></div>
                        <div className="progress-track"><div className="progress-fill vinho" style={{ width: "85%" }} /></div>
                      </div>
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Prog. OO</span><strong>78%</strong></div>
                        <div className="progress-track"><div className="progress-fill verde" style={{ width: "78%" }} /></div>
                      </div>
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Banco Dados II</span><strong>88%</strong></div>
                        <div className="progress-track"><div className="progress-fill vinho" style={{ width: "88%" }} /></div>
                      </div>
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Estrut. Dados</span><strong>70%</strong></div>
                        <div className="progress-track"><div className="progress-fill verde" style={{ width: "70%" }} /></div>
                      </div>
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Métodos Ágeis</span><strong>95%</strong></div>
                        <div className="progress-track"><div className="progress-fill vinho" style={{ width: "95%" }} /></div>
                      </div>
                    </div>
                  </div>

                  {/* Próximas Atividades */}
                  <div className="card">
                    <h3 className="card-title">Próximas Atividades</h3>
                    <div className="table-wrap">
                      <table className="custom-table">
                        <thead>
                          <tr>
                            <th>Disciplina</th>
                            <th>Atividade</th>
                            <th>Prazo</th>
                            <th style={{ textAlign: "right" }}>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="td-main" title="Eng. de Requisitos">Eng. de Requisitos</td>
                            <td className="td-sub" title="Atividade 3">Atividade 3</td>
                            <td className="td-date">12 Set</td>
                            <td className="td-status"><span className="badge badge-success">Entregue</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Arquitetura de Soft.">Arquitetura de Soft.</td>
                            <td className="td-sub" title="Trabalho Final">Trabalho Final</td>
                            <td className="td-date">15 Set</td>
                            <td className="td-status"><span className="badge badge-warning">Pendente</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Prog. Orientada a Obj.">Prog. Orientada a Obj.</td>
                            <td className="td-sub" title="Mini-teste 2">Mini-teste 2</td>
                            <td className="td-date">18 Set</td>
                            <td className="td-status"><span className="badge badge-warning">Pendente</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Banco de Dados II">Banco de Dados II</td>
                            <td className="td-sub" title="Estudo de Caso">Estudo de Caso</td>
                            <td className="td-date">08 Set</td>
                            <td className="td-status"><span className="badge badge-danger">Atrasado</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Estruturas de Dados">Estruturas de Dados</td>
                            <td className="td-sub" title="Lab Prático 4">Lab Prático 4</td>
                            <td className="td-date">22 Set</td>
                            <td className="td-status"><span className="badge badge-warning">Pendente</span></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>

              {/* Coluna Widgets */}
              <div className="widgets-column">
                <div className="card">
                  <div className="mini-calendar">
                    <div className="calendar-header">
                      <span>Setembro 2026</span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                        <line x1="16" y1="2" x2="16" y2="6" />
                        <line x1="8" y1="2" x2="8" y2="6" />
                        <line x1="3" y1="10" x2="21" y2="10" />
                      </svg>
                    </div>
                    <div className="calendar-grid">
                      <div className="cal-day-head">D</div><div className="cal-day-head">S</div><div className="cal-day-head">T</div>
                      <div className="cal-day-head">Q</div><div className="cal-day-head">Q</div><div className="cal-day-head">S</div><div className="cal-day-head">S</div>
                      <div className="cal-day" /><div className="cal-day" /><div className="cal-day">1</div>
                      <div className="cal-day">2</div><div className="cal-day">3</div><div className="cal-day">4</div><div className="cal-day">5</div>
                      <div className="cal-day">6</div><div className="cal-day">7</div><div className="cal-day">8</div>
                      <div className="cal-day">9</div><div className="cal-day">10</div><div className="cal-day">11</div><div className="cal-day">12</div>
                      <div className="cal-day">13</div><div className="cal-day">14</div><div className="cal-day active">15</div>
                      <div className="cal-day">16</div><div className="cal-day">17</div><div className="cal-day">18</div><div className="cal-day">19</div>
                      <div className="cal-day">20</div><div className="cal-day">21</div><div className="cal-day">22</div>
                      <div className="cal-day">23</div><div className="cal-day">24</div><div className="cal-day">25</div><div className="cal-day">26</div>
                      <div className="cal-day">27</div><div className="cal-day">28</div><div className="cal-day">29</div><div className="cal-day">30</div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3 className="card-title">Avisos Recentes</h3>
                  <div className="notice-list">
                    <div className="notice-item">
                      <div className="notice-head"><span>Matrícula 2026.2</span><span className="notice-time">Há 1h</span></div>
                      <p className="notice-desc">Ajuste acadêmico inicia dia 15/09 na secretaria do Campus II.</p>
                    </div>
                    <div className="notice-item">
                      <div className="notice-head"><span>Biblioteca Central</span><span className="notice-time">Ontem</span></div>
                      <p className="notice-desc">Devolução de livros pendentes prorrogada até sexta.</p>
                    </div>
                    <div className="notice-item">
                      <div className="notice-head"><span>Semana de Soft.</span><span className="notice-time">2 dias atrás</span></div>
                      <p className="notice-desc">Inscrições abertas para oficinas práticas gratuitas.</p>
                    </div>
                  </div>
                </div>

                <div className="action-buttons-card">
                  <button className="btn-action-primary">
                    Solicitar Matrícula
                  </button>
                  <button className="btn-action-secondary">
                    Emitir Histórico Escolar
                  </button>
                </div>
              </div>
            </div>
          )}

          {profile.id === "docente" && (
            <div className="main-dashboard-grid">
              <div className="center-column">
                <div className="two-card-row">
                  {/* Minhas Turmas */}
                  <div className="card">
                    <h3 className="card-title">Minhas Turmas</h3>
                    <div className="table-wrap">
                      <table className="custom-table">
                        <thead>
                          <tr>
                            <th>Disciplina</th>
                            <th>Turma</th>
                            <th>Horário</th>
                            <th>Alunos</th>
                            <th style={{ textAlign: "right" }}>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="td-main" title="Engenharia de Software">Engenharia de Software</td>
                            <td className="td-sub">T01</td>
                            <td className="td-date">Seg/Qua 08h</td>
                            <td>42</td>
                            <td className="td-status"><span className="badge badge-success">Ativo</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Introdução à Computação">Introdução à Computação</td>
                            <td className="td-sub">T03</td>
                            <td className="td-date">Seg/Qua 10h</td>
                            <td>45</td>
                            <td className="td-status"><span className="badge badge-success">Ativo</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Estruturas de Dados II">Estruturas de Dados II</td>
                            <td className="td-sub">T01</td>
                            <td className="td-date">Ter/Qui 08h</td>
                            <td>40</td>
                            <td className="td-status"><span className="badge badge-success">Ativo</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Orientação de Trabalho">Orientação de Trabalho</td>
                            <td className="td-sub">T02</td>
                            <td className="td-date">Sexta 14h</td>
                            <td>5</td>
                            <td className="td-status"><span className="badge badge-success">Ativo</span></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Frequência por Turma */}
                  <div className="card">
                    <h3 className="card-title">Frequência por Turma</h3>
                    <div className="progress-list">
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Engenharia de Software (T01)</span><strong>94%</strong></div>
                        <div className="progress-track"><div className="progress-fill verde" style={{ width: "94%" }} /></div>
                      </div>
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Introdução à Computação (T03)</span><strong>89%</strong></div>
                        <div className="progress-track"><div className="progress-fill lilas" style={{ width: "89%" }} /></div>
                      </div>
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Estruturas de Dados II (T01)</span><strong>91%</strong></div>
                        <div className="progress-track"><div className="progress-fill verde" style={{ width: "91%" }} /></div>
                      </div>
                      <div className="progress-item">
                        <div className="progress-item-head"><span>Orientação de Trabalho (T02)</span><strong>98%</strong></div>
                        <div className="progress-track"><div className="progress-fill lilas" style={{ width: "98%" }} /></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Coluna Widgets Docente */}
              <div className="widgets-column">
                <div className="card">
                  <h3 className="card-title">Agenda da Semana</h3>
                  <div className="notice-list">
                    <div className="notice-item">
                      <div className="notice-head"><span>Aula Eng. Software</span><span className="notice-time">Terça, 08:00</span></div>
                      <p className="notice-desc">Sala 104 · Campus II</p>
                    </div>
                    <div className="notice-item">
                      <div className="notice-head"><span>Reunião de Departamento</span><span className="notice-time">Terça, 14:00</span></div>
                      <p className="notice-desc">Sala de Reuniões 02</p>
                    </div>
                    <div className="notice-item">
                      <div className="notice-head"><span>Aula Int. Computação</span><span className="notice-time">Quarta, 10:00</span></div>
                      <p className="notice-desc">Lab 03</p>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3 className="card-title">Prazos Acadêmicos</h3>
                  <div className="notice-list">
                    <div className="notice-item">
                      <div className="notice-head"><span>Notas Unidade I</span><span className="notice-time" style={{ color: "var(--error-text)" }}>Até 20/09</span></div>
                      <p className="notice-desc">Prazo final de digitação no sistema.</p>
                    </div>
                    <div className="notice-item">
                      <div className="notice-head"><span>Planos de Ensino</span><span className="notice-time">Até 12/09</span></div>
                      <p className="notice-desc">Aprovação pendente da coordenação.</p>
                    </div>
                  </div>
                </div>

                <div className="action-buttons-card">
                  <button className="btn-action-primary" onClick={() => onNavegar("professores")}>
                    Cadastrar / Gerenciar Professores
                  </button>
                  <button className="btn-action-secondary">
                    Lançar Frequência
                  </button>
                </div>
              </div>
            </div>
          )}

          {profile.id === "colegiado" && (
            <div className="main-dashboard-grid">
              <div className="center-column">
                <div className="two-card-row">
                  {/* Processos Recentes */}
                  <div className="card">
                    <h3 className="card-title">Processos Recentes</h3>
                    <div className="table-wrap">
                      <table className="custom-table">
                        <thead>
                          <tr>
                            <th>Protocolo</th>
                            <th>Tipo</th>
                            <th>Solicitante</th>
                            <th>Data</th>
                            <th style={{ textAlign: "right" }}>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="td-date">2026.1092</td>
                            <td className="td-main" title="Aprov. Disciplinas">Aprov. Disciplinas</td>
                            <td className="td-sub" title="Gabriel Souza">Gabriel Souza</td>
                            <td className="td-date">10 Set</td>
                            <td className="td-status"><span className="badge badge-success">Deferido</span></td>
                          </tr>
                          <tr>
                            <td className="td-date">2026.1091</td>
                            <td className="td-main" title="Quebra de Pré-req.">Quebra de Pré-req.</td>
                            <td className="td-sub" title="Beatriz Lima">Beatriz Lima</td>
                            <td className="td-date">09 Set</td>
                            <td className="td-status"><span className="badge badge-warning">Em análise</span></td>
                          </tr>
                          <tr>
                            <td className="td-date">2026.1090</td>
                            <td className="td-main" title="Ajuste de Matrícula">Ajuste de Matrícula</td>
                            <td className="td-sub" title="Felipe Melo">Felipe Melo</td>
                            <td className="td-date">09 Set</td>
                            <td className="td-status"><span className="badge badge-warning">Em análise</span></td>
                          </tr>
                          <tr>
                            <td className="td-date">2026.1089</td>
                            <td className="td-main" title="Trancamento Curso">Trancamento Curso</td>
                            <td className="td-sub" title="Larissa Dias">Larissa Dias</td>
                            <td className="td-date">08 Set</td>
                            <td className="td-status"><span className="badge badge-success">Deferido</span></td>
                          </tr>
                          <tr>
                            <td className="td-date">2026.1088</td>
                            <td className="td-main" title="Prorrogação Prazo">Prorrogação Prazo</td>
                            <td className="td-sub" title="Lucas Rocha">Lucas Rocha</td>
                            <td className="td-date">07 Set</td>
                            <td className="td-status"><span className="badge badge-danger">Indeferido</span></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Distribuição de Processos (Donut) */}
                  <div className="card">
                    <h3 className="card-title">Distribuição de Processos</h3>
                    <div className="donut-container" style={{ gap: "12px", padding: "4px 0" }}>
                      <div className="donut-visual" style={{ width: "120px", height: "120px" }}>
                        <svg width="120" height="120" viewBox="0 0 120 120">
                          <circle cx="60" cy="60" r="44" fill="none" stroke="#F0EAE1" strokeWidth="16" />
                          <circle
                            cx="60"
                            cy="60"
                            r="44"
                            fill="none"
                            stroke="var(--primary)"
                            strokeWidth="16"
                            strokeDasharray="124.4 276.5"
                            strokeDashoffset="69.1"
                            transform="rotate(-90 60 60)"
                          />
                          <circle
                            cx="60"
                            cy="60"
                            r="44"
                            fill="none"
                            stroke="var(--secondary)"
                            strokeWidth="16"
                            strokeDasharray="96.8 276.5"
                            strokeDashoffset="-55.3"
                            transform="rotate(-90 60 60)"
                          />
                          <circle
                            cx="60"
                            cy="60"
                            r="44"
                            fill="none"
                            stroke="var(--info)"
                            strokeWidth="16"
                            strokeDasharray="55.3 276.5"
                            strokeDashoffset="-152.1"
                            transform="rotate(-90 60 60)"
                          />
                        </svg>
                        <div className="donut-center-text">
                          <span className="donut-number" style={{ fontSize: "20px" }}>18</span>
                          <span className="donut-sub" style={{ fontSize: "8.5px" }}>Processos</span>
                        </div>
                      </div>
                      <div className="donut-legend" style={{ gap: "6px" }}>
                        <div className="legend-item" style={{ fontSize: "11.5px" }}>
                          <div><span className="legend-color" style={{ background: "var(--primary)" }} />Aprov. Disciplinas</div>
                          <strong>45% (8)</strong>
                        </div>
                        <div className="legend-item" style={{ fontSize: "11.5px" }}>
                          <div><span className="legend-color" style={{ background: "var(--secondary)" }} />Ajuste Matrícula</div>
                          <strong>35% (6)</strong>
                        </div>
                        <div className="legend-item" style={{ fontSize: "11.5px" }}>
                          <div><span className="legend-color" style={{ background: "var(--info)" }} />Quebra Pré-req.</div>
                          <strong>20% (4)</strong>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Coluna Widgets Colegiado */}
              <div className="widgets-column">
                <div className="card">
                  <h3 className="card-title">Próxima Reunião</h3>
                  <div style={{ background: "var(--neutral-bg)", padding: "14px", borderRadius: "8px", marginBottom: "12px", display: "flex", alignItems: "center", gap: "14px" }}>
                    <div style={{ background: "var(--surface)", padding: "6px 12px", borderRadius: "6px", textAlign: "center" }}>
                      <span style={{ fontSize: "16px", fontWeight: 700, color: "var(--primary)", display: "block" }}>24</span>
                      <span style={{ fontSize: "10px", fontWeight: 600, color: "var(--on-surface-variant)" }}>SET</span>
                    </div>
                    <div>
                      <strong style={{ fontSize: "13px", color: "var(--on-surface)", display: "block" }}>14:00 · Sala 12A</strong>
                      <span style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}>Ordinária Semestral</span>
                    </div>
                  </div>
                  <p style={{ fontSize: "11.5px", color: "var(--on-surface-variant)", lineHeight: 1.4 }}>
                    • Análise de pedidos de prorrogação de prazo.<br />
                    • Homologação de corpo docente e turmas.
                  </p>
                </div>

                <div className="action-buttons-card">
                  <button className="btn-action-primary" onClick={() => onNavegar("professores")}>
                    Corpo Docente (Professores)
                  </button>
                  <button className="btn-action-secondary">
                    Gerar Ata de Reunião
                  </button>
                </div>
              </div>
            </div>
          )}

          {profile.id === "ti_suporte" && (
            <div className="main-dashboard-grid">
              <div className="center-column">
                <div className="two-card-row">
                  {/* Chamados Recentes */}
                  <div className="card">
                    <h3 className="card-title">Chamados Recentes</h3>
                    <div className="table-wrap">
                      <table className="custom-table">
                        <thead>
                          <tr>
                            <th>Ticket</th>
                            <th>Solicitante</th>
                            <th>Categoria</th>
                            <th>Prioridade</th>
                            <th style={{ textAlign: "right" }}>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="td-date"><strong>#98201</strong></td>
                            <td className="td-main" title="Amanda K.">Amanda K.</td>
                            <td className="td-sub" title="Acesso Portal">Acesso Portal</td>
                            <td><span className="badge badge-danger">Alta</span></td>
                            <td className="td-status"><span className="badge badge-warning">Em atendimento</span></td>
                          </tr>
                          <tr>
                            <td className="td-date"><strong>#98199</strong></td>
                            <td className="td-main" title="Carlos E.">Carlos E.</td>
                            <td className="td-sub" title="Rede/Wi-Fi">Rede/Wi-Fi</td>
                            <td><span className="badge badge-warning">Média</span></td>
                            <td className="td-status"><span className="badge badge-warning">Em atendimento</span></td>
                          </tr>
                          <tr>
                            <td className="td-date"><strong>#98195</strong></td>
                            <td className="td-main" title="Profa. Lúcia">Profa. Lúcia</td>
                            <td className="td-sub" title="Moodle">Moodle</td>
                            <td><span className="badge badge-danger">Alta</span></td>
                            <td className="td-status"><span className="badge badge-success">Resolvido</span></td>
                          </tr>
                          <tr>
                            <td className="td-date"><strong>#98188</strong></td>
                            <td className="td-main" title="Prof. Marcos">Prof. Marcos</td>
                            <td className="td-sub" title="Equipamento">Equipamento</td>
                            <td><span className="badge" style={{ background: "var(--neutral-bg)" }}>Baixa</span></td>
                            <td className="td-status"><span className="badge badge-info">Aberto</span></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Status dos Serviços */}
                  <div className="card">
                    <h3 className="card-title">Status dos Serviços</h3>
                    <div className="notice-list">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--outline-light)" }}>
                        <span style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}><span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--secondary-text)" }} />Portal Acadêmico</span>
                        <span className="badge badge-success">Uptime: 99.9%</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--outline-light)" }}>
                        <span style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}><span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--secondary-text)" }} />Backend FastAPI</span>
                        <span className="badge badge-success">Online (Porta 8000)</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--outline-light)" }}>
                        <span style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}><span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--secondary-text)" }} />Banco de Dados</span>
                        <span className="badge badge-success">Uptime: 100%</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0" }}>
                        <span style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}><span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--secondary-text)" }} />Backup Automático</span>
                        <span className="badge badge-success">Uptime: 100%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Coluna Widgets TI */}
              <div className="widgets-column">
                <div className="card">
                  <h3 className="card-title">Saúde do Sistema</h3>
                  <div className="progress-list">
                    <div className="progress-item">
                      <div className="progress-item-head"><span>CPU Principal</span><strong>45%</strong></div>
                      <div className="progress-track"><div className="progress-fill verde" style={{ width: "45%" }} /></div>
                    </div>
                    <div className="progress-item">
                      <div className="progress-item-head"><span>Memória RAM</span><strong>78%</strong></div>
                      <div className="progress-track"><div className="progress-fill lilas" style={{ width: "78%" }} /></div>
                    </div>
                    <div className="progress-item">
                      <div className="progress-item-head"><span>Armazenamento</span><strong>62%</strong></div>
                      <div className="progress-track"><div className="progress-fill verde" style={{ width: "62%" }} /></div>
                    </div>
                  </div>
                </div>

                <div className="action-buttons-card">
                  <button className="btn-action-primary">Abrir Chamado</button>
                  <button className="btn-action-secondary">Logs de Auditoria</button>
                </div>
              </div>
            </div>
          )}

          {profile.id === "financeiro" && (
            <div className="main-dashboard-grid">
              <div className="center-column">
                <div className="two-card-row">
                  {/* Mensalidades Recentes */}
                  <div className="card">
                    <h3 className="card-title">Mensalidades Recentes</h3>
                    <div className="table-wrap">
                      <table className="custom-table">
                        <thead>
                          <tr>
                            <th>Aluno</th>
                            <th>Matrícula</th>
                            <th>Valor</th>
                            <th>Vencimento</th>
                            <th style={{ textAlign: "right" }}>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="td-main" title="Carlos Oliveira">Carlos Oliveira</td>
                            <td className="td-sub">20231002</td>
                            <td><strong>R$ 1.250,00</strong></td>
                            <td className="td-date">10 Set</td>
                            <td className="td-status"><span className="badge badge-success">Pago</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Juliana Mendes">Juliana Mendes</td>
                            <td className="td-sub">20241045</td>
                            <td><strong>R$ 1.250,00</strong></td>
                            <td className="td-date">10 Set</td>
                            <td className="td-status"><span className="badge badge-success">Pago</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Marcos Viana">Marcos Viana</td>
                            <td className="td-sub">20222019</td>
                            <td><strong>R$ 1.250,00</strong></td>
                            <td className="td-date">12 Set</td>
                            <td className="td-status"><span className="badge badge-warning">Pendente</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Fernanda Costa">Fernanda Costa</td>
                            <td className="td-sub">20231078</td>
                            <td><strong>R$ 1.250,00</strong></td>
                            <td className="td-date">12 Set</td>
                            <td className="td-status"><span className="badge badge-warning">Pendente</span></td>
                          </tr>
                          <tr>
                            <td className="td-main" title="Rafaela Souza">Rafaela Souza</td>
                            <td className="td-sub">20211004</td>
                            <td><strong>R$ 1.250,00</strong></td>
                            <td className="td-date">05 Set</td>
                            <td className="td-status"><span className="badge badge-danger">Atrasado</span></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Fluxo de Receita Mensal */}
                  <div className="card">
                    <h3 className="card-title">Fluxo de Receita Mensal</h3>
                    <div style={{ padding: "4px 0" }}>
                      <svg width="100%" height="120" viewBox="0 0 320 120" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#5B2333" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="#5B2333" stopOpacity="0.0" />
                          </linearGradient>
                        </defs>
                        <path d="M10,100 L60,85 L120,95 L180,70 L240,80 L300,45 L300,115 L10,115 Z" fill="url(#revGrad)" />
                        <polyline points="10,100 60,85 120,95 180,70 240,80 300,45" fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeLinecap="round" />
                        <circle cx="10" cy="100" r="3.5" fill="var(--primary)" />
                        <circle cx="60" cy="85" r="3.5" fill="var(--primary)" />
                        <circle cx="120" cy="95" r="3.5" fill="var(--primary)" />
                        <circle cx="180" cy="70" r="3.5" fill="var(--primary)" />
                        <circle cx="240" cy="80" r="3.5" fill="var(--primary)" />
                        <circle cx="300" cy="45" r="3.5" fill="var(--primary)" />
                      </svg>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10.5px", color: "var(--on-surface-variant)", marginTop: "6px" }}>
                        <div><span>Jan</span><br /><strong>350k</strong></div>
                        <div><span>Fev</span><br /><strong>410k</strong></div>
                        <div><span>Mar</span><br /><strong>380k</strong></div>
                        <div><span>Abr</span><br /><strong>520k</strong></div>
                        <div><span>Mai</span><br /><strong>490k</strong></div>
                        <div><span>Jun</span><br /><strong>610k</strong></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Coluna Widgets Financeiro */}
              <div className="widgets-column">
                <div className="card">
                  <h3 className="card-title">Resumo do Mês (Setembro)</h3>
                  <div className="notice-list">
                    <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}>
                      <span style={{ color: "var(--on-surface-variant)", fontSize: "13px" }}>Recebido</span>
                      <strong style={{ color: "var(--secondary-text)", fontSize: "14px" }}>R$ 412.500</strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}>
                      <span style={{ color: "var(--on-surface-variant)", fontSize: "13px" }}>A receber</span>
                      <strong style={{ color: "var(--tertiary-text)", fontSize: "14px" }}>R$ 180.200</strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}>
                      <span style={{ color: "var(--on-surface-variant)", fontSize: "13px" }}>Vencido</span>
                      <strong style={{ color: "var(--error-text)", fontSize: "14px" }}>R$ 56.400</strong>
                    </div>
                  </div>
                </div>

                <div className="action-buttons-card">
                  <button className="btn-action-primary">Emitir Boletos</button>
                  <button className="btn-action-secondary">Gerar Relatório</button>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* RODAPÉ ORGÂNICO (ONDAS ESTILIZADAS) */}
        <footer className="footer-waves" aria-hidden="true">
          <svg viewBox="0 0 1180 60" preserveAspectRatio="none" fill="none">
            <path d="M0,35 C150,10 300,55 450,30 C600,5 750,50 900,25 C1050,0 1150,30 1180,35 L1180,60 L0,60 Z" fill="#5B2333" opacity="0.08" />
            <path d="M0,45 C200,25 400,60 600,40 C800,20 1000,55 1180,42 L1180,60 L0,60 Z" fill="#5B2333" opacity="0.15" />
          </svg>
        </footer>
      </main>
    </div>
  );
};
