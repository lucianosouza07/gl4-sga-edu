import React, { useEffect, useState, useCallback } from "react";
import TabelaProfessores from "../components/TabelaProfessores";
import FormularioProfessor from "../components/FormularioProfessor";
import type { Professor, ProfessorEntrada } from "../types/professor";
import {
  listarProfessores,
  cadastrarProfessor,
  atualizarProfessor,
  excluirProfessor,
} from "../services/api";

type ModoFormulario = "criar" | "editar" | null;

/**
 * Página de Cadastro e Gestão de Professores — GL4-34
 */
const CadastrarProfessor: React.FC = () => {
  const [professores, setProfessores] = useState<Professor[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [modo, setModo] = useState<ModoFormulario>(null);
  const [professorEditando, setProfessorEditando] = useState<Professor | null>(null);
  const [mensagem, setMensagem] = useState<{ texto: string; tipo: "sucesso" | "erro" } | null>(null);
  const [erroPersistente, setErroPersistente] = useState<string | null>(null);

  const exibirMensagem = (texto: string, tipo: "sucesso" | "erro") => {
    setMensagem({ texto, tipo });
    setTimeout(() => setMensagem(null), 4000);
  };

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const lista = await listarProfessores();
      setProfessores(lista);
    } catch {
      exibirMensagem("Não foi possível conectar ao servidor.", "erro");
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  function abrirFormNovo() {
    setProfessorEditando(null);
    setErroPersistente(null);
    setModo("criar");
  }

  function abrirFormEditar(prof: Professor) {
    setProfessorEditando(prof);
    setErroPersistente(null);
    setModo("editar");
  }

  function fecharForm() {
    setModo(null);
    setProfessorEditando(null);
    setErroPersistente(null);
  }

  async function handleSalvar(dados: ProfessorEntrada) {
    setSalvando(true);
    setErroPersistente(null);
    try {
      if (modo === "editar" && professorEditando) {
        await atualizarProfessor(professorEditando.id, dados);
        exibirMensagem("Professor atualizado com sucesso!", "sucesso");
      } else {
        await cadastrarProfessor(dados);
        exibirMensagem("Professor cadastrado com sucesso!", "sucesso");
      }
      fecharForm();
      await carregar();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao salvar professor.";
      setErroPersistente(msg);
    } finally {
      setSalvando(false);
    }
  }

  async function handleExcluir(prof: Professor) {
    if (!window.confirm(`Deseja excluir o professor "${prof.nome}"? Esta ação não pode ser desfeita.`)) {
      return;
    }
    try {
      await excluirProfessor(prof.id);
      exibirMensagem(`Professor "${prof.nome}" excluído com sucesso.`, "sucesso");
      await carregar();
    } catch {
      exibirMensagem("Erro ao excluir professor.", "erro");
    }
  }

  return (
    <main id="conteudo-principal" tabIndex={-1} className="pagina-professores">
      <div className="container">
        {/* Cabeçalho */}
        <div className="pagina-cabecalho">
          <h1>👨‍🏫 Professores</h1>
          <button className="btn btn-primario" onClick={abrirFormNovo} aria-label="Cadastrar novo professor">
            ➕ Novo Professor
          </button>
        </div>

        {/* Mensagem de feedback */}
        {mensagem && (
          <div
            className={`alerta alerta-${mensagem.tipo === "sucesso" ? "sucesso" : "erro"}`}
            role="alert"
            aria-live="assertive"
          >
            {mensagem.tipo === "sucesso" ? "✅" : "⚠️"} {mensagem.texto}
          </div>
        )}

        {/* Tabela */}
        <TabelaProfessores
          professores={professores}
          onEditar={abrirFormEditar}
          onExcluir={handleExcluir}
          carregando={carregando}
        />

        {/* Formulário modal */}
        {modo && (
          <FormularioProfessor
            professor={professorEditando}
            onSalvar={handleSalvar}
            onCancelar={fecharForm}
            carregando={salvando}
            erro={erroPersistente}
          />
        )}
      </div>
    </main>
  );
};

export default CadastrarProfessor;
