# 🎨 Planejamento de Conclusão da Etapa 1: Frontend com Vite, React, Tailwind v4 e shadcn/ui

Este documento detalha o passo a passo oficial para finalizar a **Etapa 1 (Preparação do Terreno)** utilizando **Tailwind CSS v4**, o plugin oficial `@tailwindcss/vite`, **shadcn/ui (CLI 4.x)** e o tema **Meridian** do Tweakcn.

---

## 🎯 Escopo da Etapa 1 (Frontend com Tailwind v4)

- [x] Inicializar o frontend React + TypeScript com Vite.
- [x] Instalar `@types/node` e configurar aliases de importação (`@/*`).
- [x] Instalar o **Tailwind CSS v4** e o plugin oficial `@tailwindcss/vite`.
- [x] Configurar o plugin `@tailwindcss/vite` no `vite.config.ts`.
- [x] Atualizar o `src/index.css` com o tema Meridian e Tailwind v4.
- [x] Executar o assistente do **shadcn/ui** (`npx shadcn@latest init`).
- [x] Aplicar o tema **Meridian** via Tweakcn (`cmojzn0oy000505ldam699poc`).
- [x] Instalar dependências complementares (`axios`, `lucide-react`).
- [x] Instalar componentes do shadcn (`npx shadcn@latest add --all`).
- [x] Envolver a aplicação no `TooltipProvider` no `src/main.tsx`.
- [x] Validar o build de produção (`npm run build` passou com sucesso).

---

## 🛠️ Passo a Passo de Execução

### Passo 1: Instalar Tailwind CSS v4 e o plugin Vite
No diretório `frontend`:

```bash
npm install tailwindcss @tailwindcss/vite
```

> **Por que mudou?** No Tailwind v4, **não** se usa mais `npx tailwindcss init -p`, nem `postcss.config.js` ou `tailwind.config.js`. A compilação é ultra-rápida e controlada diretamente pelo plugin oficial do Vite (`@tailwindcss/vite`).

---

### Passo 2: Configurar o `vite.config.ts`
Adicione o plugin `tailwindcss()` ao `vite.config.ts`:

```typescript
import path from "path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

---

### Passo 3: Configurar o `src/index.css`
Substitua o conteúdo de `src/index.css` por apenas:

```css
@import "tailwindcss";
```

---

### Passo 4: Garantir os Aliases no `tsconfig.app.json`
Certifique-se de que o `frontend/tsconfig.app.json` também tenha:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

### Passo 5: Inicializar o shadcn/ui com suporte a Tailwind v4
Execute o CLI oficial do shadcn:

```bash
npx shadcn@latest init
```

O shadcn detectará automaticamente o Vite com `@tailwindcss/vite` e criará o `components.json` configurado para Tailwind v4.

---

### Passo 6: Aplicar o Tema Meridian (Tweakcn)
Execute o comando para injetar as variáveis de cor oklch, fontes e sombras do tema:

```bash
npx shadcn@latest add https://tweakcn.com/r/themes/cmojzn0oy000505ldam699poc
```

---

### Passo 7: Instalar Bibliotecas Complementares
```bash
npm install axios lucide-react
```

---

### Passo 8: Instalar os Componentes de UI
```bash
npx shadcn@latest add button input table dialog badge card label dropdown-menu sonner
```

---

### Passo 9: Validação
Inicie o servidor de desenvolvimento:
```bash
npm run dev
```
Verifique se a aplicação sobe em `http://localhost:5173` sem erros de importação ou estilo.

---

## 🏛️ Passo 10: Padrão Arquitetural de Pastas (Feature Slices & Codebase Design)

O frontend adota a arquitetura modular orientada a **Features (Módulos Profundos)**:

- `src/features/<feature>/`: Módulo autocontido (`auth`, `alunos`, `dashboard`), encapsulando `components/`, `data/`, `hooks/`, `services/`, `views/` e a seam pública `index.ts`.
- `src/components/layout/`: Casca e navegação global da aplicação (`app-sidebar.tsx`, `site-header.tsx`, `dashboard-layout.tsx`).
- `src/components/shared/`: Componentes universais compartilhados (`page-header.tsx`, `tabela-paginacao.tsx`, `theme-toggle.tsx`).
- `src/components/ui/`: Primitivas atômicas do shadcn/ui.
- `src/api/`: Instância central do Axios (`client.ts`) e parser universal de erros (`handle-api-error.ts`).

