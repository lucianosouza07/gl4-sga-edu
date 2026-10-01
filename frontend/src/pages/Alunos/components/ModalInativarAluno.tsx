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
import { CircleAlert, UserX, Loader2 } from "lucide-react";

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
      <AlertDialogContent className="max-w-[calc(100%-2rem)] gap-0 overflow-hidden border-border/80 bg-card p-0 shadow-2xl sm:max-w-lg">
        <AlertDialogHeader className="gap-5 p-6 pb-6 sm:text-center">
          <div className="mx-auto flex size-14 items-center justify-center rounded-full bg-destructive/10 text-destructive ring-8 ring-destructive/5">
            <UserX className="size-6" aria-hidden="true" />
          </div>
          <div className="space-y-2">
            <AlertDialogTitle className="text-center text-xl font-semibold tracking-tight">
              Confirmar inativação
            </AlertDialogTitle>
            <AlertDialogDescription className="text-center text-sm leading-relaxed">
              A inativação bloqueará imediatamente o acesso do aluno ao sistema. Confira os dados antes de continuar.
            </AlertDialogDescription>
          </div>

          <div className="w-full rounded-lg border bg-muted/40 px-4 py-3 text-left">
            <Typography variant="p" className="font-semibold text-foreground">
              {aluno.nome_completo}
            </Typography>
            <Typography variant="muted" className="mt-1 text-xs">
              Matrícula <span className="font-mono text-foreground">{aluno.matricula}</span>
            </Typography>
          </div>

          <div className="flex w-full gap-3 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-left">
            <CircleAlert className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden="true" />
            <Typography variant="muted" className="text-xs leading-relaxed text-foreground/80">
              O aluno perderá o acesso ao sistema imediatamente. O histórico acadêmico será preservado.
            </Typography>
          </div>
        </AlertDialogHeader>
        <AlertDialogFooter className="mx-0 mb-0 px-6 py-4 sm:flex-row">
          <AlertDialogCancel disabled={inativando}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            className="bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90"
            onClick={handleConfirmar}
            disabled={inativando}
          >
            {inativando ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Inativando...
              </>
            ) : (
              "Inativar aluno"
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
