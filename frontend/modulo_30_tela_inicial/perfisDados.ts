/**
 * perfisDados.ts — Definições de Perfis e Dados dos Dashboards (SPEC.md / prototipo v3)
 * Módulo: modulo_30_tela_inicial
 */

export type PerfilId = "discente" | "docente" | "colegiado" | "ti_suporte" | "financeiro";

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  active?: boolean;
}

export interface KpiCardData {
  label: string;
  value: string;
  colorClass: "kpi-green" | "kpi-yellow" | "kpi-purple" | "kpi-pink";
  icon: string;
}

export interface PerfilConfig {
  id: PerfilId;
  label: string;
  name: string;
  role: string;
  avatarText: string;
  title: string;
  subtitle: string;
  navItems: NavItem[];
  kpis: KpiCardData[];
}

export const PERFIS: Record<PerfilId, PerfilConfig> = {
  discente: {
    id: "discente",
    label: "Aluno",
    name: "Letícia Silva",
    role: "Matrícula: 2037538292",
    avatarText: "LS",
    title: "Olá, Letícia!",
    subtitle: "Semestre 2026.2 · Engenharia de Software (Campus II)",
    navItems: [
      { id: "home", label: "Início", icon: "home", active: true },
      { id: "matricula", label: "Matrícula", icon: "check-circle" },
      { id: "notas", label: "Notas e Frequência", icon: "award" },
      { id: "horario", label: "Grade Horária", icon: "clock" },
      { id: "historico", label: "Histórico", icon: "file-text" },
      { id: "financeiro", label: "Financeiro", icon: "dollar-sign" },
      { id: "biblioteca", label: "Biblioteca", icon: "book-open" },
      { id: "documentos", label: "Documentos", icon: "folder" },
      { id: "suporte", label: "Suporte", icon: "message-circle" },
    ],
    kpis: [
      { label: "Disciplinas Matriculadas", value: "7", colorClass: "kpi-green", icon: "book-open" },
      { label: "Faltas no Semestre", value: "4", colorClass: "kpi-yellow", icon: "user-x" },
      { label: "IRA Acumulado", value: "8,7", colorClass: "kpi-purple", icon: "award" },
      { label: "Pendências Financeiras", value: "1", colorClass: "kpi-pink", icon: "alert-circle" },
    ],
  },
  docente: {
    id: "docente",
    label: "Professor",
    name: "Prof. Ricardo Santos",
    role: "D. Computação · Matrícula: 90214",
    avatarText: "RS",
    title: "Olá, Prof. Ricardo!",
    subtitle: "Departamento de Computação · 3 turmas ativas",
    navItems: [
      { id: "home", label: "Início", icon: "home", active: true },
      { id: "turmas", label: "Minhas Turmas", icon: "users" },
      { id: "notas", label: "Lançar Notas", icon: "edit-3" },
      { id: "frequencia", label: "Frequência", icon: "user-check" },
      { id: "plano", label: "Plano de Ensino", icon: "file-text" },
      { id: "orientacoes", label: "Orientações", icon: "user" },
      { id: "professores", label: "Cadastrar Professores", icon: "users" },
      { id: "relatorios", label: "Relatórios", icon: "folder" },
      { id: "suporte", label: "Suporte", icon: "message-circle" },
    ],
    kpis: [
      { label: "Turmas Ativas", value: "3", colorClass: "kpi-green", icon: "users" },
      { label: "Alunos Matriculados", value: "127", colorClass: "kpi-purple", icon: "user-check" },
      { label: "Notas Pendentes", value: "42", colorClass: "kpi-yellow", icon: "edit-3" },
      { label: "Orientandos", value: "5", colorClass: "kpi-pink", icon: "user" },
    ],
  },
  colegiado: {
    id: "colegiado",
    label: "Colegiado",
    name: "Profª Ana Rocha",
    role: "Coordenação · Eng. Software",
    avatarText: "AR",
    title: "Painel do Colegiado",
    subtitle: "Engenharia de Software · Coordenação de Curso",
    navItems: [
      { id: "home", label: "Início", icon: "home", active: true },
      { id: "processos", label: "Processos", icon: "file-text" },
      { id: "aproveitamento", label: "Aproveitamento", icon: "check-circle" },
      { id: "matriculas", label: "Matrículas", icon: "users" },
      { id: "corpo", label: "Corpo Docente", icon: "user-check" },
      { id: "ementas", label: "Ementas", icon: "book-open" },
      { id: "relatorios", label: "Relatórios", icon: "folder" },
      { id: "atas", label: "Atas", icon: "file-text" },
      { id: "config", label: "Configurações", icon: "clock" },
    ],
    kpis: [
      { label: "Processos Abertos", value: "18", colorClass: "kpi-yellow", icon: "folder" },
      { label: "Matrículas Deferidas", value: "312", colorClass: "kpi-green", icon: "check-circle" },
      { label: "Trancamentos", value: "9", colorClass: "kpi-pink", icon: "user-minus" },
      { label: "Docentes Ativos", value: "24", colorClass: "kpi-purple", icon: "users" },
    ],
  },
  ti_suporte: {
    id: "ti_suporte",
    label: "TI & Suporte",
    name: "André Santos",
    role: "Gerente de TI & Infraestrutura",
    avatarText: "AS",
    title: "Central de TI & Suporte",
    subtitle: "Monitoramento e Chamados · Atualizado em tempo real",
    navItems: [
      { id: "home", label: "Início", icon: "home", active: true },
      { id: "chamados", label: "Chamados", icon: "message-circle" },
      { id: "infra", label: "Infraestrutura", icon: "hard-drive" },
      { id: "usuarios", label: "Usuários", icon: "users" },
      { id: "integracoes", label: "Integrações", icon: "award" },
      { id: "logs", label: "Logs do Sistema", icon: "file-text" },
      { id: "backups", label: "Backups", icon: "folder" },
      { id: "relatorios", label: "Relatórios", icon: "clock" },
      { id: "config", label: "Configurações", icon: "alert-circle" },
    ],
    kpis: [
      { label: "Chamados Abertos", value: "23", colorClass: "kpi-yellow", icon: "message-circle" },
      { label: "Tempo Médio de Resposta", value: "2,4h", colorClass: "kpi-green", icon: "clock" },
      { label: "Servidores Online", value: "98%", colorClass: "kpi-purple", icon: "hard-drive" },
      { label: "Incidentes Críticos", value: "2", colorClass: "kpi-pink", icon: "alert-triangle" },
    ],
  },
  financeiro: {
    id: "financeiro",
    label: "Financeiro",
    name: "Mariana Lima",
    role: "Coordenação Financeira",
    avatarText: "ML",
    title: "Painel Financeiro",
    subtitle: "Gestão de Mensalidades e Bolsas · Semestre 2026.2",
    navItems: [
      { id: "home", label: "Início", icon: "home", active: true },
      { id: "mensalidades", label: "Mensalidades", icon: "dollar-sign" },
      { id: "boletos", label: "Boletos", icon: "file-text" },
      { id: "bolsas", label: "Bolsas e Descontos", icon: "award" },
      { id: "inadimplencia", label: "Inadimplência", icon: "alert-circle" },
      { id: "convenios", label: "Convênios", icon: "folder" },
      { id: "relatorios", label: "Relatórios Financeiros", icon: "file-text" },
      { id: "conciliacao", label: "Conciliação", icon: "check-circle" },
      { id: "config", label: "Configurações", icon: "clock" },
    ],
    kpis: [
      { label: "Receita do Semestre", value: "R$ 2.480.750", colorClass: "kpi-green", icon: "dollar-sign" },
      { label: "Boletos Emitidos", value: "1.847", colorClass: "kpi-yellow", icon: "file-text" },
      { label: "Taxa de Inadimplência", value: "12,3%", colorClass: "kpi-pink", icon: "alert-triangle" },
      { label: "Bolsas Concedidas", value: "189", colorClass: "kpi-purple", icon: "award" },
    ],
  },
};

/**
 * Registro de Usuários no Sistema (RBAC)
 * O perfil do usuário é obtido diretamente pelo seu cadastro/matrícula
 */
export interface RegistroUsuario {
  matricula: string;
  usuario: string;
  nome: string;
  perfil: PerfilId;
  descricaoVínculo: string;
}

export const REGISTROS_USUARIOS: RegistroUsuario[] = [
  {
    matricula: "2037538292",
    usuario: "leticia.silva",
    nome: "Letícia Silva",
    perfil: "discente",
    descricaoVínculo: "Estudante (Eng. de Software)",
  },
  {
    matricula: "90214",
    usuario: "ricardo.santos",
    nome: "Prof. Ricardo Santos",
    perfil: "docente",
    descricaoVínculo: "Docente (Departamento de Computação)",
  },
  {
    matricula: "10042",
    usuario: "ana.rocha",
    nome: "Profª Ana Rocha",
    perfil: "colegiado",
    descricaoVínculo: "Coordenação de Curso / Secretaria",
  },
  {
    matricula: "55018",
    usuario: "andre.santos",
    nome: "André Santos",
    perfil: "ti_suporte",
    descricaoVínculo: "Gerência de TI & Infraestrutura",
  },
  {
    matricula: "33075",
    usuario: "mariana.lima",
    nome: "Mariana Lima",
    perfil: "financeiro",
    descricaoVínculo: "Coordenação Financeira",
  },
];

/**
 * Localiza o usuário pelo número de matrícula ou login/usuário informado
 */
export function buscarUsuarioPorLogin(identificador: string): RegistroUsuario | null {
  const limpo = identificador.trim().toLowerCase();
  return (
    REGISTROS_USUARIOS.find(
      (u) =>
        u.matricula.toLowerCase() === limpo ||
        u.usuario.toLowerCase() === limpo ||
        u.usuario.replace(".", "").toLowerCase() === limpo
    ) || null
  );
}
