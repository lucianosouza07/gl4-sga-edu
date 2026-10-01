import React from "react";
import { Link } from "react-router-dom";
import { AlertCircle, ArrowRight, CalendarDays, RefreshCw } from "lucide-react";
import { useAuth } from "@/features/auth";
import { useDashboard } from "../hooks/use-dashboard";
import { DashboardKpis } from "../components/dashboard-kpis";
import { MatriculasBarChart } from "../components/matriculas-bar-chart";
import { SituacaoAlunosPieChart } from "../components/situacao-alunos-pie-chart";
import { UltimosCadastrosTable } from "../components/ultimos-cadastros-table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import {
  PageContainer,
  PageHeader,
  PageHeaderContent,
  PageHeaderTitle,
  PageHeaderDescription,
  PageHeaderActions,
} from "@/components/shared/page-header";

const dataLocal = (instante: string, options: Intl.DateTimeFormatOptions) =>
  new Date(instante).toLocaleString("pt-BR", { ...options, timeZone: "America/Bahia" });

const mesLocal = (mes: string, abreviado = false) =>
  dataLocal(`${mes}-01T12:00:00Z`, { month: abreviado ? "short" : "long", year: "numeric" });

function DashboardInstitucional({ nome }: { nome: string }) {
  const {
    periodo,
    dados,
    carregando,
    erro,
    ultimaConsulta,
    ano,
    consultar,
    setPeriodo,
  } = useDashboard("ano");

  const legenda = dados
    ? `${mesLocal(dados.periodo.inicio.slice(0, 7))} a ${mesLocal(dados.periodo.fim.slice(0, 7))} · mês atual parcial`
    : "Inclui o mês atual, ainda parcial";

  return (
    <PageContainer>
      <PageHeader>
        <PageHeaderContent>
          <PageHeaderTitle>Visão geral</PageHeaderTitle>
          <PageHeaderDescription>
            Olá, {nome.split(" ")[0]}. Acompanhe os alunos e as novas matrículas da instituição.
          </PageHeaderDescription>
        </PageHeaderContent>
        <PageHeaderActions>
          {dados && (
            <Badge variant="outline">
              <CalendarDays data-icon="inline-start" />
              {dados.ano}.{dados.semestre}
            </Badge>
          )}
          <Button variant="outline" nativeButton={false} render={<Link to="/alunos" />}>
            Gerenciar alunos
            <ArrowRight data-icon="inline-end" />
          </Button>
        </PageHeaderActions>
      </PageHeader>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Typography variant="muted" className="text-xs" aria-live="polite">
          {ultimaConsulta
            ? `Última consulta: ${dataLocal(ultimaConsulta, { dateStyle: "short", timeStyle: "medium" })}`
            : "Aguardando a primeira consulta"}
        </Typography>
        <Button
          variant="outline"
          size="sm"
          disabled={carregando}
          onClick={() => consultar()}
        >
          <RefreshCw
            data-icon="inline-start"
            className={carregando ? "animate-spin" : undefined}
          />
          Atualizar
        </Button>
      </div>

      {erro ? (
        <Alert variant="destructive">
          <AlertCircle />
          <AlertTitle>Não foi possível carregar o dashboard</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            Verifique a conexão e tente consultar os dados novamente.
            <Button variant="outline" size="sm" onClick={() => consultar()}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      ) : (
        <>
          {/* Indicadores superiores (KPI Cards) */}
          <DashboardKpis
            dados={dados}
            carregando={carregando}
            legendaNovasMatriculas={legenda}
          />

          {/* Grid com Gráficos: Novas Matrículas (Barras) + Situação dos Alunos (Pie) */}
          <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
            <MatriculasBarChart
              dados={dados}
              carregando={carregando}
              periodo={periodo}
              ano={ano}
              legenda={legenda}
              onPeriodoChange={(novoPeriodo) => {
                setPeriodo(novoPeriodo);
                consultar(novoPeriodo);
              }}
            />

            <SituacaoAlunosPieChart dados={dados} carregando={carregando} />
          </div>

          {/* Tabela de Últimos Cadastros */}
          <UltimosCadastrosTable dados={dados} carregando={carregando} />
        </>
      )}
    </PageContainer>
  );
}

export function OverviewView() {
  const { user } = useAuth();
  if (!user) return null;
  if (user.perfil === "ADMIN" || user.perfil === "SECRETARIA") {
    return <DashboardInstitucional key={user.id} nome={user.nome} />;
  }

  return (
    <PageContainer>
      <Card>
        <CardHeader>
          <CardTitle>
            <Typography variant="h2">Olá, {user.nome}!</Typography>
          </CardTitle>
          <CardDescription>
            Bem-vindo ao GL4 SGA-EDU. Seu perfil atual é: <strong>{user.perfil}</strong>.
          </CardDescription>
        </CardHeader>
      </Card>
    </PageContainer>
  );
}

export default OverviewView;
