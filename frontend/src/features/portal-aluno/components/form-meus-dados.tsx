import React, { useState, useEffect } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import { Separator } from "@/components/ui/separator";
import {
  Field,
  FieldGroup,
  FieldLabel,
  FieldDescription,
} from "@/components/ui/field";
import {
  User,
  Phone,
  Mail,
  Calendar,
  Lock,
  KeyRound,
  CheckCircle2,
  ShieldCheck,
  Loader2,
  Save,
} from "lucide-react";
import type { AlunoPerfil } from "../data/portal-aluno.types";

interface FormMeusDadosProps {
  aluno: AlunoPerfil;
  salvando: boolean;
  onSalvarTelefone: (telefone: string) => Promise<boolean>;
  onAbrirModalSenha: () => void;
}

export const FormMeusDados: React.FC<FormMeusDadosProps> = ({
  aluno,
  salvando,
  onSalvarTelefone,
  onAbrirModalSenha,
}) => {
  const [telefone, setTelefone] = useState(aluno.telefone || "");
  const [modificado, setModificado] = useState(false);

  useEffect(() => {
    setTelefone(aluno.telefone || "");
    setModificado(false);
  }, [aluno.telefone]);

  const handleTelefoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setTelefone(val);
    setModificado(val !== (aluno.telefone || ""));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modificado) return;
    const sucesso = await onSalvarTelefone(telefone);
    if (sucesso) {
      setModificado(false);
    }
  };

  const formatarData = (dataIso: string) => {
    try {
      const [ano, mes, dia] = dataIso.split("-");
      if (ano && mes && dia) return `${dia}/${mes}/${ano}`;
      return dataIso;
    } catch {
      return dataIso;
    }
  };

  const formatarCpf = (cpf: string) => {
    const limpo = cpf.replace(/\D/g, "");
    if (limpo.length === 11) {
      return `${limpo.slice(0, 3)}.${limpo.slice(3, 6)}.${limpo.slice(6, 9)}-${limpo.slice(9, 11)}`;
    }
    return cpf;
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* 1. Dados Institucionais e Cadastrais (Somente Leitura) */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <ShieldCheck className="size-5" />
              </div>
              <div>
                <CardTitle className="text-lg">Dados Institucionais</CardTitle>
                <CardDescription>
                  Informações acadêmicas e de registro civil geridas pela Secretaria Acadêmica.
                </CardDescription>
              </div>
            </div>
            <Badge variant="outline" className="w-fit gap-1 py-1 px-3">
              <CheckCircle2 className="size-3.5 text-primary" />
              Status: <span className="font-semibold text-foreground">{aluno.status}</span>
            </Badge>
          </div>
        </CardHeader>

        <Separator />

        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Field>
              <FieldLabel className="text-xs uppercase text-muted-foreground font-semibold flex items-center gap-1.5">
                <User className="size-3.5" /> Nome Completo
              </FieldLabel>
              <Input value={aluno.nome_completo} disabled className="bg-muted/50 cursor-not-allowed font-medium" />
              <FieldDescription className="text-[11px]">
                Para retificação de nome civil, procure a Secretaria.
              </FieldDescription>
            </Field>

            <Field>
              <FieldLabel className="text-xs uppercase text-muted-foreground font-semibold flex items-center gap-1.5">
                <Lock className="size-3.5" /> Matrícula Acadêmica
              </FieldLabel>
              <Input value={aluno.matricula} disabled className="bg-muted/50 cursor-not-allowed font-mono font-bold" />
              <FieldDescription className="text-[11px]">
                Identificador institucional único e permanente.
              </FieldDescription>
            </Field>

            <Field>
              <FieldLabel className="text-xs uppercase text-muted-foreground font-semibold flex items-center gap-1.5">
                <Lock className="size-3.5" /> CPF
              </FieldLabel>
              <Input value={formatarCpf(aluno.cpf)} disabled className="bg-muted/50 cursor-not-allowed font-mono" />
            </Field>

            <Field>
              <FieldLabel className="text-xs uppercase text-muted-foreground font-semibold flex items-center gap-1.5">
                <Calendar className="size-3.5" /> Data de Nascimento
              </FieldLabel>
              <Input value={formatarData(aluno.data_nascimento)} disabled className="bg-muted/50 cursor-not-allowed" />
            </Field>

            <Field className="md:col-span-2">
              <FieldLabel className="text-xs uppercase text-muted-foreground font-semibold flex items-center gap-1.5">
                <Mail className="size-3.5" /> E-mail Institucional (Login)
              </FieldLabel>
              <Input value={aluno.email} disabled className="bg-muted/50 cursor-not-allowed font-mono text-sm" />
            </Field>
          </div>
        </CardContent>
      </Card>

      {/* 2. Informações Pessoais Editáveis (Telefone) */}
      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Phone className="size-5" />
              </div>
              <div>
                <CardTitle className="text-lg">Dados de Contato</CardTitle>
                <CardDescription>
                  Mantenha seu telefone atualizado para comunicações institucionais urgentes.
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <Separator />

          <CardContent className="pt-6">
            <FieldGroup className="max-w-md">
              <Field>
                <FieldLabel className="text-sm font-semibold">Telefone / WhatsApp</FieldLabel>
                <Input
                  type="tel"
                  placeholder="(71) 99999-9999"
                  value={telefone}
                  onChange={handleTelefoneChange}
                  disabled={salvando}
                />
                <FieldDescription className="text-xs text-muted-foreground">
                  Informe DDD + Número para contato.
                </FieldDescription>
              </Field>
            </FieldGroup>
          </CardContent>

          <CardFooter className="flex justify-end gap-3 border-t border-border/60 pt-4 bg-muted/20">
            <Button
              type="submit"
              disabled={!modificado || salvando}
              className="gap-2"
            >
              {salvando ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Save className="size-4" />
              )}
              Salvar Alterações
            </Button>
          </CardFooter>
        </Card>
      </form>

      {/* 3. Segurança e Senha de Acesso */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <KeyRound className="size-5" />
              </div>
              <div>
                <CardTitle className="text-lg">Segurança & Credenciais</CardTitle>
                <CardDescription>
                  Altere sua senha periodicamente para manter sua conta protegida.
                </CardDescription>
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              onClick={onAbrirModalSenha}
              className="gap-2 shrink-0"
            >
              <KeyRound className="size-4" />
              Alterar Senha
            </Button>
          </div>
        </CardHeader>
      </Card>
    </div>
  );
};
