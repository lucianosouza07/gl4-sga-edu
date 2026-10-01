import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Label, Pie, PieChart, XAxis, YAxis } from "recharts";
import { AlertCircle, ArrowRight, CalendarDays, RefreshCw, TrendingUp, UserCheck, UserPlus, Users, UserX } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { dashboardService } from "@/services/dashboardService";
import type { Dashboard, PeriodoDashboard } from "@/types/dashboard";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Typography } from "@/components/ui/typography";
import {
  PageContainer,
  PageHeader,
  PageHeaderContent,
  PageHeaderTitle,
  PageHeaderDescription,
  PageHeaderActions,
} from "@/components/page-header";

const numero = (valor: number) => valor.toLocaleString("pt-BR");
const percentual = (valor: number, total: number) =>
  (total === 0 ? 0 : valor / total).toLocaleString("pt-BR", { style: "percent", maximumFractionDigits: 1 });
const dataLocal = (instante: string, options: Intl.DateTimeFormatOptions) =>
  new Date(instante).toLocaleString("pt-BR", { ...options, timeZone: "America/Bahia" });
const mesLocal = (mes: string, abreviado = false) => dataLocal(`${mes}-01T12:00:00Z`, {
  month: abreviado ? "short" : "long", year: "numeric",
});
const statusConhecidos: Record<string, { label: string; color: string }> = {
  ATIVO: { label: "Ativo", color: "var(--chart-1)" },
  INATIVO: { label: "Inativo", color: "var(--chart-2)" },
  TRANCADO: { label: "Trancado", color: "var(--chart-5)" },
  FORMADO: { label: "Formado", color: "var(--chart-4)" },
};
const statusLabel = (status: string) => statusConhecidos[status]?.label ?? status;
const barrasConfig = { total: { label: "Novas matrículas", color: "var(--chart-1)" } } satisfies ChartConfig;

function SemRegistros({ titulo, descricao }: { titulo: string; descricao: string }) {
  return <Empty className="min-h-52"><EmptyHeader><EmptyTitle>{titulo}</EmptyTitle><EmptyDescription>{descricao}</EmptyDescription></EmptyHeader></Empty>;
}

function SituacaoAlunos({ dados }: { dados: Dashboard }) {
  const total = dados.totais.alunos;
  const status = dados.alunos_por_status.map((situacao, index) => ({
    ...situacao, chave: `status${index}`, label: statusLabel(situacao.status),
    fill: statusConhecidos[situacao.status]?.color ?? "var(--chart-3)",
  }));
  const config: ChartConfig = Object.fromEntries(status.map((situacao) => [
    situacao.chave, { label: situacao.label, color: situacao.fill },
  ]));
  return total === 0 ? <SemRegistros titulo="Nenhum aluno cadastrado" descricao="A distribuição aparecerá após o primeiro cadastro." /> : (
    <div className="flex flex-col gap-3">
      <ChartContainer config={config} className="mx-auto h-52 w-full max-w-64 aspect-auto" aria-label={`Situação dos ${numero(total)} alunos cadastrados`}>
        <PieChart accessibilityLayer>
          <ChartTooltip content={<ChartTooltipContent nameKey="chave" hideLabel formatter={(valor, _nome, item) => (
            <span>{statusLabel(String(item.payload.status))}: {numero(Number(valor))} ({percentual(Number(valor), total)})</span>
          )} />} />
          <Pie data={status} dataKey="total" nameKey="chave" innerRadius={67} outerRadius={88} paddingAngle={status.length > 1 ? 4 : 0} strokeWidth={0} startAngle={90} endAngle={-270} isAnimationActive={false}>
            <Label content={({ viewBox }) => {
              if (!viewBox || !("cx" in viewBox) || !("cy" in viewBox)) return null;
              return <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle" dominantBaseline="middle">
                <tspan x={viewBox.cx} y={Number(viewBox.cy) - 4} className="fill-foreground text-3xl font-semibold">{percentual(dados.totais.ativos, total)}</tspan>
                <tspan x={viewBox.cx} y={Number(viewBox.cy) + 22} className="fill-muted-foreground text-xs">alunos ativos</tspan>
              </text>;
            }} />
          </Pie>
        </PieChart>
      </ChartContainer>
      {status.map((situacao) => <div key={situacao.chave} className="flex items-center justify-between gap-3 text-sm">
        <span className="flex items-center gap-2 text-muted-foreground"><span className="size-2.5 shrink-0 rounded-full" style={{ background: situacao.fill }} />{situacao.label}</span>
        <span className="font-medium tabular-nums">{numero(situacao.total)} <span className="ml-1 text-xs font-normal text-muted-foreground">{percentual(situacao.total, total)}</span></span>
      </div>)}
    </div>
  );
}

function UltimosCadastros({ dados }: { dados: Dashboard }) {
  return dados.ultimos_cadastros.length === 0 ? <SemRegistros titulo="Nenhum cadastro recente" descricao="Os últimos alunos cadastrados serão exibidos aqui." /> : (
    <Table>
      <TableHeader><TableRow>
        <TableHead>Aluno</TableHead><TableHead className="hidden sm:table-cell">Matrícula</TableHead>
        <TableHead className="hidden xl:table-cell">Cadastrado em</TableHead><TableHead className="text-right">Situação</TableHead>
      </TableRow></TableHeader>
      <TableBody>{dados.ultimos_cadastros.map((aluno) => <TableRow key={aluno.id}>
        <TableCell><div className="flex items-center gap-3 py-1">
          <Avatar className="size-8 shrink-0"><AvatarFallback>{aluno.nome_completo.trim().split(/\s+/).filter(Boolean).slice(0, 2).map((nome) => nome[0]).join("")}</AvatarFallback></Avatar>
          <div className="flex flex-col gap-1"><span className="font-medium">{aluno.nome_completo}</span><span className="font-mono text-xs text-muted-foreground sm:hidden">{aluno.matricula}</span></div>
        </div></TableCell>
        <TableCell className="hidden font-mono text-xs text-muted-foreground sm:table-cell">{aluno.matricula}</TableCell>
        <TableCell className="hidden text-muted-foreground xl:table-cell">{dataLocal(aluno.criado_em, { day: "2-digit", month: "short", year: "numeric" })}</TableCell>
        <TableCell className="text-right"><Badge variant={aluno.status === "ATIVO" ? "outline" : "secondary"}>{statusLabel(aluno.status)}</Badge></TableCell>
      </TableRow>)}</TableBody>
    </Table>
  );
}

function DashboardInstitucional({ nome }: { nome: string }) {
  const [periodo, setPeriodo] = useState<PeriodoDashboard>("ano");
  const [atualizacao, setAtualizacao] = useState(0);
  const [dados, setDados] = useState<Dashboard | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(false);
  const [ultimaConsulta, setUltimaConsulta] = useState<string | null>(null);
  const [ano, setAno] = useState<number | null>(null);

  function consultar(proximoPeriodo: PeriodoDashboard = periodo) {
    setCarregando(true);
    setErro(false);
    setDados(null);
    setPeriodo(proximoPeriodo);
    setAtualizacao((valor) => valor + 1);
  }

  useEffect(() => {
    const controller = new AbortController();
    dashboardService.obter(periodo, controller.signal).then((resposta) => {
      if (controller.signal.aborted) return;
      setDados(resposta);
      setUltimaConsulta(resposta.gerado_em);
      setAno(resposta.ano);
    }).catch(() => {
      if (!controller.signal.aborted) setErro(true);
    }).finally(() => {
      if (!controller.signal.aborted) setCarregando(false);
    });
    return () => controller.abort();
  }, [periodo, atualizacao]);

  const legenda = dados ? `${mesLocal(dados.periodo.inicio.slice(0, 7))} a ${mesLocal(dados.periodo.fim.slice(0, 7))} · mês atual parcial` : "Inclui o mês atual, ainda parcial";
  const pico = dados?.matriculas_por_mes.reduce((maior, mes) => mes.total >= maior.total ? mes : maior);
  const metricas = [
    { label: "Total de alunos", valor: dados?.totais.alunos, detalhe: "Todos os cadastros da instituição", icon: Users },
    { label: "Alunos ativos", valor: dados?.totais.ativos, detalhe: dados ? `${percentual(dados.totais.ativos, dados.totais.alunos)} dos alunos cadastrados` : "", icon: UserCheck },
    { label: "Novas matrículas", valor: dados?.totais.novas_matriculas, detalhe: legenda, icon: UserPlus },
    { label: "Alunos inativos", valor: dados?.totais.inativos, detalhe: dados ? `${percentual(dados.totais.inativos, dados.totais.alunos)} dos alunos cadastrados` : "", icon: UserX },
  ];

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
          {dados && <Badge variant="outline"><CalendarDays data-icon="inline-start" />{dados.ano}.{dados.semestre}</Badge>}
          <Button variant="outline" nativeButton={false} render={<Link to="/alunos" />}>Gerenciar alunos<ArrowRight data-icon="inline-end" /></Button>
        </PageHeaderActions>
      </PageHeader>
    <div className="flex flex-wrap items-center justify-between gap-3">
      <Typography variant="muted" className="text-xs" aria-live="polite">
        {ultimaConsulta ? `Última consulta: ${dataLocal(ultimaConsulta, { dateStyle: "short", timeStyle: "medium" })}` : "Aguardando a primeira consulta"}
      </Typography>
      <Button variant="outline" size="sm" disabled={carregando} onClick={() => consultar()}><RefreshCw data-icon="inline-start" className={carregando ? "animate-spin" : undefined} />Atualizar</Button>
    </div>
    {erro ? <Alert variant="destructive"><AlertCircle /><AlertTitle>Não foi possível carregar o dashboard</AlertTitle><AlertDescription className="flex flex-col items-start gap-3">Verifique a conexão e tente consultar os dados novamente.<Button variant="outline" size="sm" onClick={() => consultar()}>Tentar novamente</Button></AlertDescription></Alert> : <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-busy={carregando} aria-label="Indicadores da instituição">
        {metricas.map((metrica) => <Card key={metrica.label}>
          <CardHeader><CardDescription>{metrica.label}</CardDescription><CardAction><metrica.icon className="size-4 text-muted-foreground" /></CardAction></CardHeader>
          <CardContent className="flex flex-col gap-2">
            {carregando ? <><Skeleton className="h-9 w-24" /><Skeleton className="h-4 w-40 max-w-full" /></> : metrica.valor !== undefined && <><Typography variant="h2" className="text-3xl tabular-nums">{numero(metrica.valor)}</Typography><Typography variant="muted" className="text-xs">{metrica.detalhe}</Typography></>}
          </CardContent>
        </Card>)}
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
        <Card className="min-w-0">
          <CardHeader className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex flex-col gap-1"><CardTitle>Novas matrículas</CardTitle><CardDescription>{legenda}</CardDescription></div>
            <ToggleGroup aria-label="Período das novas matrículas" variant="outline" size="sm" spacing={0} value={[periodo]} onValueChange={(value) => {
              const proximo = value[0];
              if (proximo === "3" || proximo === "6" || proximo === "ano") consultar(proximo);
            }}>
              <ToggleGroupItem value="3" aria-label="Últimos 3 meses">3 meses</ToggleGroupItem>
              <ToggleGroupItem value="6" aria-label="Últimos 6 meses">6 meses</ToggleGroupItem>
              <ToggleGroupItem value="ano" aria-label={ano ? `Ano de ${ano}` : "Ano atual"}>{ano ?? "Ano atual"}</ToggleGroupItem>
            </ToggleGroup>
          </CardHeader>
          <CardContent aria-busy={carregando}>
            {carregando ? <Skeleton className="h-64 w-full" /> : dados && (dados.totais.novas_matriculas === 0 ? <SemRegistros titulo="Nenhuma matrícula no período" descricao="Escolha outro período ou aguarde novos cadastros." /> : (
              <ChartContainer config={barrasConfig} className="h-64 w-full aspect-auto" aria-label={`Novas matrículas por mês. ${legenda}`}>
                <BarChart accessibilityLayer data={dados.matriculas_por_mes} margin={{ top: 16, right: 8, bottom: 6, left: 0 }} barSize={32}>
                  <CartesianGrid vertical={false} strokeDasharray="3 5" />
                  <XAxis dataKey="mes" tickLine={false} axisLine={false} tickMargin={12} tickFormatter={(mes: string) => mesLocal(mes, true).split(" de ")[0]} />
                  <YAxis tickLine={false} axisLine={false} width={40} tickMargin={8} allowDecimals={false} tickFormatter={numero} />
                  <ChartTooltip cursor={false} content={<ChartTooltipContent labelFormatter={(mes) => `${mesLocal(String(mes))}${String(mes) === dados.matriculas_por_mes.at(-1)?.mes ? " · parcial" : ""}`} formatter={(valor) => <span>Novas matrículas: {numero(Number(valor))}</span>} />} />
                  <Bar dataKey="total" fill="var(--color-total)" radius={[5, 5, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ChartContainer>
            ))}
          </CardContent>
          <CardFooter className="gap-2"><TrendingUp className="size-4 shrink-0 text-primary" />{carregando ? <Skeleton className="h-4 w-64 max-w-full" /> : <span className="text-xs text-muted-foreground">{pico && pico.total > 0 ? `${mesLocal(pico.mes)} lidera o período, com ${numero(pico.total)} novos cadastros${pico.parcial ? " até o momento" : ""}.` : "Nenhum novo cadastro no período selecionado."}</span>}</CardFooter>
        </Card>
        <Card className="min-w-0"><CardHeader><CardTitle>Situação dos alunos</CardTitle><CardDescription>Distribuição atual da instituição</CardDescription></CardHeader><CardContent aria-busy={carregando}>{carregando ? <Skeleton className="mx-auto h-52 w-52 rounded-full" /> : dados && <SituacaoAlunos dados={dados} />}</CardContent></Card>
      </div>
      <Card className="min-w-0">
        <CardHeader><CardTitle>Últimos cadastros</CardTitle><CardDescription>Alunos adicionados recentemente</CardDescription><CardAction>{dados && <Badge variant="outline">{dados.ultimos_cadastros.length} recentes</Badge>}</CardAction></CardHeader>
        <CardContent aria-busy={carregando}>{carregando ? <div className="flex flex-col gap-4">{Array.from({ length: 4 }, (_, index) => <Skeleton key={index} className="h-10 w-full" />)}</div> : dados && <UltimosCadastros dados={dados} />}</CardContent>
      </Card>
    </>}
    </PageContainer>
  );
}

export function OverviewPage() {
  const { user } = useAuth();
  if (!user) return null;
  if (user.perfil === "ADMIN" || user.perfil === "SECRETARIA") return <DashboardInstitucional key={user.id} nome={user.nome} />;
  return (
    <PageContainer>
      <Card>
        <CardHeader>
          <CardTitle><Typography variant="h2">Olá, {user.nome}!</Typography></CardTitle>
          <CardDescription>Bem-vindo ao GL4 SGA-EDU. Seu perfil atual é: <strong>{user.perfil}</strong>.</CardDescription>
        </CardHeader>
      </Card>
    </PageContainer>
  );
}
