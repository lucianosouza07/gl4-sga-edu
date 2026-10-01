import React, { useState } from "react";
import type { Aluno } from "@/types/aluno";
import { alunosService } from "@/services/alunosService";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { Typography } from "@/components/ui/typography";
import { toast } from "sonner";
import { UserX, Loader2 } from "lucide-react";

interface ModalInativarAlunoProps {
  aluno: Aluno | null;
  aberto: boolean;
  onOpenChange: (aberto: boolean) => void;
  onSucesso: () => void;
}

export const ModalInativarAluno: React.FC<ModalInativarAlunoProps> = ({
  aluno,
  aberto,
  onOpenChange,
  onSucesso,
}) => {
  const [inativando, setInativando] = useState(false);

  if (!aluno) return null;

  const handleConfirmar = async () => {
    setInativando(true);
    try {
      await alunosService.inativar(aluno.id);
      toast.success("Aluno inativado com sucesso!", {
        description: `A matrícula ${aluno.matricula} e o login de acesso foram desativados.`,
      });
      onOpenChange(false);
      onSucesso();
    } catch (err: any) {
      const msg =
        err.response?.data?.detail || "Erro ao tentar inativar o aluno.";
      toast.error(msg);
    } finally {
      setInativando(false);
    }
  };

  return (
    <AlertDialog open={aberto} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
            <UserX className="h-6 w-6" />
          </div>
          <AlertDialogTitle className="text-center">
            <Typography variant="h3">Confirmar Inativação</Typography>
          </AlertDialogTitle>
          <AlertDialogDescription className="text-center">
            <Typography variant="muted">
              Tem certeza que deseja inativar o(a) aluno(a){" "}
              <strong>{aluno.nome_completo}</strong> (Matrícula: {aluno.matricula})?
            </Typography>
            <div className="mt-2 text-xs text-destructive font-medium">
              Esta ação desativará o status do aluno e revogará imediatamente o acesso ao sistema.
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={inativando}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            onClick={handleConfirmar}
            disabled={inativando}
          >
            {inativando ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Inativando...
              </>
            ) : (
              "Sim, Inativar"
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
