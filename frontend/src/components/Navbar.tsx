import React from "react";

interface Props {
  paginaAtual: string;
  onNavegar: (pagina: "home" | "professores" | "login") => void;
  statusTexto: string;
  isOnline: boolean;
}

const Navbar: React.FC<Props> = ({ paginaAtual, onNavegar, statusTexto, isOnline }) => {
  return (
    <header className="navbar-institucional" role="banner">
      <div className="container">
        <nav className="navbar-conteudo" aria-label="Navegação principal">
          {/* Logo */}
          <button
            className="logo"
            onClick={() => onNavegar("home")}
            style={{ background: "none", border: "none", cursor: "pointer" }}
            aria-label="Ir para a tela inicial do SGA-Edu"
          >
            <div className="logo-icone" aria-hidden="true">🎓</div>
            <div className="logo-textos">
              <span className="logo-nome">SGA-Edu</span>
              <span className="logo-sub">Sistema de Gestão Acadêmica</span>
            </div>
          </button>

          {/* Status */}
          <div className="status-sistema" role="status" aria-live="polite" aria-label={`Status do sistema: ${statusTexto}`}>
            <div className={`status-bolinha${isOnline ? "" : " offline"}`} aria-hidden="true" />
            <span className="status-texto">{statusTexto}</span>
          </div>

          {/* Menu */}
          <ul className="nav-lista" role="list">
            <li>
              <button
                className={`nav-link${paginaAtual === "home" ? " ativo" : ""}`}
                onClick={() => onNavegar("home")}
                aria-current={paginaAtual === "home" ? "page" : undefined}
              >
                🏠 Início
              </button>
            </li>
            <li>
              <button
                className={`nav-link${paginaAtual === "professores" ? " ativo" : ""}`}
                onClick={() => onNavegar("professores")}
                aria-current={paginaAtual === "professores" ? "page" : undefined}
              >
                👨‍🏫 Professores
              </button>
            </li>
            <li>
              <button
                className="nav-link-login"
                onClick={() => onNavegar("login")}
                aria-label="Acessar tela de login"
              >
                🔑 Login
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
