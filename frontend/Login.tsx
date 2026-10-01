import React, { useState } from "react";
import { buscarUsuarioPorLogin, PerfilId, REGISTROS_USUARIOS } from "./modulo_30_tela_inicial/perfisDados";

interface Props {
  onLogin: (perfil: PerfilId, usuario: string) => void;
  onVoltar: () => void;
}

/**
 * Login & Recuperação de Senha (SGA-13 e SGA-14)
 * O acesso se dá exclusivamente por matrícula/usuário e senha.
 * O tipo de perfil do usuário é determinado automaticamente pelo seu registro no sistema.
 */
const Login: React.FC<Props> = ({ onLogin, onVoltar }) => {
  const [abaAtiva, setAbaAtiva] = useState<"login" | "recuperar">("login");
  const [identificador, setIdentificador] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  // Estados para Recuperação de Senha (SGA-14)
  const [emailRecuperacao, setEmailRecuperacao] = useState("");

  // Detecção automática do perfil com base no registro
  const registroEncontrado = identificador.trim()
    ? buscarUsuarioPorLogin(identificador.trim())
    : null;

  function preencherDemo(matricula: string) {
    setIdentificador(matricula);
    setSenha("uneb@2026");
    setErro(null);
  }

  async function handleSubmitLogin(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);

    const idLimpo = identificador.trim();
    const senhaLimpa = senha.trim();

    if (!idLimpo || !senhaLimpa) {
      setErro("Informe sua matrícula (ou usuário) e senha de acesso.");
      return;
    }

    setCarregando(true);
    await new Promise((r) => setTimeout(r, 600));

    // Determina o perfil a partir do registro cadastral
    const registro = buscarUsuarioPorLogin(idLimpo);
    const perfilFinal: PerfilId = registro ? registro.perfil : "discente";
    const nomeFinal = registro ? registro.nome : idLimpo;

    setCarregando(false);
    onLogin(perfilFinal, nomeFinal);
  }

  async function handleSubmitRecuperacao(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setSucesso(null);

    if (!emailRecuperacao.trim() || !emailRecuperacao.includes("@")) {
      setErro("Informe um e-mail institucional ou CPF válido para envio das instruções.");
      return;
    }

    setCarregando(true);
    await new Promise((r) => setTimeout(r, 700));
    setCarregando(false);
    setSucesso(
      `Um token de recuperação temporário (válido por 30 minutos) foi enviado para ${emailRecuperacao}. Siga as instruções para redefinir sua senha.`
    );
  }

  return (
    <main className="pagina-login" aria-label="Tela de autenticação do SGA-Edu">
      <div className="login-card" role="form" aria-labelledby="login-titulo">
        {/* LOGO INSTITUCIONAL IDÊNTICO ÀS DEMAIS TELAS */}
        <div className="login-logo" aria-hidden="true" style={{ display: "flex", justifyContent: "center" }}>
          <div className="brand-icon" style={{ width: "48px", height: "48px", borderRadius: "12px" }}>
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
              <path d="M6 12v5c3 3 9 3 12 0v-5" />
            </svg>
          </div>
        </div>

        <h1 id="login-titulo" className="login-titulo">
          SGA-Edu
        </h1>
        <p className="login-sub">Portal Acadêmico · UNEB Campus II</p>

        {/* Abas: Login x Recuperar Senha */}
        <div className="login-tabs">
          <button
            className={`login-tab ${abaAtiva === "login" ? "ativo" : ""}`}
            onClick={() => {
              setAbaAtiva("login");
              setErro(null);
              setSucesso(null);
            }}
          >
            🔑 Acessar o Portal
          </button>
          <button
            className={`login-tab ${abaAtiva === "recuperar" ? "ativo" : ""}`}
            onClick={() => {
              setAbaAtiva("recuperar");
              setErro(null);
              setSucesso(null);
            }}
          >
            🔒 Esqueci Minha Senha
          </button>
        </div>

        {/* Mensagens de feedback */}
        {erro && (
          <div className="alerta alerta-erro" role="alert" aria-live="assertive">
            ⚠️ {erro}
          </div>
        )}
        {sucesso && (
          <div className="alerta alerta-sucesso" role="alert" aria-live="polite">
            ✅ {sucesso}
          </div>
        )}

        {/* Formulário de Login (SGA-13) */}
        {abaAtiva === "login" && (
          <form className="login-form" onSubmit={handleSubmitLogin} noValidate>
            <div>
              <label htmlFor="usuario">Matrícula ou Usuário Institucional</label>
              <input
                id="usuario"
                type="text"
                autoComplete="username"
                value={identificador}
                onChange={(e) => setIdentificador(e.target.value)}
                placeholder="Ex: 2037538292 ou leticia.silva"
                aria-required="true"
                disabled={carregando}
              />
              {/* Notificação sutil do registro reconhecido no sistema */}
              {registroEncontrado && (
                <div style={{ marginTop: "6px", fontSize: "11.5px", color: "var(--secondary-text)", display: "flex", alignItems: "center", gap: "5px" }}>
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--secondary-text)" }}></span>
                  Registro localizado: <strong>{registroEncontrado.nome}</strong> ({registroEncontrado.descricaoVínculo})
                </div>
              )}
            </div>

            <div>
              <label htmlFor="senha">Senha de Acesso</label>
              <input
                id="senha"
                type="password"
                autoComplete="current-password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                placeholder="••••••••"
                aria-required="true"
                disabled={carregando}
              />
            </div>

            <button type="submit" className="login-btn" disabled={carregando}>
              {carregando ? "Autenticando..." : "Entrar no Sistema"}
            </button>

            {/* Demonstração de Registros para Avaliação Rápida */}
            <div className="demo-pills">
              <div className="demo-pills-label">Preenchimento Rápido por Matrícula Cadastrada:</div>
              <div className="demo-pills-grid">
                {REGISTROS_USUARIOS.map((reg) => (
                  <button
                    key={reg.matricula}
                    type="button"
                    className="demo-pill"
                    onClick={() => preencherDemo(reg.matricula)}
                    title={`Matrícula: ${reg.matricula} — ${reg.descricaoVínculo}`}
                  >
                    {reg.nome.split(" ")[0]} ({reg.matricula})
                  </button>
                ))}
              </div>
            </div>
          </form>
        )}

        {/* Formulário de Recuperação de Senha (SGA-14) */}
        {abaAtiva === "recuperar" && (
          <form className="login-form" onSubmit={handleSubmitRecuperacao} noValidate>
            <p style={{ fontSize: "13px", color: "var(--on-surface-variant)", lineHeight: 1.5 }}>
              Informe o e-mail cadastrado ou seu CPF para receber o token de redefinição de senha:
            </p>

            <div>
              <label htmlFor="email-recuperacao">E-mail Institucional ou CPF</label>
              <input
                id="email-recuperacao"
                type="text"
                value={emailRecuperacao}
                onChange={(e) => setEmailRecuperacao(e.target.value)}
                placeholder="usuario@uneb.br ou 000.000.000-00"
                aria-required="true"
                disabled={carregando}
              />
            </div>

            <button type="submit" className="login-btn" disabled={carregando}>
              {carregando ? "Enviando..." : "Solicitar Redefinição"}
            </button>

            <button
              type="button"
              className="btn btn-secundario"
              style={{ width: "100%", marginTop: "8px" }}
              onClick={() => setAbaAtiva("login")}
            >
              ← Voltar ao Login
            </button>
          </form>
        )}

        {/* Botão de retorno à Tela Inicial pública */}
        <div style={{ textAlign: "center", marginTop: "24px" }}>
          <button
            type="button"
            onClick={onVoltar}
            style={{
              background: "none",
              border: "none",
              color: "var(--primary)",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              textDecoration: "underline",
            }}
          >
            ← Voltar para a Tela Inicial (Pública)
          </button>
        </div>
      </div>
    </main>
  );
};

export default Login;
