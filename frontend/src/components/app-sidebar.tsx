import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from "@/components/ui/sidebar";
import { NavUser } from "@/components/nav-user";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import {
  GraduationCap,
  LayoutDashboard,
  Users,
  BookOpen,
  Settings,
  UserPlus,
} from "lucide-react";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();

  const navItems = [
    {
      title: "Visão Geral",
      url: "/",
      icon: LayoutDashboard,
      active: location.pathname === "/",
    },
    {
      title: "Alunos",
      url: "/alunos",
      icon: Users,
      active: location.pathname.startsWith("/alunos"),
    },
  ];

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader className="border-b border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              render={<Link to="/" />}
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs group-data-[collapsible=icon]:size-8">
                <GraduationCap className="h-5 w-5" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <Typography variant="small" className="font-semibold text-sidebar-foreground">
                  GL4 SGA-EDU
                </Typography>
                <Typography variant="muted" className="text-xs">
                  Gestão Acadêmica
                </Typography>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        <div className="pt-2 px-1 group-data-[collapsible=icon]:hidden">
          <Button
            nativeButton={false}
            className="w-full justify-start gap-2 bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs font-medium text-sm h-9 rounded-lg"
            render={<Link to="/alunos" />}
          >
            <UserPlus className="h-4 w-4 shrink-0" />
            <span>Novo Aluno</span>
          </Button>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>
            <Typography variant="muted" className="text-xs uppercase tracking-wider font-semibold">
              Módulos Acadêmicos
            </Typography>
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    isActive={item.active}
                    tooltip={item.title}
                    render={<Link to={item.url} />}
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="mt-auto">
          <SidebarGroupLabel>
            <Typography variant="muted" className="text-xs uppercase tracking-wider font-semibold">
              Instituição
            </Typography>
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton tooltip="Cursos e Turmas" disabled>
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Cursos (Em breve)</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton tooltip="Configurações" disabled>
                  <Settings className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Configurações</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  );
}
