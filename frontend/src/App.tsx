import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, ProtectedRoute, LoginView, useAuth } from "@/features/auth";
import { DashboardLayout } from "@/components/layout";
import { OverviewView } from "@/features/dashboard";
import { AlunosView } from "@/features/alunos";
import { PortalAlunoView, MeusDadosView } from "@/features/portal-aluno";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";

/**
 * Componente de visualização adaptativa para a rota raiz (`/`).
 * Exibe a Carteirinha e Portal para Alunos, ou a Visão Geral de Métricas para Gestores.
 */
function AdaptiveRootView() {
  const { user } = useAuth();
  if (user?.perfil === "ALUNO") {
    return <PortalAlunoView />;
  }
  return <OverviewView />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <TooltipProvider>
          <Routes>
            {/* Rota Pública de Login */}
            <Route path="/login" element={<LoginView />} />

            {/* Rotas Autenticadas dentro do Layout Principal */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              {/* Rota Raiz Adaptativa (/): Aluno -> PortalAlunoView | Gestores -> OverviewView */}
              <Route index element={<AdaptiveRootView />} />

              {/* Rota de Autoatendimento do Aluno (/meus-dados) */}
              <Route
                path="meus-dados"
                element={
                  <ProtectedRoute allowedRoles={["ALUNO"]}>
                    <MeusDadosView />
                  </ProtectedRoute>
                }
              />

              {/* Módulo de Gestão Acadêmica - Alunos (/alunos) */}
              <Route
                path="alunos"
                element={
                  <ProtectedRoute allowedRoles={["ADMIN", "SECRETARIA", "PROFESSOR"]}>
                    <AlunosView />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Rota Coringa / Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster position="top-right" richColors />
        </TooltipProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
