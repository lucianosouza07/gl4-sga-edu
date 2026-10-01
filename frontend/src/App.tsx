import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, ProtectedRoute, LoginView } from "@/features/auth";
import { DashboardLayout } from "@/components/layout";
import { OverviewView } from "@/features/dashboard";
import { AlunosView } from "@/features/alunos";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <TooltipProvider>
          <Routes>
            {/* Rota Pública de Login */}
            <Route path="/login" element={<LoginView />} />

            {/* Rotas Autenticadas dentro do Dashboard */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              {/* Visão Geral */}
              <Route index element={<OverviewView />} />

              {/* Módulo de Gestão Acadêmica - Alunos */}
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
