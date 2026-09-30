import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import Rodape from "./components/Rodape";
import TelaInicial from "./pages/TelaInicial";
import CadastrarProfessor from "./pages/CadastrarProfessor";
import Login from "./pages/Login";
import { checarStatusBackend } from "./services/api";

type Pagina = "home" | "professores" | "login";

/**
 * App — Roteamento SPA por estado (sem react-router)
 * GL4-30: Tela Inicial
 * GL4-34: Cadastro de Professores
 */
const App: React.FC = () => {
  const [pagina, setPagina] = useState<Pagina>("home");
  const [isOnline, setIsOnline] = useState(false);
  const [statusTexto, setStatusTexto] = useState("Verificando…");

  // Verificação de status do backend ao montar
  useEffect(() => {
    checarStatusBackend().then(({ online, rotulo }) => {
      setIsOnline(online);
      setStatusTexto(rotulo);
    });
  }, []);

  function handleNavegar(destino: Pagina) {
    setPagina(destino);
    // Rolagem para o topo ao navegar
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleLogin() {
    setPagina("home");
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* Navbar exibida em todas as telas, exceto login */}
      {pagina !== "login" && (
        <Navbar
          paginaAtual={pagina}
          onNavegar={handleNavegar}
          statusTexto={statusTexto}
          isOnline={isOnline}
        />
      )}

      {/* Roteamento por estado */}
      {pagina === "home" && (
        <TelaInicial onNavegar={handleNavegar} isOnline={isOnline} />
      )}
      {pagina === "professores" && <CadastrarProfessor />}
      {pagina === "login" && <Login onLogin={handleLogin} />}

      {/* Rodapé exibido em todas as telas, exceto login */}
      {pagina !== "login" && <Rodape />}
    </div>
  );
};

export default App;
