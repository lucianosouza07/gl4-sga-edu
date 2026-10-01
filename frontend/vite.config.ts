import path from "path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const rootDir = path.resolve(import.meta.dirname, "..");
  const env = loadEnv(mode, rootDir, "");

  const proxyTarget = env.VITE_PROXY_TARGET || "http://127.0.0.1:8000";
  const frontendPort = parseInt(env.VITE_PORT || env.FRONTEND_PORT || "5173", 10);
  const allowedHostsRaw =
    env.VITE_ALLOWED_HOSTS ||
    "gl4-sga-edu.luis-carvalho.online,localhost,127.0.0.1";
  const allowedHosts = allowedHostsRaw
    .split(",")
    .map((host) => host.trim())
    .filter(Boolean);

  return {
    envDir: rootDir,
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(import.meta.dirname, "./src"),
      },
    },
    server: {
      port: frontendPort,
      allowedHosts: allowedHosts.length > 0 ? allowedHosts : true,
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});