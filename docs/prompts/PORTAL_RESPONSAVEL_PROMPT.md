# Prompt — Portal do Responsável (Semeando)

Cole este prompt inteiro numa sessão nova do Claude Code, com o diretório de trabalho em
`C:\Users\Leonardo\Desktop\software_escolar` (ou peça pra sessão mudar pra lá).

---

Você vai construir o **Portal do Responsável** do "Semeando", um sistema de gestão escolar.
É um app React **separado** do painel administrativo que já existe em `frontend/` — não mexa
nele. É um MVP de projeto de faculdade: **não precisa de segurança robusta**, só precisa
funcionar de ponta a ponta contra a API real.

## Contexto do projeto

- Backend: FastAPI (monolito modular) em `backend/`, rodando em `http://localhost:8000`
  (venv Python local em `backend/.venv`, **não Docker** — não assuma Docker disponível).
- Banco: Postgres local na porta 5432, banco `semeando`, usuário `semeando`/senha `semeando`.
- Painel administrativo já existe em `frontend/` (React + Vite + TS + Tailwind, porta 5173) —
  leia esse código como referência de estilo visual e de como consumir a API, mas **não o
  edite**.
- Documentação de arquitetura: `docs/ARQUITETURA.md` (convenções do backend) e
  `docs/FRONTEND_BACKEND_MAP.md` (como o painel admin já se conecta à API — mesmo padrão
  de auth que você vai reaproveitar).
- Login de teste do admin: `admin@semeando.edu.br` / `admin1234` (útil pra você mesmo
  cadastrar um responsável de teste via painel admin, se precisar).

## O que já existe no backend (confirme lendo o código, não assuma cego)

O perfil `RESPONSAVEL` **já existe e já funciona** no backend:
- Login normal: `POST /api/v1/auth/login` (mesmo endpoint do painel admin, devolve
  `access_token`/`refresh_token`/`user` com `role: "RESPONSAVEL"`).
- `GET /api/v1/notas/alunos/{aluno_id}/boletim` — boletim do filho (RESPONSAVEL só acessa
  os próprios filhos, backend checa isso).
- `GET /api/v1/frequencia/alunos/{aluno_id}?de=&ate=` — histórico de frequência + percentual.
- `GET /api/v1/financeiro/cobrancas` — sem passar `aluno_id`, já filtra automaticamente pelos
  filhos do responsável logado.
- `GET /api/v1/comunicacao/avisos` — mural (responsável vê avisos `TODOS` e `RESPONSAVEIS`).
- `GET /api/v1/calendario/eventos?de=&ate=` — qualquer autenticado vê.
- `GET/POST /api/v1/matriculas` — responsável pode ver e criar pré-matrícula dos próprios
  filhos, cancelar a própria pré-matrícula, e fazer upload de documentos
  (`POST /api/v1/matriculas/{id}/documentos/{tipo}/arquivo`).
- `GET /api/v1/pessoas/alunos/{aluno_id}` — detalhe de um filho (RESPONSAVEL só o próprio).

**O que FALTA e você precisa adicionar no backend** (`backend/app/modules/pessoas/`):
não existe hoje um endpoint para o responsável **listar os próprios filhos** sem já saber o
`aluno_id` de cada um. Adicione:

- `GET /api/v1/pessoas/alunos/meus` — perfil `RESPONSAVEL` — retorna a lista de alunos
  vinculados ao usuário logado (reaproveite
  `pessoas.service.list_aluno_ids_do_usuario(db, user)` + a função que já existe pra montar
  `AlunoRead`/`AlunoListItem` de uma lista de ids — leia `pessoas/service.py` e
  `pessoas/repository.py` pra achar o jeito certo de fazer isso sem duplicar query).
  Siga o estilo de `turmas/router.py` → `GET /turmas/minhas` como referência de "endpoint
  'meu' que resolve a partir do usuário logado".
- Depois de mudar o backend, rode as migrations se necessário
  (`cd backend && .venv\Scripts\python.exe -m alembic upgrade head` — só precisa se você
  mudar um model, o que não deve ser o caso aqui, é só um endpoint novo).
- Teste que o backend ainda sobe: `cd backend && .venv\Scripts\python.exe -c "import app.main"`.
- **CORS**: adicione a porta do seu app novo (sugestão: `5174`) em
  `backend/app/core/config.py`, campo `cors_origins` (lista default) — senão o navegador
  bloqueia as chamadas. Reinicie o servidor do backend depois de mudar isso
  (`cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`, mate o
  processo antigo antes com `netstat -ano | grep ":8000"` + `taskkill //PID <pid> //F` se
  já estiver rodando).

## O que construir (frontend)

Crie um projeto novo em `portal-responsavel/` (irmão de `frontend/` e `backend/`, na raiz do
repo). Stack: **React + Vite + TypeScript + Tailwind v4** — mesma stack do `frontend/`
existente. Rode:

```
cd C:\Users\Leonardo\Desktop\software_escolar
npm create vite@latest portal-responsavel -- --template react-ts
cd portal-responsavel
npm install
npm install react-router-dom axios lucide-react
npm install -D tailwindcss @tailwindcss/vite
```

Configure `vite.config.ts` com o plugin do Tailwind e `server.port: 5174`. Configure
`.env` com `VITE_API_URL=http://localhost:8000/api/v1`.

**Reaproveite os padrões visuais do `frontend/` existente** (não copie arquivos, reimplemente
no projeto novo): layout com sidebar, cards `rounded-xl border border-slate-200 bg-white`,
cor primária `emerald-600`, inputs com uma classe `.input` global, componentes `Modal`,
`PageHeader`, estados de loading/erro. Dê uma lida em `frontend/src/App.tsx`,
`frontend/src/layout/AppLayout.tsx`, `frontend/src/pages/MatriculasPage.tsx` e
`frontend/src/api/client.ts` antes de começar, pra copiar o estilo de cliente HTTP
(axios com interceptor de refresh token) e o visual.

### Telas

1. **Login** — mesmo padrão do painel admin (`POST /auth/login`).
2. **Seletor de filho** (se o responsável tiver mais de um filho) — vem de
   `GET /pessoas/alunos/meus` (o endpoint novo que você vai criar). Se só tiver um filho,
   pule direto pro dashboard dele.
3. **Dashboard do filho** — resumo: próximos eventos do calendário, avisos recentes não
   lidos, status da matrícula, pendência financeira (se houver cobrança atrasada), média
   geral das notas.
4. **Boletim** — notas por disciplina/período + média + situação
   (`GET /notas/alunos/{id}/boletim`).
5. **Frequência** — histórico + percentual de presença
   (`GET /frequencia/alunos/{id}?de=&ate=`).
6. **Financeiro** — lista de cobranças do filho, com status (pendente/paga/atrasada)
   (`GET /financeiro/cobrancas?aluno_id={id}`). **Só leitura** — responsável não marca como
   paga, isso é função do financeiro da escola.
7. **Matrícula** — status da matrícula atual do filho, documentos pendentes, e formulário
   pra criar uma pré-matrícula nova / fazer upload de documento quando pedido.
8. **Mural de avisos** — `GET /comunicacao/avisos`, marcar como lido
   (`POST /comunicacao/avisos/{id}/lido`).
9. **Calendário** — `GET /calendario/eventos` (próximos eventos).
10. **Meu perfil** — dados do responsável + trocar senha (`POST /auth/me/senha`).

## Regras importantes

- Esse app é **só leitura + ações limitadas** (criar pré-matrícula, upload de documento,
  marcar aviso como lido, trocar a própria senha). Responsável **não** edita notas,
  frequência, cobranças nem avisos — essas telas nem devem existir aqui.
- Se o responsável tiver mais de um filho, todo o dashboard/boletim/frequência/financeiro
  precisa ser por filho selecionado (guarde o filho ativo em estado do React, com um seletor
  no topo/sidebar).
- Trate erro 404 da API como "sem acesso a esse aluno" (o backend já devolve 404 em vez de
  403 quando o responsável tenta ver um aluno que não é seu — é de propósito, não é bug).
- Não precisa de testes automatizados, não precisa de Docker, não precisa de CI. É MVP.

## Ao terminar

1. Rode `npm run build` no `portal-responsavel/` e confirme que não tem erro de tipo.
2. Suba o backend (se não estiver rodando) e o `npm run dev` do `portal-responsavel/`.
3. Cadastre um responsável + aluno de teste pelo painel admin (`http://localhost:5173`,
   login do admin acima) se não existir nenhum ainda, conceda acesso ao portal pra esse
   responsável (`POST /pessoas/responsaveis/{id}/acesso` ou pela tela "Responsáveis" do
   painel admin), e faça login real no portal novo pra confirmar que funciona de ponta a
   ponta.
