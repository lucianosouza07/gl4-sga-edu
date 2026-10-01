import { useState } from "react";
import {
  GraduationCap,
  Sparkles,
  CheckCircle2,
  Moon,
  Sun,
  Search,
  UserPlus,
  ShieldCheck,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

function App() {
  const [isDark, setIsDark] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [testCount, setTestCount] = useState(0);

  const toggleDarkMode = () => {
    setIsDark(!isDark);
    if (!isDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-200">
      {/* Navbar Superior */}
      <header className="border-b border-border bg-card/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shadow-sm">
              <GraduationCap className="size-6" />
            </div>
            <div>
              <h1 className="text-base font-semibold leading-tight tracking-tight">
                GL4 SGA-EDU
              </h1>
              <p className="text-xs text-muted-foreground">
                Sistema de Gestão Acadêmica
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="gap-1 font-mono text-[11px]">
              <Sparkles className="size-3" /> Tema Meridian
            </Badge>

            {/* Alternador de Modo Claro / Escuro */}
            <Tooltip>
              <TooltipTrigger render={
                <Button
                  variant="outline"
                  size="icon"
                  onClick={toggleDarkMode}
                  className="rounded-full"
                  aria-label="Alternar tema"
                >
                  {isDark ? <Sun className="size-4" /> : <Moon className="size-4 text-primary" />}
                </Button>
              } />
              <TooltipContent>
                {isDark ? "Mudar para modo Claro" : "Mudar para modo Escuro"}
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </header>

      {/* Conteúdo Principal */}
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        {/* Banner de Sucesso */}
        <section className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="default" className="gap-1">
                <CheckCircle2 className="size-3.5" /> Etapa 1 Concluída
              </Badge>
              <span className="text-xs text-muted-foreground font-mono">
                Tailwind v4 + shadcn/ui
              </span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight">
              Ambiente de Desenvolvimento Operacional!
            </h2>
            <p className="text-sm text-muted-foreground">
              Os componentes do shadcn e as variáveis oklch do tema Meridian estão carregados e prontos para a construção do módulo de Alunos.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Modal Dialog de Teste */}
            <Dialog>
              <DialogTrigger render={
                <Button variant="default" className="gap-2 shadow-sm">
                  <UserPlus className="size-4" /> Testar Modal (Dialog)
                </Button>
              } />
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <ShieldCheck className="size-5 text-primary" />
                    Teste de Modal com shadcn
                  </DialogTitle>
                  <DialogDescription>
                    Este é um modal de exemplo para validar a renderização de Popups, Backdrops e formulários no projeto.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="nome-aluno">Nome do Aluno</Label>
                    <Input id="nome-aluno" placeholder="Ex: Gabriele Souza" />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="matricula-aluno">Matrícula</Label>
                    <Input id="matricula-aluno" placeholder="Ex: 20261001" />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <DialogClose render={
                    <Button variant="outline">Fechar</Button>
                  } />
                  <Button variant="default" onClick={() => alert("Formulário validado com sucesso!")}>
                    Confirmar
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </section>

        {/* Grade de Cards com Componentes */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Botões e Variantes */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="size-4 text-primary" /> Variantes de Botão
              </CardTitle>
              <CardDescription>
                Testando as cores primárias, secundárias e destrutivas do tema.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Button variant="default" size="sm">Primary</Button>
                <Button variant="secondary" size="sm">Secondary</Button>
                <Button variant="outline" size="sm">Outline</Button>
                <Button variant="destructive" size="sm">Destructive</Button>
              </div>
              <div className="pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => setTestCount(testCount + 1)}
                >
                  Contador Interativo: {testCount} cliques
                </Button>
              </div>
            </CardContent>
            <CardFooter className="text-xs text-muted-foreground border-t border-border/50 pt-3">
              Totalmente reativo e integrado ao tema.
            </CardFooter>
          </Card>

          {/* Card 2: Formulários e Inputs */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="size-4 text-primary" /> Inputs e Labels
              </CardTitle>
              <CardDescription>
                Campos com foco acessível e indicação de visual do tema.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="search-input">Buscar Aluno ou Matrícula</Label>
                <div className="relative">
                  <Input
                    id="search-input"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Digite para testar..."
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Digitado: <span className="font-mono text-foreground">{searchTerm || "(vazio)"}</span>
              </p>
            </CardContent>
            <CardFooter className="text-xs text-muted-foreground border-t border-border/50 pt-3">
              Pronto para os filtros de listagem.
            </CardFooter>
          </Card>

          {/* Card 3: Badges e Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="size-4 text-primary" /> Status e Badges
              </CardTitle>
              <CardDescription>
                Indicadores visuais de estado para os alunos.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge variant="default">Ativo</Badge>
                <Badge variant="secondary">Matriculado</Badge>
                <Badge variant="outline">Trancado</Badge>
                <Badge variant="destructive">Inativo</Badge>
              </div>
              <div className="text-xs text-muted-foreground pt-1">
                Suporta diferentes estilos e estados de acordo com a regra de negócio do SGA.
              </div>
            </CardContent>
            <CardFooter className="text-xs text-muted-foreground border-t border-border/50 pt-3">
              Paleta oklch balanceada para alta legibilidade.
            </CardFooter>
          </Card>
        </section>
      </main>
    </div>
  );
}

export default App;
