import React from "react";
import type { Dashboard } from "../data/dashboard.types";
import { Users, UserCheck, UserPlus, UserX } from "lucide-react";
import { Card, CardHeader, CardDescription, CardAction, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Typography } from "@/components/ui/typography";

interface DashboardKpisProps {
  dados: Dashboard | null;
  carregando: boolean;
  legendaNovasMatriculas: string;
}

const numero = (valor: number) => valor.toLocaleString("pt-BR");
const percentual = (valor: number, total: number) =>
  (total === 0 ? 0 : valor / total).toLocaleString("pt-BR", { style: "percent", maximumFractionDigits: 1 });

export const DashboardKpis: React.FC<DashboardKpisProps> = ({
  dados,
  carregando,
  legendaNovasMatriculas,
}) => {
  const metricas = [
    {
      label: "Total de alunos",
      valor: dados?.totais.alunos,
      detalhe: "Todos os cadastros da instituição",
      icon: Users,
    },
    {
      label: "Alunos ativos",
      valor: dados?.totais.ativos,
      detalhe: dados ? `${percentual(dados.totais.ativos, dados.totais.alunos)} dos alunos cadastrados` : "",
      icon: UserCheck,
    },
    {
      label: "Novas matrículas",
      valor: dados?.totais.novas_matriculas,
      detalhe: legendaNovasMatriculas,
      icon: UserPlus,
    },
    {
      label: "Alunos inativos",
      valor: dados?.totais.inativos,
      detalhe: dados ? `${percentual(dados.totais.inativos, dados.totais.alunos)} dos alunos cadastrados` : "",
      icon: UserX,
    },
  ];

  return (
    <div
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      aria-busy={carregando}
      aria-label="Indicadores da instituição"
    >
      {metricas.map((metrica) => (
        <Card key={metrica.label}>
          <CardHeader>
            <CardDescription>{metrica.label}</CardDescription>
            <CardAction>
              <metrica.icon className="size-4 text-muted-foreground" />
            </CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {carregando ? (
              <>
                <Skeleton className="h-9 w-24" />
                <Skeleton className="h-4 w-40 max-w-full" />
              </>
            ) : (
              metrica.valor !== undefined && (
                <>
                  <Typography variant="h2" className="text-3xl tabular-nums">
                    {numero(metrica.valor)}
                  </Typography>
                  <Typography variant="muted" className="text-xs">
                    {metrica.detalhe}
                  </Typography>
                </>
              )
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
