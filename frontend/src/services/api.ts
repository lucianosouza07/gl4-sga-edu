import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor de Requisição: Injeta o token Bearer salvo no localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("gl4_access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor de Resposta: Trata 401 deslogando o usuário e redirecionando
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Ignora redirect se o 401 veio da própria tentativa de login com credencial errada
      const isLoginRequest = error.config?.url?.includes("/auth/login");
      if (!isLoginRequest) {
        localStorage.removeItem("gl4_access_token");
        localStorage.removeItem("gl4_user");
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);
