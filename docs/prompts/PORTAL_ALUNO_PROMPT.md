# Prompt — Portal do Aluno (Semeando)

Cole este prompt inteiro numa sessão nova do Claude Code, com o diretório de trabalho em
`C:\Users\Leonardo\Desktop\software_escolar` (ou peça pra sessão mudar pra lá).

---

Você vai construir o **Portal do Aluno** do "Semeando", um sistema de gestão escolar. É um
app React **separado** do painel administrativo que já existe em `frontend/` — não mexa
nele. É um MVP de projeto de faculdade: **não precisa de segurança robusta**, só precisa
funcionar de ponta a ponta contra a API real.

## Contexto do projeto

- Backend: FastAPI (monolito modular) em `backend/`, rodando em `http://localhost:8000`
  (venv Python local em `backend/.venv`, **não Docker** — não assuma Docker disponível).
- Banco: Postgres local na porta 5432, banco `semeando`, usuário `semeando`/senha `semeando`.
- Painel administrativo já existe em `frontend/` (React + Vite + TS + Tailwind, porta 5173) —
  leia esse código como referência de estilo visual e de como consumir a API, mas **não o
  edite**.
- Documentação: `docs/ARQUITETURA.md` (convenções do backend, LEIA antes de mexer em
  qualquer módulo — tem um teste automatizado, `tests/test_architecture.py`, que verifica
  as regras de lá) e `docs/FRONTEND_BACKEND_MAP.md`.
- Login de teste do admin: `admin@semeando.edu.br` / `admin1234`.

## ⚠️ Trabalho de backend obrigatório primeiro: o aluno hoje NÃO tem login

Diferente de responsável/professor/funcionário, a tabela `alunos`
(`backend/app/modules/pessoas/models.py`) **não tem** `user_id`, e o enum de perfis
(`backend/app/core/roles.py`, classe `Role`) **não tem** um valor `ALUNO`. Você precisa
adicionar isso, replicando EXATAMENTE o padrão que já existe pra `Professor` e
`Responsavel` (ambos têm login opcional). Leia esses dois antes de mexer em qualquer coisa:

- `backend/app/core/roles.py` — adicione `ALUNO = "ALUNO"` ao enum `Role`.
- `backend/app/modules/pessoas/models.py` — no model `Aluno`, adicione
  `user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)`
  (cópia exata do que já existe em `Professor`/`Responsavel`/`Funcionario`).
- `backend/app/modules/pessoas/schemas.py` — em `AlunoRead`, adicione `user_id: int | None`.
  Crie um schema de concessão de acesso pro aluno reaproveitando `AcessoCreate` (já existe,
  usado por responsável/professor/funcionário — é só `{email, password}`).
- `backend/app/modules/pessoas/service.py` e `repository.py` — adicione uma função
  `grant_aluno_acesso` (cópia do padrão de `grant_responsavel_acesso`, procure por esse nome)
  e `get_aluno_by_user(db, user_id) -> AlunoRead | None` (cópia do padrão de
  `get_professor_by_user`).
- `backend/app/modules/pessoas/router.py` — adicione
  `POST /api/v1/pessoas/alunos/{aluno_id}/acesso` (mesmo formato de
  `POST /responsaveis/{id}/acesso`), perfis `ADMIN, SECRETARIA`.
- **Gere e rode a migration**: `cd backend && .venv\Scripts\python.exe -m alembic revision
  --autogenerate -m "aluno_user_id"` e depois
  `.venv\Scripts\python.exe -m alembic upgrade head`. **Leia o arquivo gerado antes de
  rodar** pra confirmar que só adiciona a coluna `user_id` em `alunos` (não deveria mudar
  mais nada).
- Confirme que o backend ainda sobe: `cd backend && .venv\Scripts\python.exe -c "import
  app.main"`.

Depois disso, o login do aluno funciona pelo **mesmo endpoint de sempre**:
`POST /api/v1/auth/login`, só que o usuário foi criado com `role: ALUNO` via o endpoint de
acesso que você acabou de criar.

### Ajuste de permissões a fazer nos módulos que o aluno vai usar

Hoje `notas`, `frequencia`, `financeiro`, `comunicacao` e `matricula` dão acesso de leitura
pro perfil `RESPONSAVEL` nos dados dos próprios filhos. Você precisa estender essas MESMAS
checagens pro perfil `ALUNO` ver os PRÓPRIOS dados (não de outros alunos). O jeito mais
simples, módulo por módulo:

- Em cada `permissions.py` relevante (`notas`, `frequencia`, `financeiro`, `comunicacao`),
  adicione `Role.ALUNO` nas tuplas de leitura (ex.: `CAN_VER_BOLETIM`, `CAN_VER_FREQUENCIA`).
- No `service.py` de cada um, onde hoje tem uma checagem tipo "se for RESPONSAVEL, chama
  `ensure_can_access_aluno`", adicione: "se for ALUNO, só pode acessar quando o `aluno_id`
  do próprio usuário (via `pessoas.service.get_aluno_by_user(db, user.id)`) bate com o
  `aluno_id` pedido — senão 404". Mantenha o padrão de levantar `NotFoundError` (não
  `ForbiddenError`) pra não revelar que o recurso existe, igual já é feito pra RESPONSAVEL.
- `pessoas.service.ensure_can_access_aluno` também merece esse tratamento (hoje só trata
  `RESPONSAVEL`) — adicione o caso `ALUNO` lá, assim qualquer módulo que já chama essa
  função ganha suporte a aluno de graça.
- Adicione também um endpoint `GET /api/v1/pessoas/alunos/eu` (perfil `ALUNO`) que devolve
  o próprio `AlunoRead` via `get_aluno_by_user` — é o que o app vai chamar logo após o login
  pra saber quem é o aluno logado (sem precisar adivinhar o `aluno_id`).

Depois de cada mudança, rode `cd backend && .venv\Scripts\python.exe -c "import app.main"`
pra garantir que nada quebrou.

## O que já existe e você PODE usar direto (sem mudar nada)

- `GET /api/v1/calendario/eventos?de=&ate=` — qualquer autenticado vê.
- `POST /api/v1/auth/me/senha` — trocar a própria senha.
- `GET /api/v1/auth/me` — dados do próprio usuário (nome, email).

## O que construir (frontend)

Crie um projeto novo em `portal-aluno/` (irmão de `frontend/` e `backend/`, na raiz do
repo). Mesma stack do `frontend/` existente: **React + Vite + TypeScript + Tailwind v4**.

```
cd C:\Users\Leonardo\Desktop\software_escolar
npm create vite@latest portal-aluno -- --template react-ts
cd portal-aluno
npm install
npm install react-router-dom axios lucide-react
npm install -D tailwindcss @tailwindcss/vite
```

Configure `vite.config.ts` com o plugin do Tailwind e `server.port: 5175`. Configure `.env`
com `VITE_API_URL=http://localhost:8000/api/v1`.

**Adicione a porta 5175 em `backend/app/core/config.py`, campo `cors_origins`** (senão o
navegador bloqueia as chamadas) e reinicie o servidor do backend depois.

**Reaproveite os padrões visuais do `frontend/` existente** (não copie arquivos,
reimplemente): layout simples (pode ser até mais enxuto que o painel admin — um app de
aluno não precisa de sidebar cheia de menu, pode ser um layout com 4-5 ícones de navegação
inferior/lateral), cor primária `emerald-600`, cards `rounded-xl border border-slate-200
bg-white`. Dê uma lida em `frontend/src/App.tsx`, `frontend/src/layout/AppLayout.tsx` e
`frontend/src/api/client.ts` antes de começar, pra copiar o estilo de cliente HTTP (axios
com interceptor de refresh token).

### Telas (tudo só leitura, exceto trocar senha e marcar aviso como lido)

1. **Login** — `POST /auth/login`.
2. **Início/Dashboard** — resumo: média geral, % de frequência, próximos eventos, avisos
   não lidos.
3. **Boletim** — `GET /notas/alunos/eu/boletim` (ou use o id retornado por
   `GET /pessoas/alunos/eu`, dependendo de como você implementou — confirme qual caminho
   ficou mais simples no backend que você acabou de escrever).
4. **Frequência** — `GET /frequencia/alunos/{meu_id}?de=&ate=`, com o percentual em
   destaque.
5. **Calendário** — `GET /calendario/eventos`.
6. **Mural de avisos** — `GET /comunicacao/avisos`, marcar como lido.
7. **Meu perfil** — nome, email, trocar senha.

## Regras importantes

- Esse app é **totalmente só-leitura** sobre a vida acadêmica (nenhuma tela de editar nota,
  frequência, financeiro ou aviso). As únicas ações são: trocar a própria senha e marcar
  aviso como lido.
- Não precisa de testes automatizados, não precisa de Docker, não precisa de CI. É MVP.
- Se o aluno tentar acessar algo que não é dele (não deveria nem conseguir pela UI, mas o
  backend tem que recusar de qualquer forma), confirme que o backend devolve 404, não vaza
  dado de outro aluno.

## Ao terminar

1. Rode `npm run build` no `portal-aluno/` e confirme que não tem erro de tipo.
2. Pelo painel admin (`http://localhost:5173`, login do admin), cadastre um aluno de teste
   se não existir nenhum, e conceda acesso de portal a ele usando o endpoint novo que você
   criou (`POST /pessoas/alunos/{id}/acesso` — ainda não tem botão no painel admin pra isso,
   pode chamar via `curl`/Postman mesmo, ou adicionar o botão no painel admin se quiser
   capricahr, mas não é obrigatório).
3. Suba o `npm run dev` do `portal-aluno/` e faça login real com esse aluno pra confirmar
   que funciona de ponta a ponta.
