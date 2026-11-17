import React from "react";
import type { PerfilId } from "./modulo_30_tela_inicial/perfisDados";

export interface UsuarioInfo {
  nome: string;
  perfil: PerfilId;
  matricula: string;
}

interface Props {
  paginaAtual?: string;
  onNavegar: (pagina: "home" | "professores" | "login") => void;
  statusTexto?: string;
  isOnline?: boolean;
  usuarioLogado: UsuarioInfo | null;
  onLogout?: () => void;
}

/**
 * Navbar — Cabeçalho Institucional alinhado rigorosamente ao protótipo (DESIGN.md e prototipo v3)
 * No canto superior esquerdo exibe o logotipo com o ícone SVG oficial do SGA-Edu.
 */
const Navbar: React.FC<Props> = ({
  onNavegar,
  usuarioLogado,
  onLogout,
}) => {
  return (
    <header
      className="app-header"
      style={{
        background: "var(--neutral-bg)",
        borderBottom: "1px solid var(--outline)",
        padding: "0 32px",
        height: "var(--header-h)",
      }}
      role="banner"
    >
      {/* 3. LOGO NO CANTO SUPERIOR ESQUERDO COM O ÍCONE PRESENTE NAS DEMAIS TELAS */}
      <button
        onClick={() => onNavegar("home")}
        style={{
          background: "none",
          border: "none",
          padding: 0,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          textAlign: "left",
        }}
        aria-label="Ir para a página inicial do SGA-Edu"
      >
        <div className="sidebar-brand" style={{ marginBottom: 0 }}>
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
      </button>

      {/* AÇÕES DO CABEÇALHO (BUSCA + NOTIFICAÇÕES + LOGIN) */}
      <div className="header-actions">
        {/* BARRA DE PESQUISA (POSICIONADA À DIREITA, PRÓXIMA ÀS NOTIFICAÇÕES) */}
        <div className="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Buscar disciplinas, avisos, processos, notas..."
            aria-label="Campo de busca institucional"
          />
        </div>

        <button className="notif-btn" title="Notificações" aria-label="Notificações">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </button>

        {usuarioLogado ? (
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                fontSize: "12.5px",
                fontWeight: 600,
                color: "var(--primary)",
                background: "var(--primary-container)",
                padding: "6px 12px",
                borderRadius: "var(--radius-pill)",
              }}
            >
              👤 {usuarioLogado.nome}
            </span>
            <button
              onClick={onLogout}
              className="btn btn-sm btn-perigo"
              style={{ borderRadius: "var(--radius-pill)", padding: "6px 14px" }}
              title="Encerrar sessão"
            >
              Sair
            </button>
          </div>
        ) : (
          <button
            onClick={() => onNavegar("login")}
            className="btn btn-primario btn-sm"
            style={{
              borderRadius: "var(--radius-pill)",
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: 600,
              boxShadow: "var(--shadow-sm)",
            }}
          >
            🔑 Entrar (Login)
          </button>
        )}
      </div>
    </header>
  );
};

export default Navbar;
