import { useState, useEffect, useCallback } from "react";
import { portalAlunoApi } from "../services/portal-aluno.api";
import type { AlunoPerfil } from "../data/portal-aluno.types";
import { toast } from "sonner";
import { extrairErrosAPI } from "@/api/handle-api-error";

export function usePortalAluno() {
  const [perfil, setPerfil] = useState<AlunoPerfil | null>(null);
  const [carregando, setCarregando] = useState<boolean>(true);
  const [salvando, setSalvando] = useState<boolean>(false);
  const [modalSenhaAberto, setModalSenhaAberto] = useState<boolean>(false);

  const carregarPerfil = useCallback(async () => {
    setCarregando(true);
    try {
      const dados = await portalAlunoApi.obterMeuPerfil();
      setPerfil(dados);
    } catch (err: unknown) {
      const { mensagemGeral } = extrairErrosAPI(err);
      toast.error(mensagemGeral || "Erro ao carregar dados do aluno.");
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregarPerfil();
  }, [carregarPerfil]);

  const atualizarTelefone = async (telefone: string): Promise<boolean> => {
    setSalvando(true);
    try {
      const atualizado = await portalAlunoApi.atualizarMeuPerfil({
        telefone: telefone.trim() || null,
      });
      setPerfil(atualizado);
      toast.success("Dados de contato atualizados com sucesso!");
      return true;
    } catch (err: unknown) {
      const { mensagemGeral } = extrairErrosAPI(err);
      toast.error(mensagemGeral || "Erro ao atualizar dados de contato.");
      return false;
    } finally {
      setSalvando(false);
    }
  };

  const alterarSenha = async (senhaAtual: string, novaSenha: string): Promise<boolean> => {
    setSalvando(true);
    try {
      await portalAlunoApi.atualizarMeuPerfil({
        senha_atual: senhaAtual,
        nova_senha: novaSenha,
      });
      toast.success("Senha alterada com sucesso!");
      setModalSenhaAberto(false);
      return true;
    } catch (err: unknown) {
      const { mensagemGeral } = extrairErrosAPI(err);
      toast.error(mensagemGeral || "Erro ao alterar a senha.");
      return false;
    } finally {
      setSalvando(false);
    }
  };

  return {
    perfil,
    carregando,
    salvando,
    modalSenhaAberto,
    setModalSenhaAberto,
    recarregar: carregarPerfil,
    atualizarTelefone,
    alterarSenha,
  };
}
