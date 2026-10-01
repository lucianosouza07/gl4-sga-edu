import React from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { GraduationCap, QrCode, CheckCircle2, ShieldAlert } from "lucide-react";
import type { AlunoPerfil } from "../data/portal-aluno.types";

interface CarteirinhaEstudantilProps {
  aluno: AlunoPerfil;
}

export const CarteirinhaEstudantil: React.FC<CarteirinhaEstudantilProps> = ({ aluno }) => {
  const formatarData = (dataIso: string) => {
    try {
      const [ano, mes, dia] = dataIso.split("-");
      if (ano && mes && dia) {
        return `${dia}/${mes}/${ano}`;
      }
      return dataIso;
    } catch {
      return dataIso;
    }
  };

  const getIniciais = (nome: string) => {
    return nome
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((parte) => parte[0].toUpperCase())
      .join("");
  };

  const isAtivo = aluno.status === "ATIVO";

  // Extrai o ano e semestre civil da matrícula (ex: 202620001 -> 2026.2)
  const formatarPeriodoIngresso = (matricula: string) => {
    if (matricula.length >= 5) {
      const ano = matricula.substring(0, 4);
      const sem = matricula.substring(4, 5);
      return `${ano}.${sem}`;
    }
    return "2026.1";
  };

  return (
    <Card className="relative overflow-hidden border-2 shadow-lg bg-linear-to-br from-card via-card to-primary/5 max-w-md w-full">
      {/* Top Banner Decorativo */}
      <div className="h-3 bg-linear-to-r from-primary via-primary/80 to-primary/60" />

      <CardHeader className="pb-3 pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-xs">
              <GraduationCap className="h-5 w-5" />
            </div>
            <div>
              <Typography variant="small" className="font-bold tracking-tight text-primary">
                GL4 SGA-EDU
              </Typography>
              <Typography variant="muted" className="text-xs uppercase tracking-wider">
                Identidade Estudantil
              </Typography>
            </div>
          </div>
          <Badge variant={isAtivo ? "default" : "destructive"} className="gap-1 px-2.5 py-0.5">
            {isAtivo ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Ativo</span>
              </>
            ) : (
              <>
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>Inativo</span>
              </>
            )}
          </Badge>
        </div>
      </CardHeader>

      <Separator />

      <CardContent className="pt-4 pb-5 space-y-4">
        {/* Identificação Principal do Aluno */}
        <div className="flex items-start gap-4">
          <Avatar className="h-20 w-20 rounded-xl border-2 border-primary/20 shadow-xs">
            <AvatarFallback className="text-xl font-bold bg-primary/10 text-primary">
              {getIniciais(aluno.nome_completo)}
            </AvatarFallback>
          </Avatar>

          <div className="space-y-1 flex-1 min-w-0">
            <Typography variant="h4" className="text-base font-bold truncate leading-tight">
              {aluno.nome_completo}
            </Typography>
            <div className="space-y-0.5 text-xs text-muted-foreground">
              <div className="flex items-center justify-between">
                <span>Matrícula:</span>
                <span className="font-mono font-bold text-foreground">{aluno.matricula}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Ingresso:</span>
                <span className="font-medium text-foreground">{formatarPeriodoIngresso(aluno.matricula)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Nascimento:</span>
                <span className="font-medium text-foreground">{formatarData(aluno.data_nascimento)}</span>
              </div>
            </div>
          </div>
        </div>

        <Separator className="border-dashed" />

        {/* Rodapé com Código e Verificação */}
        <div className="flex items-center justify-between pt-1">
          <div className="space-y-0.5">
            <Typography variant="muted" className="text-[10px] uppercase font-semibold">
              E-mail Institucional
            </Typography>
            <Typography variant="small" className="text-xs truncate max-w-[220px]">
              {aluno.email}
            </Typography>
          </div>

          <div className="flex flex-col items-center justify-center p-1.5 rounded-lg bg-background/80 border shadow-2xs">
            <QrCode className="h-10 w-10 text-primary" />
            <Typography variant="muted" className="text-[8px] font-mono mt-0.5">
              AUTENTICADO
            </Typography>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
