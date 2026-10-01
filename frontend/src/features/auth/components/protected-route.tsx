import React from "react";
import { Navigate, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/use-auth";
import type { PerfilUsuario } from "../data/auth.types";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ShieldAlert } from "lucide-react";

export interface ProtectedRouteProps {
  allowedRoles?: PerfilUsuario[];
  children?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  allowedRoles,
  children,
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center p-6">
        <div className="w-full max-w-md space-y-4">
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-10 w-1/2" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.perfil)) {
    return (
      <div className="flex h-screen w-full items-center justify-center p-6 bg-background">
        <Card className="max-w-md w-full border-destructive/30">
          <CardHeader className="text-center">
            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <CardTitle>
              <Typography variant="h3">Acesso Não Autorizado</Typography>
            </CardTitle>
            <CardDescription>
              <Typography variant="muted">
                Seu perfil de acesso ({user.perfil}) não possui permissão para visualizar esta página.
              </Typography>
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <Button variant="outline" onClick={() => window.history.back()}>
              Voltar para página anterior
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return children ? <>{children}</> : <Outlet />;
};
