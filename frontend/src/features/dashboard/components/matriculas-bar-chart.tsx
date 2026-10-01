import React from "react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { TrendingUp } from "lucide-react";
import type { Dashboard, PeriodoDashboard } from "../data/dashboard.types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

interface MatriculasBarChartProps {
  dados: Dashboard | null;
  carregando: boolean;
  periodo: PeriodoDashboard;
  ano: number | null;
  legenda: string;
  onPeriodoChange: (periodo: PeriodoDashboard) => void;
}

const numero = (valor: number) => valor.toLocaleString("pt-BR");
const dataLocal = (instante: string, options: Intl.DateTimeFormatOptions) =>
  new Date(instante).toLocaleString("pt-BR", { ...options, timeZone: "America/Bahia" });
const mesLocal = (mes: string, abreviado = false) =>
  dataLocal(`${mes}-01T12:00:00Z`, { month: abreviado ? "short" : "long", year: "numeric" });

const barrasConfig = {
  total: { label: "Novas matrículas", color: "var(--chart-1)" },
} satisfies ChartConfig;

export const MatriculasBarChart: React.FC<MatriculasBarChartProps> = ({
  dados,
  carregando,
  periodo,
  ano,
  legenda,
  onPeriodoChange,
}) => {
  const pico = dados?.matriculas_por_mes.reduce(
    (maior, mes) => (mes.total >= maior.total ? mes : maior),
    dados.matriculas_por_mes[0]
  );

  return (
    <Card className="min-w-0">
      <CardHeader className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <CardTitle>Novas matrículas</CardTitle>
          <CardDescription>{legenda}</CardDescription>
        </div>
        <ToggleGroup
          aria-label="Período das novas matrículas"
          variant="outline"
          size="sm"
          spacing={0}
          value={[periodo]}
          onValueChange={(value) => {
            const proximo = value[0];
            if (proximo === "3" || proximo === "6" || proximo === "ano") {
              onPeriodoChange(proximo);
            }
          }}
        >
          <ToggleGroupItem value="3" aria-label="Últimos 3 meses">
            3 meses
          </ToggleGroupItem>
          <ToggleGroupItem value="6" aria-label="Últimos 6 meses">
            6 meses
          </ToggleGroupItem>
          <ToggleGroupItem value="ano" aria-label={ano ? `Ano de ${ano}` : "Ano atual"}>
            {ano ?? "Ano atual"}
          </ToggleGroupItem>
        </ToggleGroup>
      </CardHeader>
      <CardContent aria-busy={carregando}>
        {carregando ? (
          <Skeleton className="h-64 w-full" />
        ) : dados && dados.totais.novas_matriculas === 0 ? (
          <Empty className="min-h-52">
            <EmptyHeader>
              <EmptyTitle>Nenhuma matrícula no período</EmptyTitle>
              <EmptyDescription>Escolha outro período ou aguarde novos cadastros.</EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          dados && (
            <ChartContainer
              config={barrasConfig}
              className="h-64 w-full aspect-auto"
              aria-label={`Novas matrículas por mês. ${legenda}`}
            >
              <BarChart
                accessibilityLayer
                data={dados.matriculas_por_mes}
                margin={{ top: 16, right: 8, bottom: 6, left: 0 }}
                barSize={32}
              >
                <CartesianGrid vertical={false} strokeDasharray="3 5" />
                <XAxis
                  dataKey="mes"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={12}
                  tickFormatter={(mes: string) => mesLocal(mes, true).split(" de ")[0]}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  width={40}
                  tickMargin={8}
                  allowDecimals={false}
                  tickFormatter={numero}
                />
                <ChartTooltip
                  cursor={false}
                  content={
                    <ChartTooltipContent
                      labelFormatter={(mes) =>
                        `${mesLocal(String(mes))}${
                          String(mes) === dados.matriculas_por_mes.at(-1)?.mes ? " · parcial" : ""
                        }`
                      }
                      formatter={(valor) => <span>Novas matrículas: {numero(Number(valor))}</span>}
                    />
                  }
                />
                <Bar dataKey="total" fill="var(--color-total)" radius={[5, 5, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ChartContainer>
          )
        )}
      </CardContent>
      <CardFooter className="gap-2">
        <TrendingUp className="size-4 shrink-0 text-primary" />
        {carregando ? (
          <Skeleton className="h-4 w-64 max-w-full" />
        ) : (
          <span className="text-xs text-muted-foreground">
            {pico && pico.total > 0
              ? `${mesLocal(pico.mes)} lidera o período, com ${numero(pico.total)} novos cadastros${
                  pico.parcial ? " até o momento" : ""
                }.`
              : "Nenhum novo cadastro no período selecionado."}
          </span>
        )}
      </CardFooter>
    </Card>
  );
};
