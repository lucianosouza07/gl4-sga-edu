import React, { useEffect, useState } from "react";
import type { ResumoMetricas } from "../professor";

interface Props {
  metricas: ResumoMetricas;
  isOnline: boolean;
  onIrParaLogin: () => void;
}

/**
 * HeroDashboard — SGA-Edu (Campus II)
 * Tela Inicial Pública (visitante não autenticado)
 * Alinhado a SGA-12, DESIGN.md e SPEC.md.
 */
const HeroDashboard: React.FC<Props> = ({ metricas, isOnline, onIrParaLogin }) => {
  const [dataAtual, setDataAtual] = useState("");

  useEffect(() => {
    const agora = new Date();
    setDataAtual(
      agora.toLocaleDateString("pt-BR", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    );
  }, []);

  function handleRolarParaPerfis() {
    const el = document.getElementById("secao-perfis");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  }

  return (
    <section className="portal-hero" aria-label="Painel de boas-vindas do sistema">
      <div className="portal-hero-top">
        <span className="portal-tag-semestre">
          🏛️ UNEB Campus II · Semestre Ativo <strong>2026.2</strong>
        </span>
        <span style={{ fontSize: "12.5px", opacity: 0.9 }}>
          📅 {dataAtual}
        </span>
      </div>

      <div style={{ maxWidth: "800px" }}>
        <p style={{ fontSize: "13.5px", color: "var(--tertiary)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "6px" }}>
          Portal Integrado de Gestão Acadêmica
        </p>
        <h1 className="portal-hero-title">
          Bem-vindo(a) ao SGA-Edu
        </h1>
        <p className="portal-hero-sub">
          Ambiente digital unificado da Universidade do Estado da Bahia (Campus II - Alagoinhas).
          Centraliza a gestão acadêmica, diário de classe, processos de colegiado, suporte de TI e administração financeira.
        </p>
      </div>

      {/* Alerta de Acesso não autenticado & Botão de Login */}
      <div
        style={{
          marginTop: "24px",
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "14px",
        }}
      >
        <button
          className="btn"
          onClick={onIrParaLogin}
          style={{
            background: "var(--tertiary)",
            color: "var(--on-surface)",
            padding: "12px 24px",
            fontSize: "14px",
            fontWeight: 700,
            borderRadius: "var(--radius-sm)",
            boxShadow: "0 4px 14px rgba(0,0,0,0.2)",
          }}
        >
          🔑 Entrar no Portal (Matrícula e Senha)
        </button>

        <button
          className="btn"
          onClick={handleRolarParaPerfis}
          style={{
            background: "rgba(255,255,255,0.14)",
            color: "#fff",
            border: "1px solid rgba(255,255,255,0.3)",
            padding: "12px 20px",
            fontSize: "14px",
            fontWeight: 600,
            borderRadius: "var(--radius-sm)",
          }}
        >
          👥 Conhecer Opções de Acesso por Perfil ↓
        </button>
      </div>

      {/* Indicadores rápidos do sistema */}
      <div className="portal-metricas-resumo" role="list" aria-label="Indicadores do sistema">
        <div className="portal-metrica-item" role="listitem">
          <div className="portal-metrica-num">2026.2</div>
          <div className="portal-metrica-label">Período Letivo Vigente</div>
        </div>
        <div className="portal-metrica-item" role="listitem">
          <div className="portal-metrica-num">5</div>
          <div className="portal-metrica-label">Perfis de Usuário (RBAC)</div>
        </div>
        <div className="portal-metrica-item" role="listitem">
          <div className="portal-metrica-num">{metricas.totalProfessores}</div>
          <div className="portal-metrica-label">Professores Cadastrados</div>
        </div>
        <div className="portal-metrica-item" role="listitem">
          <div className="portal-metrica-num" style={{ color: isOnline ? "#A8D5A0" : "#E8879C" }}>
            {isOnline ? "Online" : "Operacional"}
          </div>
          <div className="portal-metrica-label">Status da API (FastAPI)</div>
        </div>
      </div>
    </section>
  );
};

export default HeroDashboard;
