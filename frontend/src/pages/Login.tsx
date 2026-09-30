import React, { useState } from "react";

interface Props {
  onLogin: () => void;
}

/**
 * Página de Login — preservada da implementação original
 */
const Login: React.FC<Props> = ({ onLogin }) => {
  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);

    if (!usuario.trim() || !senha.trim()) {
      setErro("Preencha usuário e senha.");
      return;
    }

    setCarregando(true);
    // Simulação de autenticação (backend de auth não implementado ainda)
    await new Promise((r) => setTimeout(r, 800));

    // Credenciais de demonstração
    if (usuario === "admin" && senha === "admin") {
      onLogin();
    } else {
      setErro("Usuário ou senha inválidos. (demo: admin / admin)");
    }
    setCarregando(false);
  }

  return (
    <main className="pagina-login" aria-label="Tela de login do SGA-Edu">
      <div className="login-card" role="form" aria-labelledby="login-titulo">
        <div className="login-logo" aria-hidden="true">
          <div style={{ fontSize: "2.5rem", marginBottom: ".5rem" }}>🎓</div>
        </div>
        <h1 id="login-titulo" className="login-titulo">SGA-Edu</h1>
        <p className="login-sub">Sistema de Gestão Acadêmica</p>

        {erro && (
          <div className="alerta alerta-erro" role="alert" aria-live="assertive" style={{ marginTop: "1rem" }}>
            ⚠️ {erro}
          </div>
        )}

        <form className="login-form" onSubmit={handleSubmit} noValidate style={{ marginTop: "1.5rem" }}>
          <div>
            <label htmlFor="usuario">Usuário</label>
            <input
              id="usuario"
              type="text"
              autoComplete="username"
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              aria-required="true"
              disabled={carregando}
            />
          </div>
          <div>
            <label htmlFor="senha">Senha</label>
            <input
              id="senha"
              type="password"
              autoComplete="current-password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              aria-required="true"
              disabled={carregando}
            />
          </div>
          <button type="submit" className="login-btn" disabled={carregando}>
            {carregando ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </main>
  );
};

export default Login;
