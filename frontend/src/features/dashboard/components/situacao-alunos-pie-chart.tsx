import React from "react";
import { Label, Pie, PieChart } from "recharts";
import type { Dashboard } from "../data/dashboard.types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";

interface SituacaoAlunosPieChartProps {
  dados: Dashboard | null;
  carregando: boolean;
}

const numero = (valor: number) => valor.toLocaleString("pt-BR");
const percentual = (valor: number, total: number) =>
  (total === 0 ? 0 : valor / total).toLocaleString("pt-BR", { style: "percent", maximumFractionDigits: 1 });

const statusConhecidos: Record<string, { label: string; color: string }> = {
  ATIVO: { label: "Ativo", color: "var(--chart-1)" },
  INATIVO: { label: "Inativo", color: "var(--chart-2)" },
  TRANCADO: { label: "Trancado", color: "var(--chart-5)" },
  FORMADO: { label: "Formado", color: "var(--chart-4)" },
};
const statusLabel = (status: string) => statusConhecidos[status]?.label ?? status;

export const SituacaoAlunosPieChart: React.FC<SituacaoAlunosPieChartProps> = ({
  dados,
  carregando,
}) => {
  const total = dados?.totais.alunos ?? 0;
  const status =
    dados?.alunos_por_status.map((situacao, index) => ({
      ...situacao,
      chave: `status${index}`,
      label: statusLabel(situacao.status),
      fill: statusConhecidos[situacao.status]?.color ?? "var(--chart-3)",
    })) ?? [];

  const config: ChartConfig = Object.fromEntries(
    status.map((situacao) => [situacao.chave, { label: situacao.label, color: situacao.fill }])
  );

  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle>Situação dos alunos</CardTitle>
        <CardDescription>Distribuição atual da instituição</CardDescription>
      </CardHeader>
      <CardContent aria-busy={carregando}>
        {carregando ? (
          <Skeleton className="mx-auto h-52 w-52 rounded-full" />
        ) : total === 0 ? (
          <Empty className="min-h-52">
            <EmptyHeader>
              <EmptyTitle>Nenhum aluno cadastrado</EmptyTitle>
              <EmptyDescription>A distribuição aparecerá após o primeiro cadastro.</EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          <div className="flex flex-col gap-3">
            <ChartContainer
              config={config}
              className="mx-auto h-52 w-full max-w-64 aspect-auto"
              aria-label={`Situação dos ${numero(total)} alunos cadastrados`}
            >
              <PieChart accessibilityLayer>
                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      nameKey="chave"
                      hideLabel
                      formatter={(valor, _nome, item) => (
                        <span>
                          {statusLabel(String(item.payload.status))}: {numero(Number(valor))} (
                          {percentual(Number(valor), total)})
                        </span>
                      )}
                    />
                  }
                />
                <Pie
                  data={status}
                  dataKey="total"
                  nameKey="chave"
                  innerRadius={67}
                  outerRadius={88}
                  paddingAngle={status.length > 1 ? 4 : 0}
                  strokeWidth={0}
                  startAngle={90}
                  endAngle={-270}
                  isAnimationActive={false}
                >
                  <Label
                    content={({ viewBox }) => {
                      if (!viewBox || !("cx" in viewBox) || !("cy" in viewBox)) return null;
                      return (
                        <text
                          x={viewBox.cx}
                          y={viewBox.cy}
                          textAnchor="middle"
                          dominantBaseline="middle"
                        >
                          <tspan
                            x={viewBox.cx}
                            y={Number(viewBox.cy) - 4}
                            className="fill-foreground text-3xl font-semibold"
                          >
                            {percentual(dados?.totais.ativos ?? 0, total)}
                          </tspan>
                          <tspan
                            x={viewBox.cx}
                            y={Number(viewBox.cy) + 22}
                            className="fill-muted-foreground text-xs"
                          >
                            alunos ativos
                          </tspan>
                        </text>
                      );
                    }}
                  />
                </Pie>
              </PieChart>
            </ChartContainer>
            {status.map((situacao) => (
              <div key={situacao.chave} className="flex items-center justify-between gap-3 text-sm">
                <span className="flex items-center gap-2 text-muted-foreground">
                  <span className="size-2.5 shrink-0 rounded-full" style={{ background: situacao.fill }} />
                  {situacao.label}
                </span>
                <span className="font-medium tabular-nums">
                  {numero(situacao.total)}{" "}
                  <span className="ml-1 text-xs font-normal text-muted-foreground">
                    {percentual(situacao.total, total)}
                  </span>
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
