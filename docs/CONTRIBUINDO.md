# Como contribuir

## Fluxo

1. **Pegue uma issue** (ou crie uma descrevendo o problema/funcionalidade) e se atribua.
2. **Crie uma branch** a partir da `main` atualizada:
   ```bash
   git switch main && git pull
   git switch -c feat/matricula-upload
   ```
   Padrão: `<tipo>/<descricao-curta>`, com tipos `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `ci`.
3. **Desenvolva em commits pequenos** no padrão Conventional Commits:
   `feat(matricula): permitir upload de documentos`.
4. **Rode tudo localmente antes de abrir o PR**:
   ```bash
   cd backend
   uv run ruff check . && uv run ruff format --check . && uv run mypy app tests && uv run pytest
   cd ../frontend
   npm run lint && npm run typecheck && npm test && npm run build
   ```
5. **Abra o Pull Request** para a `main` com uma descrição do que mudou, por que mudou e como
   testar. Relacione a issue (`Closes #12`).
6. **Review**: pelo menos 1 aprovação de outra pessoa do time. Quem revisa confere o checklist
   abaixo, roda o código se necessário e comenta com respeito e objetividade.
7. **Merge** com *squash* depois do CI verde e da aprovação. Apague a branch.

## Checklist do PR

Copie no corpo do PR e marque:

```markdown
- [ ] Segui o padrão router → service → repository e as regras do docs/ARQUITETURA.md
- [ ] Regras de negócio, permissões e checagem de propriedade estão no BACK-END
- [ ] Nenhum campo sensível (status, valor, desconto, role, responsavel_id, pago) é aceito do cliente
- [ ] Todo arquivo novo tem teste correspondente (tests/.../test_<arquivo>.py)
- [ ] Testes de router cobrem: caminho feliz, 401, 403, acesso a dado de outra família (404) e 422
- [ ] Criei migration (se alterei models) e revisei o arquivo gerado
- [ ] Ações sensíveis registram auditoria (record_audit)
- [ ] Atualizei docs/modulos/<modulo>.md (endpoints, regras, máquina de estados)
- [ ] Lint, mypy e testes passam localmente (back e front)
- [ ] Não commitei segredos (.env, chaves de API)
```

## Boas práticas

- Um PR deve ter um assunto só. PRs pequenos são revisados mais rápido e com mais qualidade.
- Não desative testes de arquitetura para "fazer passar". Se a regra não serve, discuta e
  altere o `docs/ARQUITETURA.md` no mesmo PR.
- Dados de exemplo nos testes e no seed devem ser **fictícios**. Nunca use dados reais de
  alunos ou famílias (LGPD).
- Dúvida de arquitetura? Abra uma issue com o rótulo `discussão` antes de codar.
