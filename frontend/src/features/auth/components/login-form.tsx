import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuth } from "../hooks/use-auth";
import { extrairErrosAPI } from "@/api/handle-api-error";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Typography } from "@/components/ui/typography";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { GraduationCap, Loader2, AlertCircle } from "lucide-react";

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"form">) {
  const [identificador, setIdentificador] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro(null);
    setCarregando(true);

    try {
      await login(identificador, senha);
      navigate("/");
    } catch (err: unknown) {
      const { mensagemGeral } = extrairErrosAPI(err);
      setErro(mensagemGeral || "Não foi possível autenticar. Verifique seus dados e tente novamente.");
    } finally {
      setCarregando(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn("flex flex-col gap-6", className)}
      {...props}
    >
      <FieldGroup>
        <div className="flex flex-col items-center gap-2 text-center mb-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md shadow-primary/20">
            <GraduationCap className="h-6 w-6" />
          </div>
          <Typography variant="h2">GL4 SGA-EDU</Typography>
          <Typography variant="muted">
            Insira suas credenciais institucionais para acessar o portal acadêmico.
          </Typography>
        </div>

        {erro && (
          <div className="flex items-center gap-2 p-3 text-sm rounded-lg bg-destructive/10 text-destructive border border-destructive/20 animate-in fade-in">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <Typography variant="small">{erro}</Typography>
          </div>
        )}

        <Field>
          <FieldLabel htmlFor="identificador">
            <Typography variant="small">E-mail ou Matrícula</Typography>
          </FieldLabel>
          <Input
            id="identificador"
            type="text"
            placeholder="admin@gl4.edu ou 202620001"
            value={identificador}
            onChange={(e) => setIdentificador(e.target.value)}
            required
            autoComplete="username"
            disabled={carregando}
          />
          <FieldDescription>
            <Typography variant="muted">
              Alunos podem usar sua matrícula; Secretaria/Admin utilizam o e-mail institucional.
            </Typography>
          </FieldDescription>
        </Field>

        <Field>
          <div className="flex items-center justify-between">
            <FieldLabel htmlFor="password">
              <Typography variant="small">Senha</Typography>
            </FieldLabel>
          </div>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            autoComplete="current-password"
            disabled={carregando}
          />
        </Field>

        <Field className="pt-2">
          <Button type="submit" className="w-full" disabled={carregando}>
            {carregando ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Autenticando...
              </>
            ) : (
              "Entrar no Sistema"
            )}
          </Button>
        </Field>

        <div className="text-center pt-2">
          <Typography variant="muted">
            Primeiro acesso de aluno? Sua senha padrão inicial foi cadastrada pela Secretaria.
          </Typography>
        </div>
      </FieldGroup>
    </form>
  );
}
