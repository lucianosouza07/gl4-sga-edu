import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Typography } from "@/components/ui/typography";
import {
  Field,
  FieldGroup,
  FieldLabel,
  FieldDescription,
  FieldError,
} from "@/components/ui/field";
import { KeyRound, Loader2, AlertCircle } from "lucide-react";

export interface ModalAlterarSenhaProps {
  aberto: boolean;
  onOpenChange: (aberto: boolean) => void;
  onConfirmar: (senhaAtual: string, novaSenha: string) => Promise<boolean>;
  salvando: boolean;
}

export const ModalAlterarSenha: React.FC<ModalAlterarSenhaProps> = ({
  aberto,
  onOpenChange,
  onConfirmar,
  salvando,
}) => {
  const [senhaAtual, setSenhaAtual] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmarNovaSenha, setConfirmarNovaSenha] = useState("");
  const [erroLocal, setErroLocal] = useState<string | null>(null);

  const resetar = () => {
    setSenhaAtual("");
    setNovaSenha("");
    setConfirmarNovaSenha("");
    setErroLocal(null);
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) resetar();
    onOpenChange(open);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroLocal(null);

    if (!senhaAtual) {
      setErroLocal("Informe sua senha atual.");
      return;
    }

    if (!novaSenha || novaSenha.length < 6) {
      setErroLocal("A nova senha deve ter no mínimo 6 caracteres.");
      return;
    }

    if (novaSenha !== confirmarNovaSenha) {
      setErroLocal("A confirmação não coincide com a nova senha digitada.");
      return;
    }

    if (senhaAtual === novaSenha) {
      setErroLocal("A nova senha não pode ser igual à senha atual.");
      return;
    }

    const sucesso = await onConfirmar(senhaAtual, novaSenha);
    if (sucesso) {
      resetar();
    }
  };

  return (
    <Dialog open={aberto} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-[calc(100%-2rem)] gap-0 overflow-hidden border-border/80 bg-card p-0 shadow-2xl sm:max-w-md">
        {/* Header Visual */}
        <DialogHeader className="gap-3 border-b border-border/60 bg-muted/40 p-6">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <KeyRound className="size-5" />
          </div>
          <div className="space-y-1">
            <DialogTitle className="text-xl font-bold tracking-tight">
              Alterar Senha de Acesso
            </DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Digite sua senha atual e escolha uma nova senha segura.
            </DialogDescription>
          </div>
        </DialogHeader>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {erroLocal && (
            <div className="flex items-start gap-3 rounded-lg border border-destructive/20 bg-destructive/10 p-3.5 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <Typography variant="small" className="font-medium text-destructive">
                {erroLocal}
              </Typography>
            </div>
          )}

          <FieldGroup className="space-y-3.5">
            <Field>
              <FieldLabel className="text-sm font-semibold">
                Senha Atual <span className="text-destructive">*</span>
              </FieldLabel>
              <Input
                type="password"
                placeholder="••••••••"
                value={senhaAtual}
                onChange={(e) => setSenhaAtual(e.target.value)}
                disabled={salvando}
                autoFocus
              />
            </Field>

            <Field>
              <FieldLabel className="text-sm font-semibold">
                Nova Senha <span className="text-destructive">*</span>
              </FieldLabel>
              <Input
                type="password"
                placeholder="Mínimo 6 caracteres"
                value={novaSenha}
                onChange={(e) => setNovaSenha(e.target.value)}
                disabled={salvando}
              />
              <FieldDescription className="text-xs text-muted-foreground">
                Recomendamos combinar letras maiúsculas, números e caracteres especiais.
              </FieldDescription>
            </Field>

            <Field>
              <FieldLabel className="text-sm font-semibold">
                Confirmar Nova Senha <span className="text-destructive">*</span>
              </FieldLabel>
              <Input
                type="password"
                placeholder="Repita a nova senha"
                value={confirmarNovaSenha}
                onChange={(e) => setConfirmarNovaSenha(e.target.value)}
                disabled={salvando}
              />
            </Field>
          </FieldGroup>

          <DialogFooter className="pt-3 border-t border-border/60">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={salvando}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={salvando} className="gap-2">
              {salvando && <Loader2 className="size-4 animate-spin" />}
              Salvar Nova Senha
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
