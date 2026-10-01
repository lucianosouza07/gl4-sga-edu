import React from "react";
import type { Dashboard } from "../data/dashboard.types";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription, CardAction, CardContent } from "@/components/ui/card";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface UltimosCadastrosTableProps {
  dados: Dashboard | null;
  carregando: boolean;
}

const dataLocal = (instante: string, options: Intl.DateTimeFormatOptions) =>
  new Date(instante).toLocaleString("pt-BR", { ...options, timeZone: "America/Bahia" });

const statusConhecidos: Record<string, { label: string; color: string }> = {
  ATIVO: { label: "Ativo", color: "var(--chart-1)" },
  INATIVO: { label: "Inativo", color: "var(--chart-2)" },
  TRANCADO: { label: "Trancado", color: "var(--chart-5)" },
  FORMADO: { label: "Formado", color: "var(--chart-4)" },
};
const statusLabel = (status: string) => statusConhecidos[status]?.label ?? status;

export const UltimosCadastrosTable: React.FC<UltimosCadastrosTableProps> = ({
  dados,
  carregando,
}) => {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle>Últimos cadastros</CardTitle>
        <CardDescription>Alunos adicionados recentemente</CardDescription>
        <CardAction>
          {dados && <Badge variant="outline">{dados.ultimos_cadastros.length} recentes</Badge>}
        </CardAction>
      </CardHeader>
      <CardContent aria-busy={carregando}>
        {carregando ? (
          <div className="flex flex-col gap-4">
            {Array.from({ length: 4 }, (_, index) => (
              <Skeleton key={index} className="h-10 w-full" />
            ))}
          </div>
        ) : dados && dados.ultimos_cadastros.length === 0 ? (
          <Empty className="min-h-52">
            <EmptyHeader>
              <EmptyTitle>Nenhum cadastro recente</EmptyTitle>
              <EmptyDescription>Os últimos alunos cadastrados serão exibidos aqui.</EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          dados && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Aluno</TableHead>
                  <TableHead className="hidden sm:table-cell">Matrícula</TableHead>
                  <TableHead className="hidden xl:table-cell">Cadastrado em</TableHead>
                  <TableHead className="text-right">Situação</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dados.ultimos_cadastros.map((aluno) => (
                  <TableRow key={aluno.id}>
                    <TableCell>
                      <div className="flex items-center gap-3 py-1">
                        <Avatar className="size-8 shrink-0">
                          <AvatarFallback>
                            {aluno.nome_completo
                              .trim()
                              .split(/\s+/)
                              .filter(Boolean)
                              .slice(0, 2)
                              .map((nome) => nome[0])
                              .join("")}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col gap-1">
                          <span className="font-medium">{aluno.nome_completo}</span>
                          <span className="font-mono text-xs text-muted-foreground sm:hidden">
                            {aluno.matricula}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="hidden font-mono text-xs text-muted-foreground sm:table-cell">
                      {aluno.matricula}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground xl:table-cell">
                      {dataLocal(aluno.criado_em, {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant={aluno.status === "ATIVO" ? "outline" : "secondary"}>
                        {statusLabel(aluno.status)}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )
        )}
      </CardContent>
    </Card>
  );
};
