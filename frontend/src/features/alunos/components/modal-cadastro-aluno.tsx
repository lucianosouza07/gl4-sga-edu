import React, { useState } from "react";
import { alunoApi } from "../services/aluno.api";
import type { AlunoCreate } from "../data/aluno.types";
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
} from "@/components/ui/field";
import { toast } from "sonner";
import { UserPlus, Loader2, AlertCircle } from "lucide-react";
import { extrairErrosAPI } from "@/api/handle-api-error";

export interface ModalCadastroAlunoProps {
  aberto: boolean;
  onOpenChange: (aberto: boolean) => void;
  onSucesso: () => void;
}

const FORM_VAZIO: AlunoCreate = {
  nome_completo: "",
  cpf: "",
  email: "",
  telefone: "",
  data_nascimento: "",
  senha_inicial: "",
};

export const ModalCadastroAluno: React.FC<ModalCadastroAlunoProps> = ({
  aberto,
  onOpenChange,
  onSucesso,
}) => {
  const [formData, setFormData] = useState<AlunoCreate>(FORM_VAZIO);
  const [mensagemGeral, setMensagemGeral] = useState<string | null>(null);
  const [errosPorCampo, setErrosPorCampo] = useState<Record<string, string>>({});
  const [salvando, setSalvando] = useState(false);

  const limparErros = () => {
    setMensagemGeral(null);
    setErrosPorCampo({});
  };

  const handleChange = (campo: keyof AlunoCreate, valor: string) => {
    setFormData((prev) => ({ ...prev, [campo]: valor }));
    // Remove o erro específico do campo ao editar
    if (errosPorCampo[campo]) {
      setErrosPorCampo((prev) => {
        const next = { ...prev };
        delete next[campo];
        return next;
      });
    }
    if (Object.keys(errosPorCampo).length === 0) setMensagemGeral(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    limparErros();
    setSalvando(true);

    try {
      const payload: AlunoCreate = {
        nome_completo: formData.nome_completo.trim(),
        cpf: formData.cpf.replace(/\D/g, ""),
        email: formData.email.trim(),
        telefone: formData.telefone ? formData.telefone.trim() : null,
        data_nascimento: formData.data_nascimento,
        senha_inicial: formData.senha_inicial ? formData.senha_inicial : null,
      };

      const aluno = await alunoApi.cadastrar(payload);
      toast.success("Aluno cadastrado com sucesso!", {
        description: `Matrícula ${aluno.matricula} gerada para o aluno.`,
      });

      setFormData(FORM_VAZIO);
      onOpenChange(false);
      onSucesso();
    } catch (err: unknown) {
      const { mensagemGeral: msg, errosPorCampo: campos } = extrairErrosAPI(err);
      setMensagemGeral(msg);
      setErrosPorCampo(campos);
    } finally {
      setSalvando(false);
    }
  };

  const temErros = Object.keys(errosPorCampo).length > 0;

  return (
    <Dialog open={aberto} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <UserPlus className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle className="text-xl font-semibold tracking-tight">
                Cadastrar Novo Aluno
              </DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground">
                Preencha os dados acadêmicos e pessoais para gerar a matrícula e o acesso.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Banner de erro geral */}
        {mensagemGeral && (
          <div className="flex flex-col gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20 animate-in fade-in">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <Typography variant="small" className="font-medium">
                {mensagemGeral}
              </Typography>
            </div>
            {/* Lista de erros específicos por campo */}
            {temErros && (
              <ul className="pl-6 space-y-0.5">
                {Object.entries(errosPorCampo).map(([campo, mensagem]) => (
                  <li key={campo} className="text-xs text-destructive/90 list-disc">
                    <span className="font-semibold capitalize">{campo.replace(/_/g, " ")}</span>: {mensagem}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <FieldGroup>
            {/* Nome Completo */}
            <Field>
              <FieldLabel htmlFor="nome_completo">
                <Typography variant="small">
                  Nome Completo <span className="text-destructive">*</span>
                </Typography>
              </FieldLabel>
              <Input
                id="nome_completo"
                placeholder="Ex: Carlos Eduardo Silva"
                value={formData.nome_completo}
                onChange={(e) => handleChange("nome_completo", e.target.value)}
                required
                disabled={salvando}
                className={errosPorCampo.nome_completo ? "border-destructive focus-visible:ring-destructive/30" : ""}
              />
              {errosPorCampo.nome_completo && (
                <p className="text-xs text-destructive mt-1">{errosPorCampo.nome_completo}</p>
              )}
            </Field>

            {/* CPF */}
            <div className="grid grid-cols-1 gap-4">
              <Field>
                <FieldLabel htmlFor="cpf">
                  <Typography variant="small">
                    CPF <span className="text-destructive">*</span>
                  </Typography>
                </FieldLabel>
                <Input
                  id="cpf"
                  placeholder="000.000.000-00"
                  value={formData.cpf}
                  onChange={(e) => handleChange("cpf", e.target.value)}
                  required
                  maxLength={14}
                  disabled={salvando}
                  className={errosPorCampo.cpf ? "border-destructive focus-visible:ring-destructive/30" : ""}
                />
                {errosPorCampo.cpf && (
                  <p className="text-xs text-destructive mt-1">{errosPorCampo.cpf}</p>
                )}
              </Field>
            </div>

            {/* E-mail e Telefone */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field>
                <FieldLabel htmlFor="email">
                  <Typography variant="small">
                    E-mail Institucional <span className="text-destructive">*</span>
                  </Typography>
                </FieldLabel>
                <Input
                  id="email"
                  type="email"
                  placeholder="aluno@gl4.edu"
                  value={formData.email}
                  onChange={(e) => handleChange("email", e.target.value)}
                  required
                  disabled={salvando}
                  className={errosPorCampo.email ? "border-destructive focus-visible:ring-destructive/30" : ""}
                />
                {errosPorCampo.email && (
                  <p className="text-xs text-destructive mt-1">{errosPorCampo.email}</p>
                )}
              </Field>

              <Field>
                <FieldLabel htmlFor="telefone">
                  <Typography variant="small">Telefone de Contato</Typography>
                </FieldLabel>
                <Input
                  id="telefone"
                  placeholder="(11) 98888-7777"
                  value={formData.telefone || ""}
                  onChange={(e) => handleChange("telefone", e.target.value)}
                  disabled={salvando}
                  className={errosPorCampo.telefone ? "border-destructive focus-visible:ring-destructive/30" : ""}
                />
                {errosPorCampo.telefone && (
                  <p className="text-xs text-destructive mt-1">{errosPorCampo.telefone}</p>
                )}
              </Field>
            </div>

            {/* Data de Nascimento e Senha Inicial */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field>
                <FieldLabel htmlFor="data_nascimento">
                  <Typography variant="small">
                    Data de Nascimento <span className="text-destructive">*</span>
                  </Typography>
                </FieldLabel>
                <Input
                  id="data_nascimento"
                  type="date"
                  value={formData.data_nascimento}
                  onChange={(e) => handleChange("data_nascimento", e.target.value)}
                  required
                  disabled={salvando}
                  className={errosPorCampo.data_nascimento ? "border-destructive focus-visible:ring-destructive/30" : ""}
                />
                {errosPorCampo.data_nascimento && (
                  <p className="text-xs text-destructive mt-1">{errosPorCampo.data_nascimento}</p>
                )}
              </Field>

              <Field>
                <FieldLabel htmlFor="senha_inicial">
                  <Typography variant="small">Senha Inicial (Opcional)</Typography>
                </FieldLabel>
                <Input
                  id="senha_inicial"
                  type="password"
                  placeholder="Padrão: Mudar@123"
                  value={formData.senha_inicial || ""}
                  onChange={(e) => handleChange("senha_inicial", e.target.value)}
                  disabled={salvando}
                />
                <FieldDescription>
                  <Typography variant="muted" className="text-xs">
                    Se vazio, será aplicada a senha padrão.
                  </Typography>
                </FieldDescription>
              </Field>
            </div>
          </FieldGroup>

          <DialogFooter className="pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                onOpenChange(false);
                limparErros();
              }}
              disabled={salvando}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={salvando}>
              {salvando ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Cadastrando...
                </>
              ) : (
                "Confirmar Cadastro"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
