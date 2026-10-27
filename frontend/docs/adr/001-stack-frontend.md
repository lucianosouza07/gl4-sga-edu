# ADR 001: Definição da Stack Front-end

## Status
Aprovado

## Contexto
Necessidade de evoluir o protótipo do Figma para código, definindo uma stack padronizada que garanta tipagem estática, facilidade de manutenção e integração fluida de componentes.

## Decisão
Adotaremos a seguinte stack de tecnologia para a interface de usuário:

- **Library Principal:** React com **TypeScript**
- **Build Tool / Bundler:** Vite
- **Estilização:** CSS Tradicional (`.css`), aproveitando estilos declarativos e classes utilitárias/modulares para espelhar os tokens do Figma.
- **Gerenciador de Pacotes:** `npm` (gerenciamento padrão de dependências do Node.js).

## Justificativa
- **React + TypeScript:** Garante tipagem estática, reduzindo erros em tempo de execução e acelerando o desenvolvimento com autocomplete no editor.
- **Vite:** Oferece um ambiente de desenvolvimento e build extremamente rápido.
- **CSS Tradicional (`.css`):** Mantém a curva de aprendizado baixa e permite reaproveitamento direto dos estilos definidos no protótipo.
- **npm:** Solução nativa do ecossistema Node.js.

## Consequências
- Maior segurança no código devido à validação de tipos do TypeScript.
- Necessidade de definir interfaces/tipos para as propriedades (*props*) dos componentes React.