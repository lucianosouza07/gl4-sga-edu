import React, { useState } from "react";
import { alunosService } from "@/services/alunosService";
import type { AlunoCreate } from "@/types/aluno";
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

interface ModalCadastroAlunoProps {
  aberto: boolean;
  onOpenChange: (aberto: boolean) => void;
  onSucesso: () => void;
}

export const ModalCadastroAluno: React.FC<ModalCadastroAlunoProps> = ({
  aberto,
  onOpenChange,
  onSucesso,
}) => {
  const [formData, setFormData] = useState<AlunoCreate>({
    matricula: "",
    nome_completo: "",
    cpf: "",
    email: "",
    telefone: "",
    data_nascimento: "",
    senha_inicial: "",
  });

  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  const handleChange = (campo: keyof AlunoCreate, valor: string) => {
    setFormData((prev) => ({ ...prev, [campo]: valor }));
    if (erro) setErro(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro(null);
    setSalvando(true);

    try {
      const payload: AlunoCreate = {
        matricula: formData.matricula.trim(),
        nome_completo: formData.nome_completo.trim(),
        cpf: formData.cpf.replace(/\D/g, ""), // Limpa pontuações
        email: formData.email.trim(),
        telefone: formData.telefone ? formData.telefone.trim() : null,
        data_nascimento: formData.data_nascimento,
        senha_inicial: formData.senha_inicial ? formData.senha_inicial : null,
      };

      await alunosService.cadastrar(payload);
      toast.success("Aluno cadastrado com sucesso!", {
        description: `Matrícula ${payload.matricula} vinculada à conta de usuário.`,
      });

      // Limpa o formulário e fecha o modal
      setFormData({
        matricula: "",
        nome_completo: "",
        cpf: "",
        email: "",
        telefone: "",
        data_nascimento: "",
        senha_inicial: "",
      });
      onOpenChange(false);
      onSucesso();
    } catch (err: any) {
      const msgErro =
        err.response?.data?.detail ||
        "Ocorreu um erro ao cadastrar o aluno. Verifique os dados.";
      setErro(msgErro);
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Dialog open={aberto} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <UserPlus className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle>
                <Typography variant="h3">Cadastrar Novo Aluno</Typography>
              </DialogTitle>
              <DialogDescription>
                <Typography variant="muted">
                  Preencha os dados acadêmicos e pessoais para gerar a matrícula e o acesso.
                </Typography>
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {erro && (
          <div className="flex items-center gap-2 p-3 text-sm rounded-lg bg-destructive/10 text-destructive border border-destructive/20 animate-in fade-in">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <Typography variant="small">{erro}</Typography>
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
              />
            </Field>

            {/* Matrícula e CPF em 2 colunas */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field>
                <FieldLabel htmlFor="matricula">
                  <Typography variant="small">
                    Matrícula <span className="text-destructive">*</span>
                  </Typography>
                </FieldLabel>
                <Input
                  id="matricula"
                  placeholder="Ex: 20261001"
                  value={formData.matricula}
                  onChange={(e) => handleChange("matricula", e.target.value)}
                  required
                  disabled={salvando}
                />
              </Field>

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
                />
              </Field>
            </div>

            {/* E-mail e Telefone em 2 colunas */}
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
                />
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
                />
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
                />
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
              onClick={() => onOpenChange(false)}
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
