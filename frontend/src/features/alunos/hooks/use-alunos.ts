import { useState, useEffect, useCallback } from "react";
import { alunoApi } from "../services/aluno.api";
import type { Aluno } from "../data/aluno.types";
import { toast } from "sonner";
import { extrairErrosAPI } from "@/api/handle-api-error";

export const TAMANHO_PADRAO_ALUNOS = 10;

export function useAlunos() {
  const [alunos, setAlunos] = useState<Aluno[]>([]);
  const [carregando, setCarregando] = useState<boolean>(true);
  const [busca, setBusca] = useState<string>("");
  const [apenasAtivos, setApenasAtivos] = useState<boolean>(true);

  // Paginação
  const [pagina, setPagina] = useState<number>(1);
  const [tamanho, setTamanho] = useState<number>(TAMANHO_PADRAO_ALUNOS);
  const [total, setTotal] = useState<number>(0);
  const [totalPaginas, setTotalPaginas] = useState<number>(1);

  // Modais e Ações
  const [modalCadastroAberto, setModalCadastroAberto] = useState<boolean>(false);
  const [alunoParaInativar, setAlunoParaInativar] = useState<Aluno | null>(null);
  const [reativandoId, setReativandoId] = useState<string | null>(null);

  const carregarAlunos = useCallback(async () => {
    setCarregando(true);
    try {
      const dados = await alunoApi.listar({
        busca: busca.trim() || undefined,
        apenas_ativos: apenasAtivos,
        pagina,
        tamanho_pagina: tamanho,
      });
      setAlunos(dados.itens);
      setTotal(dados.total);
      setTotalPaginas(dados.total_paginas);
    } catch (err: unknown) {
      const { mensagemGeral } = extrairErrosAPI(err);
      toast.error(mensagemGeral || "Erro ao carregar lista de alunos.");
    } finally {
      setCarregando(false);
    }
  }, [busca, apenasAtivos, pagina, tamanho]);

  // Ao mudar busca/filtros, volta para página 1
  useEffect(() => {
    setPagina(1);
  }, [busca, apenasAtivos, tamanho]);

  // Debounce para busca por texto
  useEffect(() => {
    const timer = setTimeout(() => {
      carregarAlunos();
    }, 300);
    return () => clearTimeout(timer);
  }, [carregarAlunos]);

  const handleTamanhoChange = (novoTamanho: number) => {
    setTamanho(novoTamanho);
    setPagina(1);
  };

  const handleReativar = async (aluno: Aluno) => {
    setReativandoId(aluno.id);
    try {
      await alunoApi.reativar(aluno.id);
      toast.success("Aluno reativado com sucesso!", {
        description: `O acesso de ${aluno.nome_completo} ao sistema foi restaurado.`,
      });
      await carregarAlunos();
    } catch (err: unknown) {
      const { mensagemGeral } = extrairErrosAPI(err);
      toast.error(mensagemGeral || "Erro ao tentar reativar o aluno.");
    } finally {
      setReativandoId(null);
    }
  };

  return {
    alunos,
    carregando,
    busca,
    setBusca,
    apenasAtivos,
    setApenasAtivos,
    pagina,
    setPagina,
    tamanho,
    total,
    totalPaginas,
    handleTamanhoChange,
    modalCadastroAberto,
    setModalCadastroAberto,
    alunoParaInativar,
    setAlunoParaInativar,
    reativandoId,
    carregarAlunos,
    handleReativar,
  };
}
