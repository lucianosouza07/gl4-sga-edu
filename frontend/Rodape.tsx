import React from "react";

const Rodape: React.FC = () => {
  const ano = new Date().getFullYear();
  return (
    <footer
      style={{
        background: "var(--primary)",
        color: "rgba(255,255,255,0.8)",
        padding: "20px 24px",
        marginTop: "auto",
        fontSize: "12.5px",
        borderTop: "1px solid rgba(255,255,255,0.1)",
      }}
      role="contentinfo"
    >
      <div
        style={{
          maxWidth: "1240px",
          margin: "0 auto",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <strong>SGA-Edu</strong> · Sistema Integrado de Gestão Acadêmica do Ensino Superior
          <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.6)", marginTop: "2px" }}>
            Universidade do Estado da Bahia — Campus II (Alagoinhas) · Semestre Letivo 2026.2
          </div>
        </div>

        <div style={{ textAlign: "right", fontSize: "11.5px" }}>
          <span>© {ano} SGA-Edu · Sprint 01 (SGA-10 a SGA-17)</span>
          <div style={{ color: "var(--tertiary)", fontWeight: 500, marginTop: "2px" }}>
            GL4-30 (Tela Inicial) & GL4-34 (Professores)
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Rodape;
