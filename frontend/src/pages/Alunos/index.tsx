import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { alunosService } from "@/services/alunosService";
import type { Aluno } from "@/types/aluno";
import { TabelaAlunos } from "./components/TabelaAlunos";
import { ModalCadastroAluno } from "./components/ModalCadastroAluno";
import { ModalInativarAluno } from "./components/ModalInativarAluno";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UserPlus, Search, RefreshCw, Users, UserCheck, UserX, GraduationCap } from "lucide-react";
import { toast } from "sonner";

export const AlunosPage: React.FC = () => {
  const { user } = useAuth();
  const [alunos, setAlunos] = useState<Aluno[]>([]);
  const [carregando, setCarregando] = useState<boolean>(true);
  const [busca, setBusca] = useState<string>("");
  const [apenasAtivos, setApenasAtivos] = useState<boolean>(true);

  // Modais
  const [modalCadastroAberto, setModalCadastroAberto] = useState<boolean>(false);
  const [alunoParaInativar, setAlunoParaInativar] = useState<Aluno | null>(null);

  const podeGerenciar = user?.perfil === "ADMIN" || user?.perfil === "SECRETARIA";

  const carregarAlunos = useCallback(async () => {
    setCarregando(true);
    try {
      const dados = await alunosService.listar({
        busca: busca.trim() || undefined,
        apenas_ativos: apenasAtivos,
      });
      setAlunos(dados);
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Erro ao carregar lista de alunos.";
      toast.error(msg);
    } finally {
      setCarregando(false);
    }
  }, [busca, apenasAtivos]);

  useEffect(() => {
    // Debounce simples para a busca por texto
    const timer = setTimeout(() => {
      carregarAlunos();
    }, 300);
    return () => clearTimeout(timer);
  }, [carregarAlunos]);

  const totalAtivos = alunos.filter((a) => a.status === "ATIVO").length;
  const totalInativos = alunos.filter((a) => a.status === "INATIVO").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Cabeçalho da Página */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Typography variant="h2" className="text-2xl font-bold tracking-tight text-foreground">
            Gestão de Alunos
          </Typography>
          <Typography variant="muted" className="text-sm mt-0.5">
            Cadastre, consulte e gerencie as matrículas e dados acadêmicos.
          </Typography>
        </div>
        {podeGerenciar && (
          <Button onClick={() => setModalCadastroAberto(true)} className="shrink-0 shadow-xs gap-2">
            <UserPlus className="h-4 w-4" />
            <span>Novo Aluno</span>
          </Button>
        )}
      </div>

      {/* Cards de Resumo Estilo Meridian */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="shadow-2xs border-border/80">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <Typography variant="muted" className="text-xs font-medium">
              Total na Busca
            </Typography>
            <Badge variant="outline" className="text-[11px] font-mono">Geral</Badge>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline justify-between">
              <Typography variant="h2" className="text-2xl font-semibold tabular-nums">
                {carregando ? "..." : alunos.length}
              </Typography>
              <Users className="h-4 w-4 text-muted-foreground/60" />
            </div>
            <Typography variant="muted" className="text-xs mt-1">
              Registros correspondentes
            </Typography>
          </CardContent>
        </Card>

        <Card className="shadow-2xs border-border/80">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <Typography variant="muted" className="text-xs font-medium">
              Alunos Ativos
            </Typography>
            <Badge variant="default" className="text-[11px] bg-emerald-600/15 text-emerald-700 dark:text-emerald-400 border-emerald-600/20">
              Ativos
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline justify-between">
              <Typography variant="h2" className="text-2xl font-semibold tabular-nums">
                {carregando ? "..." : totalAtivos}
              </Typography>
              <UserCheck className="h-4 w-4 text-emerald-600/70" />
            </div>
            <Typography variant="muted" className="text-xs mt-1">
              Matrículas regulares
            </Typography>
          </CardContent>
        </Card>

        <Card className="shadow-2xs border-border/80">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <Typography variant="muted" className="text-xs font-medium">
              Inativos / Trancados
            </Typography>
            <Badge variant="secondary" className="text-[11px]">Inativos</Badge>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline justify-between">
              <Typography variant="h2" className="text-2xl font-semibold tabular-nums">
                {carregando ? "..." : totalInativos}
              </Typography>
              <UserX className="h-4 w-4 text-muted-foreground/60" />
            </div>
            <Typography variant="muted" className="text-xs mt-1">
              Acesso bloqueado
            </Typography>
          </CardContent>
        </Card>

        <Card className="shadow-2xs border-border/80">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <Typography variant="muted" className="text-xs font-medium">
              Semestre Vigente
            </Typography>
            <Badge variant="outline" className="text-[11px] font-mono">2026.1</Badge>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline justify-between">
              <Typography variant="h2" className="text-2xl font-semibold tabular-nums">
                1º Sem
              </Typography>
              <GraduationCap className="h-4 w-4 text-primary/70" />
            </div>
            <Typography variant="muted" className="text-xs mt-1">
              Ano Letivo 2026
            </Typography>
          </CardContent>
        </Card>
      </div>

      {/* Barra de Filtros e Busca */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-4 rounded-xl border bg-card shadow-xs">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nome ou matrícula..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="apenas-ativos"
              checked={apenasAtivos}
              onCheckedChange={(checked) => setApenasAtivos(!!checked)}
            />
            <Label htmlFor="apenas-ativos" className="text-sm cursor-pointer select-none">
              Apenas alunos ativos
            </Label>
          </div>

          <Button
            variant="outline"
            size="icon"
            onClick={carregarAlunos}
            disabled={carregando}
            title="Atualizar lista"
          >
            <RefreshCw className={`h-4 w-4 ${carregando ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Tabela de Alunos */}
      <TabelaAlunos
        alunos={alunos}
        carregando={carregando}
        onSolicitarInativacao={(aluno) => setAlunoParaInativar(aluno)}
        podeGerenciar={podeGerenciar}
      />

      {/* Modais */}
      <ModalCadastroAluno
        aberto={modalCadastroAberto}
        onOpenChange={setModalCadastroAberto}
        onSucesso={carregarAlunos}
      />

      <ModalInativarAluno
        aluno={alunoParaInativar}
        aberto={!!alunoParaInativar}
        onOpenChange={(aberto) => !aberto && setAlunoParaInativar(null)}
        onSucesso={carregarAlunos}
      />
    </div>
  );
};
