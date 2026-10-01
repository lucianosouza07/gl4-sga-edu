# 🎨 Planejamento de Conclusão da Etapa 1: Frontend com Vite, React, Tailwind e shadcn/ui

Este documento detalha o planejamento e o passo a passo para finalizar a **Etapa 1 (Preparação do Terreno)** no Frontend, incluindo a inicialização com Vite, configuração do Tailwind CSS, configuração do **shadcn/ui** e aplicação do tema **Meridian** (Tweakcn).

---

## 🎯 Escopo da Conclusão da Etapa 1

- [ ] Inicializar o frontend React + TypeScript com Vite.
- [ ] Configurar os aliases de importação (`@/*`) no Vite e TypeScript.
- [ ] Configurar o Tailwind CSS.
- [ ] Inicializar o **shadcn/ui**.
- [ ] Aplicar o tema **Meridian** via registro do Tweakcn:
  `npx shadcn@latest add https://tweakcn.com/r/themes/cmojzn0oy000505ldam699poc`
- [ ] Instalar dependências de comunicação e ícones (`axios`, `lucide-react`).
- [ ] Instalar os componentes base do shadcn necessários para o módulo de alunos (`button`, `input`, `table`, `dialog`, `badge`, `card`, `label`, `sonner`).
- [ ] Validar o servidor de desenvolvimento (`npm run dev`).

---

## 🛠️ Passo a Passo de Execução

### Passo 1: Limpar e inicializar o projeto Vite
Navegue até a pasta `frontend` e inicialize o template React com TypeScript:

```bash
cd frontend

# Se houver apenas a pasta placeholder 'modulo_id_name', inicialize o projeto com:
npm create vite@latest . -- --template react-ts
```

> **Atenção:** Caso o instalador pergunte sobre sobrescrever arquivos vazios existentes no diretório, confirme para criar na raiz da pasta `frontend/`.

Instale as dependências padrão do Node:
```bash
npm install
```

---

### Passo 2: Configurar Aliases de Caminho (`@/*`)

Para que o shadcn/ui e os imports funcionem perfeitamente com `@/components/...`:

1. Instale os tipos do Node para o TypeScript resolver `path`:
```bash
npm install -D @types/node
```

2. Atualize o `tsconfig.json` (ou `tsconfig.app.json`):
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

3. Atualize o `vite.config.ts`:
```typescript
import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

---

### Passo 3: Configurar o Tailwind CSS

Instale o Tailwind CSS e dependências utilitárias do ecossistema shadcn:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Configure o arquivo `tailwind.config.js` com suporte a variáveis CSS e animações:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx,js,jsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("tailwindcss-animate")],
}
```

---

### Passo 4: Inicializar o shadcn/ui

Execute o assistente do shadcn:

```bash
npx shadcn@latest init
```

Responda às perguntas recomendadas:
- **Which style would you like to use?** › `New York` (ou `Default`)
- **Which color would you like to use as base color?** › `Neutral` / `Slate`
- **Do you want to use CSS variables for colors?** › `yes`

---

### Passo 5: Aplicar o Tema Customizado (Meridian - Tweakcn)

Execute o comando fornecido para importar as variáveis e estilo do tema:

```bash
npx shadcn@latest add https://tweakcn.com/r/themes/cmojzn0oy000505ldam699poc
```

> **Sobre o tema Meridian:**
> - Paleta moderna em `oklch` com tons equilibrados para interfaces administrativas e educacionais.
> - Suporte nativo a modo claro e modo escuro (`dark mode`).
> - Tipografia limpa e sombras elegantes para cards e tabelas.

---

### Passo 6: Instalar Dependências Complementares

Instale o cliente HTTP e a biblioteca de ícones:

```bash
npm install axios lucide-react
```

---

### Passo 7: Instalar os Componentes do shadcn para o Cadastro de Alunos

Adicione os componentes essenciais que utilizaremos nas telas da Etapa 5:

```bash
npx shadcn@latest add button input table dialog badge card label dropdown-menu sonner
```

---

### Passo 8: Validação e Teste Local

Inicie o servidor de desenvolvimento do Vite:

```bash
npm run dev
```

Abra no navegador (normalmente `http://localhost:5173`) e confirme que o React está carregando com os estilos do Tailwind e shadcn/ui devidamente injetados.

---

## 📋 Checklist de Entrega da Fase 1

- [ ] Estrutura `frontend/src` gerada com Vite + React-TS
- [ ] Path alias `@` configurado e validado
- [ ] Tailwind CSS e `index.css` estilizados
- [ ] `components.json` gerado pelo shadcn
- [ ] Tema Meridian aplicado com sucesso
- [ ] `axios` e `lucide-react` instalados no `package.json`
- [ ] Componentes de UI instalados em `frontend/src/components/ui/`
