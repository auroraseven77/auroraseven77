# Finding — Phase 13.1: Branch protection

## Status
CONFIRMED

## Origem
Avaliação pós-reconstrugção (Bloco 13).

## Comportamento descoberto
`main` estava sem branch protection. Tês pushes diretos consecutivos
foram aceitos sem PR nem checks, mesmo com 4 workflows configurados
para rodar em `push` para `main`.

Além disso, havia dois rulesets paralelos (main-1, main-2)
que sobrepunham a branch protection e exigiam 1 aprovação — bloqueando
qualquer merge em repo solo.

## Fix aplicado
Duas ações:

1. Ativar branch protection em `main` via `gh api -X PUT:
   - required_status_checks.strict: true
   - required_status_checks.contexts: 7 checks
   - enforce_admins: true
   - required_pull_request_reviews.required_approving_review_count: 0
   - required_conversation_resolution: true
   - allow_force_pushes: false
   - allow_deletions: false

2. Deletar os rulesets redundantes `main-1` e `main-2` via `gh api -X DELETE`.

## Prova factual

**Push direto rejeitado:**
```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - 7 of 7 required status checks are expected.
remote: - Changes must be made through a pull request.
```

**Merge sem PR rejeitado:**
```
X Pull request is not mergeable: the base branch policy prohibits the merge.
```

**PR #9 com 7/7 checks → merge permitido:**
```
✓ Merged pull request #9 from auroraseven77/revert-test-bp
```

**Estado pós-selagem:**
- `main` = `57845e3`
- rulesets: vazio
- protection: 7 checks + enforce_admins + require_pr

## Implicacao contratual
Toda alteração em `main` requer PR com os 7 checks verdes. Push direto é impossível, inclusive para admin. Isso é invariante operacional.

## Artefatos
- Configuração GitHub (não versionada)
- Histórico de commits mostra os 3 testes + 3 reverts

## Verificação
```
gh api repos/auroraseven77/auroraseven77/branches/main/protection --jq '{
  required_checks: .required_status_checks.contexts,
  enforce_admins: .enforce_admins.enabled,
  require_pr: (.required_pull_request_reviews != null)
}'
```