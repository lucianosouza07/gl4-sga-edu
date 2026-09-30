import React, { useEffect, useState } from "react";
import type { ResumoMetricas } from "../types/professor";

interface Props {
  metricas: ResumoMetricas;
  isOnline: boolean;
}

/**
 * Hero Dashboard — GL4-30
 * Exibe saudação contextual, data atual e contadores de resumo do sistema.
 */
const HeroDashboard: React.FC<Props> = ({ metricas, isOnline }) => {
  const [dataAtual, setDataAtual] = useState("");
  const [saudacao, setSaudacao] = useState("Bem-vindo(a)");

  useEffect(() => {
    const agora = new Date();

    // Saudação contextual por hora
    const hora = agora.getHours();
    if (hora < 12) setSaudacao("Bom dia! ☀️");
    else if (hora < 18) setSaudacao("Boa tarde! 🌤️");
    else setSaudacao("Boa noite! 🌙");

    // Data formatada em pt-BR
    setDataAtual(
      agora.toLocaleDateString("pt-BR", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    );
  }, []);

  return (
    <section className="hero-dashboard" aria-label="Painel de resumo do sistema">
      <div className="container">
        <div className="hero-conteudo">
          <div>
            <p className="hero-saudacao" aria-label={`Saudação: ${saudacao}`}>{saudacao}</p>
            <h1 className="hero-titulo">SGA-Edu<br />Sistema de Gestão Acadêmica</h1>
            <p className="hero-data" aria-label={`Data atual: ${dataAtual}`}>📅 {dataAtual}</p>
          </div>

          {/* Contadores / Métricas */}
          <div className="hero-metricas" role="list" aria-label="Indicadores do sistema">
            <div className="metrica-card" role="listitem">
              <div className="metrica-numero" aria-label={`${metricas.totalProfessores} professores cadastrados`}>
                {metricas.totalProfessores}
              </div>
              <div className="metrica-rotulo">Professores</div>
            </div>
            <div className="metrica-card" role="listitem">
              <div className="metrica-numero" aria-label={`${metricas.modulosAtivos} módulos ativos`}>
                {metricas.modulosAtivos}
              </div>
              <div className="metrica-rotulo">Módulos Ativos</div>
            </div>
            <div className="metrica-card" role="listitem">
              <div className="metrica-numero"
                aria-label={`Status do sistema: ${isOnline ? "online" : "offline"}`}
              >
                {isOnline ? "🟢" : "🔴"}
              </div>
              <div className="metrica-rotulo">Sistema</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroDashboard;
