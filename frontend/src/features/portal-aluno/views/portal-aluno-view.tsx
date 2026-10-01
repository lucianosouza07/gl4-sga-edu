import React from "react";
import { Link } from "react-router-dom";
import { usePortalAluno } from "../hooks/use-portal-aluno";
import { CarteirinhaEstudantil } from "../components/carteirinha-estudantil";
import { Typography } from "@/components/ui/typography";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  GraduationCap,
  UserCheck,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
  BookOpen,
} from "lucide-react";

export const PortalAlunoView: React.FC = () => {
  const { perfil, carregando } = usePortalAluno();

  if (carregando) {
    return (
      <div className="space-y-6 max-w-6xl">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-80 w-full lg:col-span-1 rounded-xl" />
          <div className="space-y-4 lg:col-span-2">
            <Skeleton className="h-28 w-full rounded-xl" />
            <Skeleton className="h-48 w-full rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (!perfil) {
    return (
      <div className="p-8 text-center">
        <Typography variant="h4" className="text-destructive">
          Não foi possível carregar os dados do aluno.
        </Typography>
        <Typography variant="muted" className="mt-2">
          Verifique sua conexão ou tente novamente mais tarde.
        </Typography>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Banner de Boas-Vindas */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-2xl bg-linear-to-r from-primary/15 via-primary/5 to-background p-6 border border-primary/20 shadow-xs">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Typography variant="h2" className="text-2xl md:text-3xl font-bold tracking-tight">
              Olá, {perfil.nome_completo.split(" ")[0]}! 👋
            </Typography>
            <Badge variant="secondary" className="gap-1 bg-primary/10 text-primary font-medium">
              <Sparkles className="size-3" /> Portal Discente
            </Badge>
          </div>
          <Typography variant="muted" className="text-sm">
            Bem-vindo ao seu ambiente acadêmico digital. Acesse sua carteirinha e dados cadastrais.
          </Typography>
        </div>

        <div className="flex items-center gap-3">
          <Button
            nativeButton={false}
            render={<Link to="/meus-dados" />}
            className="gap-2 shadow-xs"
          >
            <UserCheck className="size-4" />
            <span>Meus Dados Cadastrais</span>
            <ArrowRight className="size-4" />
          </Button>
        </div>
      </div>

      {/* Grid Principal: Carteirinha + Resumo Acadêmico */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Coluna 1: Carteirinha Estudantil */}
        <div className="lg:col-span-1 flex justify-center lg:justify-start">
          <CarteirinhaEstudantil aluno={perfil} />
        </div>

        {/* Coluna 2 e 3: Atalhos e Módulos */}
        <div className="lg:col-span-2 space-y-5">
          {/* Card: Status da Matrícula */}
          <Card className="border-border/80">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <GraduationCap className="size-5" />
                  </div>
                  <div>
                    <CardTitle className="text-base">Situação da Matrícula</CardTitle>
                    <CardDescription className="text-xs">
                      Status oficial junto ao registro acadêmico institucional
                    </CardDescription>
                  </div>
                </div>
                <Badge variant={perfil.status === "ATIVO" ? "default" : "destructive"}>
                  {perfil.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm pt-1">
                <div className="rounded-lg bg-muted/40 p-3">
                  <Typography variant="muted" className="text-xs uppercase font-semibold">
                    Matrícula
                  </Typography>
                  <Typography variant="small" className="font-mono font-bold text-sm mt-0.5">
                    {perfil.matricula}
                  </Typography>
                </div>

                <div className="rounded-lg bg-muted/40 p-3">
                  <Typography variant="muted" className="text-xs uppercase font-semibold">
                    Ano / Semestre
                  </Typography>
                  <Typography variant="small" className="font-bold text-sm mt-0.5">
                    {perfil.matricula.length >= 5
                      ? `${perfil.matricula.substring(0, 4)}.${perfil.matricula.substring(4, 5)}`
                      : "2026.1"}
                  </Typography>
                </div>

                <div className="rounded-lg bg-muted/40 p-3 col-span-2 sm:col-span-1">
                  <Typography variant="muted" className="text-xs uppercase font-semibold">
                    Cadastro
                  </Typography>
                  <Typography variant="small" className="font-medium text-xs mt-0.5">
                    {new Date(perfil.criado_em).toLocaleDateString("pt-BR")}
                  </Typography>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Card: Próximos Módulos Acadêmicos (Espaço para Codebase Design Seams) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Boletim e Notas (Preview) */}
            <Card className="border-dashed border-border/80 bg-card/60">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <div className="flex size-8 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                    <FileText className="size-4" />
                  </div>
                  <div>
                    <CardTitle className="text-sm">Boletim Escolar</CardTitle>
                    <CardDescription className="text-xs">Notas e Médias</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-2">
                <Typography variant="muted" className="text-xs">
                  O módulo de notas estará disponível assim que o período de avaliações for iniciado pelos docentes.
                </Typography>
              </CardContent>
            </Card>

            {/* Frequência e Aulas (Preview) */}
            <Card className="border-dashed border-border/80 bg-card/60">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <div className="flex size-8 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                    <Clock className="size-4" />
                  </div>
                  <div>
                    <CardTitle className="text-sm">Frequência e Presença</CardTitle>
                    <CardDescription className="text-xs">Diário Eletrônico</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-2">
                <Typography variant="muted" className="text-xs">
                  O acompanhamento de faltas e presença por disciplina será integrado nas próximas etapas.
                </Typography>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
