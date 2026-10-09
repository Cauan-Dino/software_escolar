# Semeando — Orientação a Objetos no sistema

Material de apoio para a apresentação de POO. Tudo abaixo aponta para código real do
`backend/` (Python 3.12 + FastAPI + SQLAlchemy).

> **Ponto de honestidade antes de apresentar:** o projeto usa um estilo *modular em camadas*
> (router → service → repository). Os `service.py` e `repository.py` são **funções de módulo**,
> não classes. A orientação a objetos aparece com força nos **models, exceções, mixins,
> máquina de estados, value objects e interfaces**. Por isso este documento tem duas partes:
> o que **já é** OO (para mostrar) e o que **pode virar** OO (para propor/implementar).

---

## Parte 1 — O que já é orientado a objetos

### 1. Herança e hierarquia de exceções
`app/core/exceptions.py`

```
Exception
└── AppError                 (status_code, default_code, default_detail)
    ├── UnauthorizedError    401
    ├── ForbiddenError       403
    ├── NotFoundError        404
    ├── ConflictError        409
    │   └── InvalidTransitionError
    ├── BusinessRuleError    422
    ├── RateLimitError       429
    └── LLMIndisponivelError 502   (módulo assistente)
```

- **Herança:** cada erro só redefine atributos de classe; o construtor vem de `AppError`.
- **Polimorfismo:** um único handler (`_app_error_handler`) trata *qualquer* `AppError` lendo
  `exc.status_code`. Subclasses novas funcionam sem alterar o handler.
- **Princípio aberto/fechado:** estende-se criando classes, sem modificar código existente.

### 2. Herança múltipla / Mixins (composição de comportamento)
`app/core/database.py` e `app/modules/pessoas/models.py`

```python
class Aluno(TimestampMixin, SoftDeleteMixin, Base): ...
class Cobranca(Base): ...
class Matricula(TimestampMixin, Base): ...
```

- `TimestampMixin` adiciona `created_at`/`updated_at`; `SoftDeleteMixin` adiciona `deleted_at`.
- Cada model escolhe os comportamentos que quer, sem duplicar colunas.
- `Base(DeclarativeBase)` é a classe-mãe de todos os models (herança + mapeamento objeto-relacional).

### 3. Classes genéricas (parametrização de tipo)
`app/shared/state_machine.py`

```python
class StateMachine[S: Enum]:
    def can(self, current: S, target: S) -> bool: ...
    def ensure(self, current: S, target: S) -> None: ...
    def targets(self, current: S) -> frozenset[S]: ...
    def is_terminal(self, state: S) -> bool: ...
```

- Um objeto, uma responsabilidade: *quais transições de status são válidas*.
- Reutilizável para qualquer `Enum`. Hoje existe uma instância, `MATRICULA_FSM`
  (`PRE_MATRICULA → EM_ANALISE → APROVADA → AGUARDANDO_PAGAMENTO → ATIVA`).
- **Encapsulamento:** o dicionário de transições é privado (`_transitions`) e imutável
  (`frozenset`); só se acessa via métodos.
- Também há `Page[T]` em `app/shared/pagination.py` (modelo genérico).

### 4. Encapsulamento e estado interno: `RateLimiter`
`app/core/rate_limit.py`

- Atributos privados (`_hits`, `_lock`, `_clock`) e API pública mínima (`hit`, `reset`).
- **Injeção de dependência:** o relógio entra pelo construtor (`clock=time.monotonic`), por isso
  os testes passam um relógio falso.
- **Atributo e método de classe:** `_instances` + `@classmethod reset_all()`.

### 5. Interface / contrato: `LLMClient` (Protocol) e `DeepSeekClient`
`app/modules/assistente/llm.py`

```python
class LLMClient(Protocol):
    def chat(self, messages, tools) -> LLMResponse: ...

class DeepSeekClient:   # implementação concreta
    def chat(self, messages, tools) -> LLMResponse: ...
```

- **Abstração + polimorfismo:** o service depende de `LLMClient`, não do DeepSeek. Nos testes
  entra um cliente falso; trocar de provedor (OpenAI, Claude…) é criar outra classe.
- É o **Princípio da Inversão de Dependência** (o "D" do SOLID) em ~10 linhas.

### 6. Objetos de valor imutáveis (`@dataclass(frozen=True)`)
| Classe | Arquivo | Papel |
|---|---|---|
| `CurrentUser` | `core/deps.py` | identidade autenticada (com `@property is_staff`) |
| `StoredFile` | `shared/storage.py` | resultado de salvar um arquivo |
| `ToolCall`, `LLMResponse` | `assistente/llm.py` | mensagens do LLM |
| `CobrancaPaga` | `financeiro/schemas.py` | evento de domínio |
| `RefreshTokenData` | `core/security.py` | dados do refresh token |

Imutáveis → sem efeito colateral, seguros para passar entre camadas.

### 7. Enums com comportamento
`app/shared/serie.py`, `app/core/roles.py`

```python
class Serie(StrEnum):
    ANO_1 = "ANO_1"
    @property
    def label(self) -> str: ...
    @property
    def segmento(self) -> Segmento: ...
```

`Role`, `Serie`, `Segmento`, `Turno`, `StatusMatricula`, `StatusCobranca`… (16 enums). Elimina
"strings mágicas" e carrega regras junto do tipo.

### 8. Herança nos schemas (DTOs)
`app/shared/schemas.py`

- `InputSchema` (`extra="forbid"`) → base de **todo** schema de entrada.
- `OutputSchema` (`from_attributes=True`) → base de **todo** schema de saída.
- Cada `XxxCreate`, `XxxUpdate`, `XxxRead` herda e especializa. Regra de segurança
  (rejeitar campos inesperados) fica em **um** lugar.

### 9. Associações entre objetos (modelo de domínio)
Diagrama de classes (resumo):

```
User 1───0..1 Aluno / Responsavel / Professor / Funcionario
Aluno 1───* ResponsavelAluno *───1 Responsavel      (associação N:N com atributos)
Aluno 1───* Matricula *───1 Turma
Turma 1───* TurmaProfessor *───1 Professor
Matricula 1───* DocumentoMatricula
Aluno 1───* Cobranca ;  Aluno 1───* Bolsa
Aviso 1───* LeituraAviso
```

`ResponsavelAluno` é uma **classe de associação** (parentesco, responsável financeiro,
pode buscar). Ótimo exemplo para a aula: relação N:N que carrega dados próprios.

### 10. Padrões de projeto presentes
| Padrão | Onde | Observação |
|---|---|---|
| **Strategy / Dependency Inversion** | `LLMClient` | trocar provedor sem mexer no service |
| **State** (versão tabela) | `StateMachine` / `MATRICULA_FSM` | transições válidas centralizadas |
| **Observer / Pub-Sub** | `core/events.py` + `CobrancaPaga` | **ver ressalva abaixo** |
| **Repository** | `*/repository.py` | isola o acesso ao banco |
| **Mixin** | `TimestampMixin`, `SoftDeleteMixin` | composição de comportamento |
| **Dependency Injection** | `Depends(get_db)`, `Depends(require_roles(...))` | FastAPI injeta sessão e usuário |
| **DTO** | `*Create/*Read` | separa API de modelo de banco |

> **Ressalva sobre o Observer:** `events.publish(...)` já é chamado ao pagar uma cobrança,
> mas hoje **nenhum módulo se inscreve** (`subscribe`) no evento — o `main.py` tem só o ponto
> de ligação. Apresente como "mecanismo pronto, ainda sem assinante" ou implemente o
> assinante (ativar a matrícula ao pagar), o que fecha o exemplo.

---

## Parte 2 — Onde dá para "orientar a objeto" (refatorações propostas)

Estas são as oportunidades reais; cada uma é pequena e demonstrável.

### A. Superclasse `Pessoa` (maior ganho, mais didático)
Hoje `Aluno`, `Responsavel`, `Professor` e `Funcionario` repetem `id`, `user_id`, `nome`,
`cpf`, `email`, `telefone`. Proposta:

```python
class Pessoa(TimestampMixin, SoftDeleteMixin, Base):
    __abstract__ = True
    id; user_id; nome; cpf; email; telefone

class Aluno(Pessoa): data_nascimento ...
class Responsavel(Pessoa): ...
class Professor(Pessoa): formacao ...
class Funcionario(Pessoa): cargo, tipo ...
```

Demonstra **herança, generalização e classe abstrata** num domínio que todo mundo entende.
Pode-se acrescentar um método polimórfico, ex.: `def papel(self) -> Role`.
> Atenção: `Aluno` não tem `email/telefone` hoje (aluno menor de idade). Opção: manter em
> `Aluno` apenas o que existe, ou separar `PessoaContato`.

### B. Regras de negócio dentro das entidades (tirar do service)
Hoje a lógica fica em funções (`_atualizar_atraso`, `calcular_bolsa_ativa`, `_transition`).
Mover para **métodos do objeto** (modelo rico em vez de anêmico):

```python
class Cobranca(Base):
    def esta_vencida(self, hoje: date) -> bool: ...
    def marcar_paga(self, quando: datetime) -> None:   # valida status, altera estado
    def aplicar_desconto(self, percentual: Decimal) -> None: ...

class Matricula(Base):
    def aprovar(self) -> None:  MATRICULA_FSM.ensure(self.status, S.APROVADA); ...
    def cancelar(self, motivo: str) -> None: ...

class Turma(Base):
    @property
    def vagas_disponiveis(self) -> int: ...
    def tem_vaga(self) -> bool: ...
```

Argumento para a banca: **encapsulamento de invariantes** — ninguém altera `status` sem passar
pela regra.

### C. Services e repositories como classes
Transformar `matricula/service.py` (481 linhas de funções) em:

```python
class MatriculaService:
    def __init__(self, db: Session, repo: MatriculaRepository, pessoas: PessoaService): ...
    def aprovar(self, matricula_id: int, user: CurrentUser) -> MatriculaRead: ...
```

Ganhos: dependências explícitas no construtor (hoje são `import` de módulo), fácil trocar o
repositório por um falso em teste, e permite **herança** (`BaseRepository[T]` genérico com
`get/add/list/delete` reaproveitado por todos os módulos — hoje cada `repository.py` repete
`_paginate`, `add`, `get_*`).

### D. Calculo de preço/bolsa como Strategy
`calcular_bolsa_ativa` e a geração de mensalidades podem virar:

```python
class RegraDesconto(Protocol):
    def aplicar(self, valor: Decimal, aluno: Aluno) -> Decimal: ...

class DescontoBolsa(RegraDesconto): ...
class DescontoIrmaos(RegraDesconto): ...      # exemplo de extensão
class DescontoPontualidade(RegraDesconto): ...
```

Mostra **polimorfismo** e aberto/fechado: nova regra = nova classe.

### E. Notificações / Storage como interfaces
- `storage.py` já diz "troque por S3/MinIO mantendo as mesmas funções" → transformar em
  `class ArmazenamentoArquivos(Protocol)` com `LocalStorage` e `S3Storage`.
- `Notificador(Protocol)` com `EmailNotificador`, `WhatsAppNotificador` para avisos.

### F. Relatórios com herança/Template Method
`class Relatorio(ABC)` com `gerar()` chamando `coletar()`, `formatar()` (abstratos);
`RelatorioBoletim`, `RelatorioFinanceiro` implementam. Bom exemplo de **classe abstrata**.

---

## Parte 3 — Roteiro sugerido (≈ 10–12 min)

1. **Contexto (1 min):** sistema escolar, monolito modular, 10 módulos.
2. **Modelo de domínio (2 min):** diagrama de classes da seção 9 — destaque `ResponsavelAluno`.
3. **Pilares com código real (5 min):**
   - Herança: `AppError` e subclasses + um handler só (polimorfismo).
   - Composição/mixins: `Aluno(TimestampMixin, SoftDeleteMixin, Base)`.
   - Encapsulamento: `RateLimiter` e `StateMachine`.
   - Abstração: `LLMClient` ↔ `DeepSeekClient`.
4. **Padrões de projeto (1–2 min):** tabela da seção 10.
5. **Evolução (2 min):** `Pessoa` abstrata + `Cobranca.marcar_paga()` — antes/depois.
6. **Conclusão:** OO não é só `class`; é onde as regras moram e quem depende de quem.

### Demo ao vivo sugerida
- Tentar mudar status de matrícula de `ATIVA` → `PRE_MATRICULA` pela API e mostrar o
  `409 INVALID_TRANSITION` (a hierarquia de exceções + `StateMachine` trabalhando juntas).
- Chamar um endpoint sem permissão e mostrar o `403 FORBIDDEN` no mesmo formato de erro.

## Possíveis perguntas da banca
- *"Por que service/repository são funções e não classes?"* → decisão do projeto para manter
  simplicidade; a Parte 2-C mostra a migração e o que se ganha (DI, herança de repositório).
- *"Onde está o polimorfismo?"* → handler de `AppError`, `LLMClient`, e (proposto) `RegraDesconto`.
- *"Isso é modelo anêmico?"* → hoje parcialmente sim; Parte 2-B é exatamente a correção.
