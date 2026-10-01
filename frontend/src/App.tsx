import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/pages/Login";
import { DashboardLayout } from "@/pages/Dashboard/DashboardLayout";
import { OverviewPage } from "@/pages/Dashboard/OverviewPage";
import { AlunosPage } from "@/pages/Alunos";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <TooltipProvider>
          <Routes>
            {/* Rota Pública de Login */}
            <Route path="/login" element={<LoginPage />} />

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
              <Route index element={<OverviewPage />} />

              {/* Módulo de Gestão Acadêmica - Alunos */}
              <Route
                path="alunos"
                element={
                  <ProtectedRoute allowedRoles={["ADMIN", "SECRETARIA", "PROFESSOR"]}>
                    <AlunosPage />
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
