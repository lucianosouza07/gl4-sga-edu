import React, { useEffect, useState, useCallback } from "react";
import HeroDashboard from "../components/HeroDashboard";
import CardModulo from "../components/CardModulo";
import type { ResumoMetricas } from "../types/professor";
import { listarProfessores } from "../services/api";

interface Props {
  onNavegar: (pagina: "home" | "professores" | "login") => void;
  isOnline: boolean;
}

/**
 * Tela Inicial — GL4-30
 * Exibe hero dashboard, card de Professores e cards dos módulos futuros.
 */
const TelaInicial: React.FC<Props> = ({ onNavegar, isOnline }) => {
  const [metricas, setMetricas] = useState<ResumoMetricas>({
    totalProfessores: 0,
    modulosAtivos: 1,
  });

  const carregarMetricas = useCallback(async () => {
    try {
      const professores = await listarProfessores();
      setMetricas((prev) => ({ ...prev, totalProfessores: professores.length }));
    } catch {
      // Backend offline — mantém 0
    }
  }, []);

  useEffect(() => {
    carregarMetricas();
  }, [carregarMetricas]);

  const modulos = [
    {
      id: "alunos",
      icone: "🎓",
      nome: "Alunos",
      descricao: "Cadastro, matrícula e acompanhamento de alunos.",
      status: "em-breve" as const,
    },
    {
      id: "disciplinas",
      icone: "📚",
      nome: "Disciplinas",
      descricao: "Gerenciamento de disciplinas e grades curriculares.",
      status: "em-breve" as const,
    },
    {
      id: "turmas",
      icone: "🏫",
      nome: "Turmas",
      descricao: "Organização de turmas e alocação de professores.",
      status: "em-breve" as const,
    },
    {
      id: "notas",
      icone: "📊",
      nome: "Notas & Frequência",
      descricao: "Lançamento de notas e controle de frequência.",
      status: "em-breve" as const,
    },
    {
      id: "relatorios",
      icone: "📄",
      nome: "Relatórios",
      descricao: "Geração de relatórios acadêmicos e administrativos.",
      status: "em-breve" as const,
    },
  ];

  return (
    <main id="conteudo-principal" tabIndex={-1}>
      {/* Skip navigation */}
      <a href="#conteudo-principal" className="sr-only">
        Ir para o conteúdo principal
      </a>

      {/* Hero Dashboard */}
      <HeroDashboard
        metricas={metricas}
        isOnline={isOnline}
      />

      {/* Módulos */}
      <section className="secao-modulos" aria-label="Módulos do sistema">
        <div className="container">
          <h2 className="secao-titulo">📦 Módulos do Sistema</h2>
          <div className="grade-modulos" role="list">

            {/* Card Professores — GL4-34 integrado */}
            <div role="listitem">
              <CardModulo
                icone="👨‍🏫"
                nome="Professores"
                descricao="Cadastro, consulta, edição e remoção de professores do sistema."
                status="ativo"
                contador={`${metricas.totalProfessores} professor${metricas.totalProfessores !== 1 ? "es" : ""} cadastrado${metricas.totalProfessores !== 1 ? "s" : ""}`}
                acoes={
                  <>
                    <button
                      className="btn btn-primario btn-sm"
                      onClick={() => onNavegar("professores")}
                      aria-label="Cadastrar novo professor"
                    >
                      ➕ Novo Professor
                    </button>
                    <button
                      className="btn btn-secundario btn-sm"
                      onClick={() => onNavegar("professores")}
                      aria-label="Consultar lista de professores"
                    >
                      🔍 Consultar
                    </button>
                  </>
                }
              />
            </div>

            {/* Módulos futuros */}
            {modulos.map((mod) => (
              <div key={mod.id} role="listitem">
                <CardModulo
                  icone={mod.icone}
                  nome={mod.nome}
                  descricao={mod.descricao}
                  status={mod.status}
                />
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
};

export default TelaInicial;
