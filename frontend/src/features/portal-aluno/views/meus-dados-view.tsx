import React from "react";
import { usePortalAluno } from "../hooks/use-portal-aluno";
import { FormMeusDados } from "../components/form-meus-dados";
import { ModalAlterarSenha } from "../components/modal-alterar-senha";
import { Typography } from "@/components/ui/typography";
import { Skeleton } from "@/components/ui/skeleton";
import { UserCheck } from "lucide-react";

export const MeusDadosView: React.FC = () => {
  const {
    perfil,
    carregando,
    salvando,
    modalSenhaAberto,
    setModalSenhaAberto,
    atualizarTelefone,
    alterarSenha,
  } = usePortalAluno();

  if (carregando) {
    return (
      <div className="space-y-6 max-w-4xl">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-64 w-full rounded-xl" />
        <Skeleton className="h-40 w-full rounded-xl" />
      </div>
    );
  }

  if (!perfil) {
    return (
      <div className="p-8 text-center">
        <Typography variant="h4" className="text-destructive">
          Não foi possível carregar seus dados cadastrais.
        </Typography>
        <Typography variant="muted" className="mt-2">
          Tente recarregar a página.
        </Typography>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Cabeçalho da Página */}
      <div className="space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <UserCheck className="size-5" />
          </div>
          <Typography variant="h2" className="text-2xl font-bold tracking-tight">
            Meus Dados Cadastrais
          </Typography>
        </div>
        <Typography variant="muted" className="text-sm">
          Consulte suas informações acadêmicas oficiais e mantenha seus contatos atualizados.
        </Typography>
      </div>

      {/* Formulário Principal */}
      <FormMeusDados
        aluno={perfil}
        salvando={salvando}
        onSalvarTelefone={atualizarTelefone}
        onAbrirModalSenha={() => setModalSenhaAberto(true)}
      />

      {/* Modal de Alteração de Senha */}
      <ModalAlterarSenha
        aberto={modalSenhaAberto}
        onOpenChange={setModalSenhaAberto}
        onConfirmar={alterarSenha}
        salvando={salvando}
      />
    </div>
  );
};
