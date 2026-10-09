# Mapeamento Frontend ↔ Backend

O frontend (`frontend/`) agora chama a API real do backend (`backend/`) em vez de dados
mockados. Este documento mapeia cada tela aos endpoints que ela usa, e descreve como
rodar os dois juntos.

## Como ligar os dois

1. **Banco + API** (precisa de Docker Desktop rodando):
   ```bash
   docker compose up -d db api
   ```
   A API sobe em `http://localhost:8000` (docs em `http://localhost:8000/api/docs`).

2. **Admin inicial** — a API não tem bootstrap (criar usuário exige já estar logado
   como ADMIN), então rode uma vez:
   ```bash
   cd backend
   uv run python -m scripts.seed_admin
   ```
   Cria `admin@semeando.edu.br` / `admin1234`. Idempotente — pode rodar de novo sem duplicar.

   Sem Docker, dá pra rodar a API local com `uv run uvicorn app.main:app --reload`,
   mas aí precisa de um Postgres acessível em `localhost:5433` (ajuste `DATABASE_URL`
   no `.env` do backend se usar outra porta).

3. **Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Lê a URL da API de `frontend/.env` (`VITE_API_URL=http://localhost:8000/api/v1`).

4. Login em `http://localhost:5173/login` com o admin criado no passo 2.

## Autenticação

- `access_token` fica em memória + `localStorage` (`frontend/src/api/client.ts`).
- `refresh_token` fica em cookie **httpOnly** (setado pelo backend); o axios manda
  `withCredentials: true` para carregá-lo automaticamente.
- Em qualquer 401, o interceptor do axios chama `POST /auth/refresh` uma vez e repete
  a requisição original; se o refresh falhar, desloga.
- Ao recarregar a página, `AuthContext` tenta `GET /auth/me` com o token salvo para
  restaurar a sessão sem precisar logar de novo.

| Tela/ação | Método | Endpoint | Arquivo frontend |
|---|---|---|---|
| Login | `POST` | `/api/v1/auth/login` | `src/pages/LoginPage.tsx`, `src/api/auth.ts` |
| Restaurar sessão (F5) | `GET` | `/api/v1/auth/me` | `src/lib/AuthContext.tsx` |
| Logout | `POST` | `/api/v1/auth/logout` | `src/lib/AuthContext.tsx` |
| Trocar senha | `POST` | `/api/v1/auth/me/senha` | `src/pages/PerfilPage.tsx` |
| Refresh automático (401) | `POST` | `/api/v1/auth/refresh` | `src/api/client.ts` |

## Pessoas

| Tela | Ações | Endpoints | Arquivo frontend |
|---|---|---|---|
| **Alunos** | listar/buscar, criar, editar, excluir | `GET/POST /pessoas/alunos`, `PATCH/DELETE /pessoas/alunos/{id}` | `src/pages/AlunosPage.tsx`, `src/api/pessoas.ts` |
| **Responsáveis** | listar/buscar, criar, editar, conceder acesso | `GET/POST /pessoas/responsaveis`, `PATCH /pessoas/responsaveis/{id}`, `POST /pessoas/responsaveis/{id}/acesso` | `src/pages/ResponsaveisPage.tsx` |
| **Professores** | listar/buscar, criar, editar, excluir | `GET/POST /pessoas/professores`, `PATCH/DELETE /pessoas/professores/{id}` | `src/pages/ProfessoresPage.tsx` |
| **Funcionários** | listar/buscar, criar, editar, excluir | `GET/POST /pessoas/funcionarios`, `PATCH/DELETE /pessoas/funcionarios/{id}` | `src/pages/FuncionariosPage.tsx` |

**Regras do backend refletidas no form de Alunos:** criar aluno exige pelo menos 1
responsável vinculado, com exatamente 1 marcado como financeiro — o form simplifica
isso pedindo 1 responsável (já cadastrado) na criação; vínculos extras exigiriam
`POST /pessoas/alunos/{id}/responsaveis` (endpoint já mapeado em `src/api/pessoas.ts`,
ainda sem tela própria).

## Turmas

| Ação | Endpoint | Arquivo frontend |
|---|---|---|
| Listar | `GET /turmas` | `src/pages/TurmasPage.tsx` |
| Criar | `POST /turmas` | idem |
| Editar (capacidade/ativa) | `PATCH /turmas/{id}` | idem |
| Vincular/desvincular professor | `POST/DELETE /turmas/{id}/professores/...` | mapeado em `src/api/turmas.ts`, sem UI ainda |

Observação: `nome`, `segmento` e `vagas_disponiveis` são campos computados pelo
backend (`@computed_field`) — o frontend só os lê, nunca envia.

## Matrículas

| Ação | Endpoint | Arquivo frontend |
|---|---|---|
| Listar (com filtro de status) | `GET /matriculas?status=...` | `src/pages/MatriculasPage.tsx` |
| Criar (aluno já cadastrado) | `POST /matriculas` | idem |
| Iniciar análise | `POST /matriculas/{id}/analise` | idem (chamado automaticamente antes de aprovar, se ainda `PRE_MATRICULA`) |
| Aprovar (escolhe turma) | `POST /matriculas/{id}/aprovar` | idem |
| Rejeitar (motivo obrigatório) | `POST /matriculas/{id}/rejeitar` | idem |
| Cancelar | `POST /matriculas/{id}/cancelar` | mapeado em `src/api/matriculas.ts`, sem botão na UI ainda |
| Checar/upload/download de documento | `PATCH/POST/GET /matriculas/{id}/documentos/{tipo}/...` | mapeado em `src/api/matriculas.ts`, sem UI ainda (fica para o detalhe de matrícula) |

A máquina de estados do backend é: `PRE_MATRICULA → EM_ANALISE → APROVADA → ...`.
A tela cria sempre como pré-matrícula de um aluno existente (a criação de aluno novo
direto na pré-matrícula — campo `aluno` do `PreMatriculaCreate` — não está exposta na UI).

## Usuários do sistema (admin)

| Ação | Endpoint | Arquivo frontend |
|---|---|---|
| Listar | `GET /auth/users` | `src/pages/UsuariosPage.tsx` |
| Criar | `POST /auth/users` | idem |
| Editar (nome/papel/status) | `PATCH /auth/users/{id}` | idem |

## O que ainda não está na UI (mas a API já suporta)

- Upload/download de documentos de matrícula (certidão, cartão de vacina etc.)
- Adicionar/remover vínculos extras de responsável num aluno já existente
- Vincular/desvincular professor de uma turma
- Cancelar matrícula
- Cadastro público de responsável (`POST /pessoas/responsaveis/registro`) — é para o
  futuro portal do responsável, não para o painel administrativo

## Arquivos-chave

- `frontend/src/api/client.ts` — instância axios, token, refresh automático, parse de erro
- `frontend/src/types/api.ts` — tipos TypeScript espelhando os schemas Pydantic (snake_case)
- `frontend/src/api/{auth,pessoas,turmas,matriculas}.ts` — uma função por endpoint
- `frontend/src/lib/AuthContext.tsx` — sessão (login/logout/restaurar ao recarregar)
- `frontend/src/lib/useAsyncList.ts` — hook de loading/erro para listagens
- `backend/scripts/seed_admin.py` — cria o admin inicial para destravar o primeiro login
