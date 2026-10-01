import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "@/services/api";
import type { Usuario, TokenResponse } from "@/types/auth";

interface AuthContextType {
  user: Usuario | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (identificador: string, senha: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<Usuario | null>(() => {
    const savedUser = localStorage.getItem("gl4_user");
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("gl4_access_token")
  );
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Validação do token existente na inicialização da aplicação
  useEffect(() => {
    async function validarSessao() {
      const savedToken = localStorage.getItem("gl4_access_token");
      if (savedToken) {
        try {
          const response = await api.get<Usuario>("/auth/me");
          setUser(response.data);
          localStorage.setItem("gl4_user", JSON.stringify(response.data));
        } catch {
          // Token inválido ou expirado
          logout();
        }
      }
      setIsLoading(false);
    }

    validarSessao();
  }, []);

  const login = async (identificador: string, senha: string) => {
    const response = await api.post<TokenResponse>("/auth/login", {
      identificador,
      senha,
    });
    const { access_token, usuario } = response.data;

    setToken(access_token);
    setUser(usuario);
    localStorage.setItem("gl4_access_token", access_token);
    localStorage.setItem("gl4_user", JSON.stringify(usuario));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("gl4_access_token");
    localStorage.removeItem("gl4_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser utilizado dentro de um <AuthProvider />");
  }
  return context;
};
