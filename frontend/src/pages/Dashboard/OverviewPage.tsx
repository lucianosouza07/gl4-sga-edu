import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { alunosService } from "@/services/alunosService";
import { Typography } from "@/components/ui/typography";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Users, GraduationCap, ShieldCheck, ArrowRight } from "lucide-react";

export const OverviewPage: React.FC = () => {
  const { user } = useAuth();
  const [totalAlunos, setTotalAlunos] = useState<number>(0);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    async function carregarMetricas() {
      try {
        const alunos = await alunosService.listar({ apenas_ativos: true });
        setTotalAlunos(alunos.length);
      } catch {
        // Se aluno comum não tiver permissão para listar todos, trata silenciosamente
        setTotalAlunos(0);
      } finally {
        setCarregando(false);
      }
    }

    carregarMetricas();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Banner de Boas-Vindas */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 rounded-xl bg-linear-to-r from-primary/10 via-primary/5 to-transparent border border-primary/20">
        <div>
          <Typography variant="h2">Olá, {user?.nome}!</Typography>
          <Typography variant="muted" className="mt-1">
            Bem-vindo ao GL4 SGA-EDU. Seu perfil atual é: <strong>{user?.perfil}</strong>.
          </Typography>
        </div>
        {(user?.perfil === "ADMIN" || user?.perfil === "SECRETARIA") && (
          <Button render={<Link to="/alunos" />}>
            <span>Acessar Alunos</span>
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Cards de Métricas */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>
              <Typography variant="small" className="text-muted-foreground font-medium">
                Alunos Ativos
              </Typography>
            </CardTitle>
            <Users className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <Typography variant="h2">
              {carregando ? "..." : totalAlunos}
            </Typography>
            <Typography variant="muted" className="text-xs mt-1">
              Cadastrados e com matrícula ativa
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>
              <Typography variant="small" className="text-muted-foreground font-medium">
                Ano Letivo / Semestre
              </Typography>
            </CardTitle>
            <GraduationCap className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <Typography variant="h2">2026.1</Typography>
            <Typography variant="muted" className="text-xs mt-1">
              Período acadêmico vigente
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>
              <Typography variant="small" className="text-muted-foreground font-medium">
                Nível de Acesso
              </Typography>
            </CardTitle>
            <ShieldCheck className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <Typography variant="h2">{user?.perfil}</Typography>
            <Typography variant="muted" className="text-xs mt-1">
              Controle de acesso por papel (RBAC)
            </Typography>
          </CardContent>
        </Card>
      </div>

      {/* Orientações Rápidas */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Typography variant="h4">Gestão do Módulo de Alunos</Typography>
          </CardTitle>
          <CardDescription>
            <Typography variant="muted">
              Orientações sobre as operações disponíveis para a equipe pedagógica.
            </Typography>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Typography variant="p">
            • <strong>Cadastro Conjunto:</strong> Cada aluno cadastrado pela Secretaria/Admin tem sua conta de usuário (IAM) criada automaticamente com senha padrão (Mudar@123).
          </Typography>
          <Typography variant="p">
            • <strong>Inativação Lógica (Soft Delete):</strong> A inativação preserva o histórico acadêmico e revoga imediatamente as permissões de login do aluno.
          </Typography>
        </CardContent>
      </Card>
    </div>
  );
};
