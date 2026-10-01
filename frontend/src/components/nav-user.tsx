import {
  Avatar,
  AvatarFallback,
} from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import { useAuth } from "@/contexts/AuthContext";
import {
  EllipsisVerticalIcon,
  LogOutIcon,
  ShieldCheckIcon,
} from "lucide-react";

export function NavUser() {
  const { user, logout } = useAuth();
  const { isMobile } = useSidebar();

  if (!user) return null;

  // Iniciais do nome para AvatarFallback
  const iniciais = user.nome
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <SidebarMenuButton size="lg" className="aria-expanded:bg-muted" />
            }
          >
            <Avatar className="size-8  bg-primary/10 text-primary font-semibold">
              <AvatarFallback className="">{iniciais}</AvatarFallback>
            </Avatar>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium">{user.nome}</span>
              <span className="truncate text-xs text-muted-foreground">
                {user.email}
              </span>
            </div>
            <EllipsisVerticalIcon className="ml-auto size-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="min-w-56"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuGroup>
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-2 px-2 py-2 text-left text-sm">
                  <Avatar className="size-9  bg-primary/10 text-primary font-semibold">
                    <AvatarFallback className="">{iniciais}</AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <Typography variant="small" className="truncate font-medium">
                      {user.nome}
                    </Typography>
                    <Typography variant="muted" className="truncate text-xs">
                      {user.email}
                    </Typography>
                  </div>
                </div>
              </DropdownMenuLabel>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem disabled>
                <ShieldCheckIcon className="mr-2 h-4 w-4 text-muted-foreground" />
                <Typography variant="small">Perfil: {user.perfil}</Typography>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:bg-destructive/10 focus:text-destructive cursor-pointer"
              onClick={logout}
            >
              <LogOutIcon className="mr-2 h-4 w-4" />
              <Typography variant="small">Sair do Sistema</Typography>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
