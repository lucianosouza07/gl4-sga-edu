import React from "react";
import { useAuth } from "@/features/auth";
import { useAlunos } from "../hooks/use-alunos";
import { TabelaAlunos } from "../components/tabela-alunos";
import { ModalCadastroAluno } from "../components/modal-cadastro-aluno";
import { ModalInativarAluno } from "../components/modal-inativar-aluno";
import { TabelaPaginacao } from "@/components/shared/tabela-paginacao";
import {
  PageContainer,
  PageHeader,
  PageHeaderContent,
  PageHeaderTitle,
  PageHeaderDescription,
  PageHeaderActions,
} from "@/components/shared/page-header";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UserPlus, Search, RefreshCw, Users, UserCheck, UserX, GraduationCap } from "lucide-react";

export const AlunosView: React.FC = () => {
  const { user } = useAuth();
  const {
    alunos,
    carregando,
    busca,
    setBusca,
    apenasAtivos,
    setApenasAtivos,
    pagina,
    setPagina,
    tamanho,
    total,
    totalPaginas,
    handleTamanhoChange,
    modalCadastroAberto,
    setModalCadastroAberto,
    alunoParaInativar,
    setAlunoParaInativar,
    reativandoId,
    carregarAlunos,
    handleReativar,
  } = useAlunos();

  const podeGerenciar = user?.perfil === "ADMIN" || user?.perfil === "SECRETARIA";
  const totalAtivos = alunos.filter((a) => a.status === "ATIVO").length;
  const totalInativos = alunos.filter((a) => a.status === "INATIVO").length;

  return (
    <PageContainer>
      {/* Cabeçalho Padronizado da Página */}
      <PageHeader>
        <PageHeaderContent>
          <PageHeaderTitle>Gestão de Alunos</PageHeaderTitle>
          <PageHeaderDescription>
            Cadastre, consulte e gerencie as matrículas e dados acadêmicos.
          </PageHeaderDescription>
        </PageHeaderContent>
        {podeGerenciar && (
          <PageHeaderActions>
            <Button onClick={() => setModalCadastroAberto(true)} className="shrink-0 shadow-xs gap-2">
              <UserPlus className="h-4 w-4" />
              <span>Novo Aluno</span>
            </Button>
          </PageHeaderActions>
        )}
      </PageHeader>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="shadow-2xs border-border/80">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <Typography variant="muted" className="text-xs font-medium">
              Total Encontrados
            </Typography>
            <Badge variant="outline" className="text-[11px] font-mono">Geral</Badge>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline justify-between">
              <Typography variant="h2" className="text-2xl font-semibold tabular-nums">
                {carregando ? "..." : total}
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

      {/* Tabela + Paginação */}
      <div className="overflow-hidden rounded-xl border bg-card shadow-xs min-w-0 w-full">
        <TabelaAlunos
          alunos={alunos}
          carregando={carregando}
          onSolicitarInativacao={(aluno) => setAlunoParaInativar(aluno)}
          onReativar={handleReativar}
          reativandoId={reativandoId}
          podeGerenciar={podeGerenciar}
        />

        {!carregando && total > 0 && (
          <div className="px-4 pb-4">
            <TabelaPaginacao
              pagina={pagina}
              totalPaginas={totalPaginas}
              total={total}
              tamanho={tamanho}
              onPaginaChange={setPagina}
              onTamanhoChange={handleTamanhoChange}
              desabilitado={carregando}
            />
          </div>
        )}
      </div>

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
    </PageContainer>
  );
};

export default AlunosView;
