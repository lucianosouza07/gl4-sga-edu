import React, { useState, useEffect } from "react";
import Navbar from "./Navbar";
import Rodape from "./Rodape";
import TelaInicial from "./modulo_30_tela_inicial/TelaInicial";
import { DashboardPerfil } from "./modulo_30_tela_inicial/DashboardPerfil";
import CadastrarProfessor from "./modulo_34_cadastrar_professor/CadastrarProfessor";
import Login from "./Login";
import { PERFIS, PerfilId } from "./modulo_30_tela_inicial/perfisDados";
import { checarStatusBackend } from "./api";

export type Pagina = "home" | "professores" | "login";

export interface UsuarioLogado {
  nome: string;
  perfil: PerfilId;
  matricula: string;
}

/**
 * App — Orquestrador do Portal SGA-Edu
 * 1. Inicializa em estado NÃO autenticado (visitante público).
 * 2. Exibe tela inicial pública alinhada rigorosamente ao protótipo.
 * 3. O acesso se dá exclusivamente por matrícula e senha (registro define o perfil).
 * 4. Após o login, exibe o painel do perfil correspondente.
 */
const App: React.FC = () => {
  const [pagina, setPagina] = useState<Pagina>("home");
  const [usuarioLogado, setUsuarioLogado] = useState<UsuarioLogado | null>(null);
  const [isOnline, setIsOnline] = useState(false);
  const [statusTexto, setStatusTexto] = useState("Verificando...");

  // Verificação de conectividade com o backend FastAPI ao carregar a página
  useEffect(() => {
    checarStatusBackend().then(({ online, rotulo }) => {
      setIsOnline(online);
      setStatusTexto(rotulo);
    });
  }, []);

  function handleNavegar(destino: Pagina) {
    setPagina(destino);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleIrParaLogin() {
    setPagina("login");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleEfetuarLogin(perfil: PerfilId, usuario: string) {
    const configPerfil = PERFIS[perfil] || PERFIS.discente;
    setUsuarioLogado({
      nome: usuario || configPerfil.name,
      perfil: perfil,
      matricula: configPerfil.role,
    });
    setPagina("home");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleLogout() {
    setUsuarioLogado(null);
    setPagina("home");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* NAVBAR INSTITUCIONAL: exibida quando na Home pública ou no Cadastro de Professores */}
      {(!usuarioLogado || pagina === "professores") && pagina !== "login" && (
        <Navbar
          paginaAtual={pagina}
          onNavegar={handleNavegar}
          statusTexto={statusTexto}
          isOnline={isOnline}
          usuarioLogado={usuarioLogado}
          onLogout={handleLogout}
        />
      )}

      {/* ROTEAMENTO DE CONTEÚDO */}

      {/* 1. Página HOME */}
      {pagina === "home" && (
        <>
          {usuarioLogado ? (
            // Usuário autenticado: exibe o dashboard completo com sidebar e indicadores do perfil
            <DashboardPerfil
              perfilId={usuarioLogado.perfil}
              onNavegar={handleNavegar}
              onLogout={handleLogout}
            />
          ) : (
            // Usuário não autenticado: exibe a Home pública alinhada ao protótipo
            <TelaInicial
              onNavegar={handleNavegar}
              onIrParaLogin={handleIrParaLogin}
              isOnline={isOnline}
            />
          )}
        </>
      )}

      {/* 2. Página de Cadastro e Gestão de Professores (GL4-34 / SGA-16) */}
      {pagina === "professores" && (
        <CadastrarProfessor />
      )}

      {/* 3. Página de Login & Recuperação de Senha (SGA-13 / SGA-14) */}
      {pagina === "login" && (
        <Login
          onLogin={handleEfetuarLogin}
          onVoltar={() => handleNavegar("home")}
        />
      )}

      {/* RODAPÉ INSTITUCIONAL: exibido na Home pública e na página de Professores */}
      {(!usuarioLogado || pagina === "professores") && pagina !== "login" && (
        <Rodape />
      )}
    </div>
  );
};

export default App;
