# 🏛️ Arquitetura Multi-Role e Codebase Design: Guia para Implementações Futuras

**Sistema de Gestão Acadêmica — GL4 SGA-EDU**  
**Padrão Arquitetural Oficial:** *Domain-First com Costuras de Papel (Role Seams)* baseado em **Codebase Design (Deep Modules)**.

---

## 1. Visão Geral e Filosofia Arquitetural

Conforme o sistema evolui para suportar múltiplos perfis de usuários (`ADMIN`, `SECRETARIA`, `PROFESSOR`, `ALUNO` e futuros como `RESPONSAVEL`), o maior risco arquitetural é a **fragmentação em silos por papel** (organização *Role-First*).

### ❌ O Antipadrão a Evitar: *Role-First* (Módulos Rasos)
Organizar pastas primariamente pelo perfil de quem acessa:
```
# ANTIPADRÃO — NÃO FAZER:
backend/
  aluno/notas.py        # Duplica busca de matrículas e cálculo de média
  professor/notas.py    # Duplica fórmulas de aprovação e arredondamento
frontend/
  aluno/boletim/        # Duplica cards e formatação de notas
  professor/diario/     # Duplica tabelas e status badges
```
* **Módulos Rasos (Shallow Modules):** Interfaces quase tão complexas quanto a implementação, sem ocultação real de regras.
* **Quebra de Localidade (Locality):** Se a instituição altera a nota de corte de `7.0` para `6.0`, o desenvolvedor precisa modificar arquivos espalhados em múltiplos diretórios.
* **Risco de Inconsistência:** O aluno visualiza uma média calculada com regra X enquanto o diário do professor usa regra Y.

---

###  O Padrão Adotado: *Domain-First com Costuras de Papel*

No GL4 SGA-EDU, a regra de ouro é: **O domínio de negócio é profundo e único; os papéis de usuário são apenas costuras (seams) de autorização e escopo.**

```
                               ┌────────────────────────────────────────────────────────┐
                               │             MÓDULO PROFUNDO DE DOMÍNIO                 │
                               │  (NotaService, AlunoService, MatriculaService, etc.)   │
                               │  - Regras de cálculo (médias, aprovação, frequência)   │
                               │  - Validações de integridade acadêmica                 │
                               │  - Modelagem e persistência SQL                        │
                               └───────────────────────────▲────────────────────────────┘
                                                           │
                                ┌──────────────────────────┼───────────────────────────┐
                                │                          │                           │
                   (Costura 1: Self-Service)      (Costura 2: Docente)         (Costura 3: Gestão)
                   Role: ALUNO                    Role: PROFESSOR              Roles: SECRETARIA / ADMIN
                   Endpoints: /api/v1/.../me      Endpoints: /api/v1/turmas/.. Endpoints: /api/v1/alunos/..
                   Frontend: portal-aluno/        Frontend: portal-professor/  Frontend: alunos/
```

---

## 2. Princípios de Codebase Design Aplicados

| Princípio | Aplicação no SGA-EDU |
| :--- | :--- |
| **Módulo Profundo (Deep Module)** | Serviços no backend (`NotaService`, `AlunoService`) e componentes de domínio no frontend (`BoletimCard`, `TabelaNotas`) possuem interface pequena e concentram alta complexidade interna. |
| **Costura (Seam)** | O local exato onde o comportamento varia por perfil: no backend são os **endpoints com `require_roles` e injeção de identidade**; no frontend são as **views dos portais e `AppSidebar`**. |
| **Alavancagem (Leverage)** | Uma única implementação de cálculo de boletim atende Aluno, Professor, Secretaria e futuros Responsáveis sem reimplementação. |
| **Localidade (Locality)** | Se a regra pedagógica de aprovação mudar, apenas o método do serviço de domínio é alterado e todos os perfis são atualizados automaticamente. |
| **Teste de Exclusão (Deletion Test)** | Se removermos a pasta `portal-aluno/`, nenhuma regra de cálculo de nota ou contrato de API se perde. O domínio permanece íntegro. |

---

## 3. Padrão Arquitetural no Backend (Python / FastAPI)

Para qualquer nova funcionalidade com múltiplos papéis, a estrutura do backend deve seguir 3 camadas:

### 3.1. Camada de Domínio Puro (`app/services/<dominio>_service.py`)
Contém funções estáticas ou classes com regras de negócio completas, sem referências diretas a requisições HTTP, headers ou sessões de frontend.

```python
# app/services/nota_service.py
class NotaService:
    @staticmethod
    def obter_boletim_aluno(db: Session, aluno_id: int) -> BoletimEscolarResponse:
        """
        Módulo Profundo:
        - Recupera matrículas e disciplinas do semestre ativo
        - Calcula médias ponderadas e aplica regras de arredondamento
        - Determina situação acadêmica (APROVADO, REPROVADO, EM_EXAME)
        - Retorna o schema canônico de Boletim
        """
        # Regra de negócio pura e testável isoladamente
        ...
```

### 3.2. As Três Costuras de Endpoints (API Seams)
Os endpoints em `app/api/v1/endpoints/` atuam como adaptadores de entrada, aplicando autorização e contexto:

#### 1. Costura Self-Service (Discente: `ALUNO`)
- **Regra:** O endpoint **nunca** aceita `aluno_id` via URL ou Body. O ID é extraído diretamente do token JWT (`current_user.id`).
- **Segurança:** Imunidade nativa a vulnerabilidades IDOR (Insecure Direct Object Reference).
- **Prefixo Canônico:** `/api/v1/<recurso>/me` ou `/api/v1/<recurso>/minhas`.

```python
@router.get("/alunos/me/boletim", response_model=BoletimEscolarResponse)
def obter_meu_boletim(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([PerfilUsuario.ALUNO])),
):
    aluno = AlunoService.obter_por_usuario_id(db, current_user.id)
    return NotaService.obter_boletim_aluno(db, aluno_id=aluno.id)
```

#### 2. Costura Operacional (Docente: `PROFESSOR`)
- **Regra:** Valida se o docente logado tem vínculo ativo com a turma/disciplina antes de permitir leitura ou alteração.
- **Prefixo Canônico:** `/api/v1/turmas/{turma_id}/...`.

```python
@router.post("/turmas/{turma_id}/notas", response_model=GradeLancadaResponse)
def lancar_notas(
    turma_id: int,
    payload: LancamentoNotasRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([PerfilUsuario.PROFESSOR])),
):
    # Valida vínculo institucional do professor autenticado
    ProfessorService.validar_docente_na_turma(db, current_user.id, turma_id)
    return NotaService.lancar_notas_turma(db, turma_id, payload)
```

#### 3. Costura Administrativa (Gestão: `SECRETARIA` / `ADMIN`)
- **Regra:** Permite busca por ID explícito para auditoria, correção de notas, histórico escolar e relatórios.
- **Prefixo Canônico:** `/api/v1/alunos/{aluno_id}/...` ou `/api/v1/turmas/{turma_id}/...`.

```python
@router.get("/alunos/{aluno_id}/boletim", response_model=BoletimEscolarResponse)
def obter_boletim_aluno_admin(
    aluno_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles([PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN])),
):
    # Reutiliza o mesmo método profundo
    return NotaService.obter_boletim_aluno(db, aluno_id=aluno_id)
```

---

## 4. Padrão Arquitetural no Frontend (React + Feature Slices)

O frontend divide-se estritamente entre **Módulos de Domínio Reutilizáveis** e **Portais Especializados**:

```
src/
├── features/
│   ├── notas/                              # ◄── MÓDULO DE DOMÍNIO REUTILIZÁVEL
│   │   ├── types/
│   │   │   └── nota.types.ts               # Schemas de dados e interfaces TypeScript
│   │   ├── hooks/
│   │   │   ├── use-boletim.ts              # Consulta de boletim (genérico)
│   │   │   └── use-lancamento-notas.ts     # Mutação de notas por turma
│   │   ├── components/
│   │   │   ├── boletim-card.tsx            # Card visual de disciplina, médias e faltas
│   │   │   ├── status-aprovacao-badge.tsx  # Badge visual (Aprovado / Reprovado / Exame)
│   │   │   └── tabela-lancar-notas.tsx     # Tabela editável de notas
│   │   └── index.ts                        # Seam pública exportando componentes e hooks
│   │
│   ├── portal-aluno/                       # ◄── PORTAL DISCENTE (Orquestrador)
│   │   ├── views/
│   │   │   ├── portal-aluno-view.tsx       # Home do discente: consome <BoletimCard />
│   │   │   └── meus-dados-view.tsx         # Autoatendimento discente (/meus-dados)
│   │   └── index.ts
│   │
│   ├── portal-professor/                   # ◄── PORTAL DOCENTE (Orquestrador)
│   │   ├── views/
│   │   │   └── diario-classe-view.tsx      # Diário: consome <TabelaLancarNotas />
│   │   └── index.ts
│   │
│   └── alunos/                             # ◄── GESTÃO ACADÊMICA (Secretaria / Admin)
│       └── views/
│           └── aluno-detalhe-view.tsx      # Aba "Boletim": consome o MESMO <BoletimCard />!
```

### 4.1. Widgets de Domínio Reutilizáveis
Componentes como `<BoletimCard />` recebem dados puros e são agnósticos de permissão:
```tsx
// src/features/notas/components/boletim-card.tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { StatusAprovacaoBadge } from "./status-aprovacao-badge";
import type { DisciplinaBoletim } from "../types/nota.types";

interface BoletimCardProps {
  disciplina: DisciplinaBoletim;
}

export function BoletimCard({ disciplina }: BoletimCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-semibold">{disciplina.nome}</CardTitle>
        <StatusAprovacaoBadge status={disciplina.situacao} />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-2 text-sm">
          <div><span className="text-muted-foreground">N1:</span> {disciplina.nota1 ?? "-"}</div>
          <div><span className="text-muted-foreground">N2:</span> {disciplina.nota2 ?? "-"}</div>
          <div><span className="text-muted-foreground">Média:</span> <strong>{disciplina.media}</strong></div>
          <div><span className="text-muted-foreground">Faltas:</span> {disciplina.totalFaltas}</div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 4.2. Views de Portais (Compositores Finos)
A view do portal discente apenas consome a API do próprio aluno (`/me`) e renderiza os widgets:
```tsx
// src/features/portal-aluno/views/meu-boletim-view.tsx
import { useMeuBoletim } from "@/features/notas/hooks/use-boletim";
import { BoletimCard } from "@/features/notas/components/boletim-card";

export function MeuBoletimView() {
  const { boletim, isLoading } = useMeuBoletim();

  if (isLoading) return <div>Carregando boletim escolar...</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {boletim?.disciplinas.map((disc) => (
        <BoletimCard key={disc.id} disciplina={disc} />
      ))}
    </div>
  );
}
```

---

## 5. Roteamento Adaptativo e Menu Dinâmico

### 5.1. Rota Raiz Adaptativa (`/`)
A rota raiz `/` adapta sua exibição com base no perfil do usuário autenticado:
- **`ADMIN` / `SECRETARIA`:** Renderiza `<OverviewView />` (Métricas institucionais, KPIs, gráficos de matrículas).
- **`ALUNO`:** Renderiza `<PortalAlunoView />` (Carteirinha digital, atalhos rápidos e widgets acadêmicos).
- **`PROFESSOR`:** Renderiza `<PortalProfessorView />` (Minhas turmas e diários pendentes).

### 5.2. Navegação Lateral Declarativa (`AppSidebar`)
O menu lateral filtra opções por `user.perfil`:
- Links administrativos ("Novo Aluno", "Alunos", "Configurações") são ocultados para discentes e docentes.
- Links de autoatendimento ("Meu Portal", "Meus Dados", "Meu Boletim") são exibidos para discentes.

---

## 6. Prova de Escalabilidade: O "Teste da Nova Role"

Para validar se uma arquitetura é verdadeiramente escalável, simulamos a adição de uma nova role no futuro:

> **Cenário:** O sistema precisa permitir que `RESPONSAVEL` (Pais/Responsáveis) visualizem as notas e frequência dos filhos.

### O que NÃO muda:
1. **Regras de Negócio (`NotaService`):** Alteração **zero**. Fórmulas, médias e aprovações permanecem idênticas.
2. **Componentes Visuais (`BoletimCard`):** Alteração **zero**. O card de visualização já está pronto e testado.

### O que é adicionado (Custo Mínimo e Cirúrgico):
1. **Backend:** 1 novo endpoint em `app/api/v1/endpoints/responsaveis.py`:
   - `GET /api/v1/responsaveis/me/filhos/{aluno_id}/boletim`
   - Valida vínculo filial entre o responsável autenticado e o aluno, e delega para `NotaService.obter_boletim_aluno(db, aluno_id)`.
2. **Frontend:** 1 view simples em `features/portal-responsavel/views/filho-boletim-view.tsx` consumindo `<BoletimCard />`.

---

## 7. Checklist para Implementação de Novas Funcionalidades

Ao criar qualquer funcionalidade que envolva mais de um perfil de usuário:

- [ ] **1. Identificar o Módulo Profundo:** A regra de cálculo ou processo foi implementada em um Service de domínio puro (`app/services/`), independente de quem chama?
- [ ] **2. Separar as Costuras de API:**
  - Existe rota `/me` para o usuário consultar/atualizar seus próprios dados?
  - A rota `/me` extrai o ID exclusivamente do token JWT sem permitir alteração por parâmetro?
  - A rota operacional valida o vínculo de responsabilidade do solicitante (ex: professor na turma)?
  - A rota administrativa exige `require_roles([PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN])`?
- [ ] **3. Componentizar o Frontend:**
  - Os componentes visuais ricos foram colocados em `src/features/<dominio>/components/`?
  - As telas em `portal-<role>/` atuam apenas como orquestradores leves, sem reimplementar tabelas e cards?
- [ ] **4. Garantir Conformidade com Shadcn:** Nenhuma tag HTML crua proibida foi utilizada (auditar via `scripts/check_shadcn_usage.py`).
- [ ] **5. Testes Unitários e Integração:** Foram criados testes no Pytest para cada perfil (`200` para autorizado, `403` para perfil incorreto, `401` para não autenticado).
