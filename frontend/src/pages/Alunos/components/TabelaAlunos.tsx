import React from "react";
import type { Aluno } from "@/types/aluno";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { Skeleton } from "@/components/ui/skeleton";
import { UserX, Calendar, Phone, Mail, CheckCircle, XCircle, GraduationCap } from "lucide-react";

interface TabelaAlunosProps {
  alunos: Aluno[];
  carregando: boolean;
  onSolicitarInativacao: (aluno: Aluno) => void;
  podeGerenciar: boolean;
}

export const TabelaAlunos: React.FC<TabelaAlunosProps> = ({
  alunos,
  carregando,
  onSolicitarInativacao,
  podeGerenciar,
}) => {
  if (carregando) {
    return (
      <div className="space-y-3 p-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-12 w-full rounded-md" />
        ))}
      </div>
    );
  }

  if (alunos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center border rounded-xl bg-card shadow-2xs">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-muted/80 text-muted-foreground mb-4 shadow-2xs">
          <GraduationCap className="size-7" />
        </div>
        <Typography variant="h4" className="font-semibold text-foreground">
          Nenhum aluno cadastrado
        </Typography>
        <Typography variant="muted" className="mt-1.5 max-w-sm text-sm">
          Comece adicionando novos alunos à instituição para gerenciar matrículas, turmas e frequências.
        </Typography>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border bg-card shadow-xs">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead className="w-[120px]">
              <Typography variant="small" className="font-semibold">
                Matrícula
              </Typography>
            </TableHead>
            <TableHead>
              <Typography variant="small" className="font-semibold">
                Nome Completo
              </Typography>
            </TableHead>
            <TableHead className="w-[140px]">
              <Typography variant="small" className="font-semibold">
                CPF
              </Typography>
            </TableHead>
            <TableHead>
              <Typography variant="small" className="font-semibold">
                Contato
              </Typography>
            </TableHead>
            <TableHead className="w-[130px]">
              <Typography variant="small" className="font-semibold">
                Nascimento
              </Typography>
            </TableHead>
            <TableHead className="w-[110px] text-center">
              <Typography variant="small" className="font-semibold">
                Status
              </Typography>
            </TableHead>
            {podeGerenciar && (
              <TableHead className="w-[100px] text-right">
                <Typography variant="small" className="font-semibold">
                  Ações
                </Typography>
              </TableHead>
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {alunos.map((aluno) => {
            const isAtivo = aluno.status === "ATIVO";
            return (
              <TableRow key={aluno.id} className="hover:bg-muted/30 transition-colors">
                <TableCell className="font-mono text-xs font-semibold">
                  {aluno.matricula}
                </TableCell>
                <TableCell>
                  <Typography variant="small" className="font-medium text-foreground">
                    {aluno.nome_completo}
                  </Typography>
                </TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {aluno.cpf}
                </TableCell>
                <TableCell>
                  <div className="flex flex-col gap-0.5 text-xs">
                    <span className="flex items-center gap-1.5 text-muted-foreground">
                      <Mail className="h-3 w-3 shrink-0" />
                      {aluno.email}
                    </span>
                    {aluno.telefone && (
                      <span className="flex items-center gap-1.5 text-muted-foreground">
                        <Phone className="h-3 w-3 shrink-0" />
                        {aluno.telefone}
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3 shrink-0" />
                    {aluno.data_nascimento}
                  </span>
                </TableCell>
                <TableCell className="text-center">
                  <Badge
                    variant={isAtivo ? "default" : "secondary"}
                    className={
                      isAtivo
                        ? "bg-emerald-600/10 text-emerald-700 dark:text-emerald-400 border-emerald-600/20"
                        : "bg-destructive/10 text-destructive border-destructive/20"
                    }
                  >
                    {isAtivo ? (
                      <CheckCircle className="mr-1 h-3 w-3" />
                    ) : (
                      <XCircle className="mr-1 h-3 w-3" />
                    )}
                    {aluno.status}
                  </Badge>
                </TableCell>
                {podeGerenciar && (
                  <TableCell className="text-right">
                    {isAtivo && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                        title="Inativar Aluno"
                        onClick={() => onSolicitarInativacao(aluno)}
                      >
                        <UserX className="h-4 w-4 mr-1" />
                        <span className="text-xs">Inativar</span>
                      </Button>
                    )}
                  </TableCell>
                )}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
};
