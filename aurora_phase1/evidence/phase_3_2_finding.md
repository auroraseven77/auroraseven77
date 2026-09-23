# Finding — Phase 3.2: Command Injection

## Status
CONFIRMED

## Origem
Fase 3 (chat antigo). Reconstruído no Bloco 7.

## Vulnerabilidade descoberta
Argumentos com metacaracteres de shell (`;`, `|`, `&`, backtick, `$(`)
podiam passar a validação de tipo e chegar ao subprocesso.

## Fix aplicado
`IsolatedExecutor._validate`:
- `command` deve estar em `allowed_commands`
- `args` são inspecionados contra `denied_patterns`
- Se algum arg casa com um pattern negado, `REJECTED_CONTENT_VIOLATION`

`subprocess.run(shell=False)` obrigatório. Args passados como lista.

## Implicação contratual
Argumentos são tokens de dados brutos. Nunca interpretados por shell.
Rejeição textual antes de subprocesso.

## Achado secundário
O `denied_patterns` bloqueia `;` mesmo em `python3 -c '...; ...'`. Isso
é comportamento correto (defesa), mas exige que o teste use arquivo
`.py` em vez de string com `;`.

## Artefatos
- `core/executor.py` — `_validate`
- `tests/test_executor.py::test_injection_in_args`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_executor.py::TestExecutor::test_injection_in_args`
