# Finding — Phase 4: Environment Leakage

## Status
CONFIRMED (fix aplicado)

## Origem
Fase 4 (chat antigo). Reconstruído no Bloco 7.

## Vulnerabilidade descoberta
Subprocesso herdava env do processo pai. Variáveis como SECRET_PAI,
tokens de API, paths privados vazavam para o comando executado.

## Fix aplicado
STERILE_ENV fixo:
- PATH derivado de sys.executable (portável)
- USER=aurora_sandbox
- HOME=/tmp/aurora_sandbox
- LC_ALL=C.UTF-8
- LANG=C.UTF-8

Nenhum env herdado. `subprocess.run(env=self._sterile_env)`.

O PATH é derivado de `sys.executable` para ser portável (descoberto no
Bloco 7 quando `PATH=/usr/bin:/bin` fixo falhava no Termux — ver
`phase_7_finding.md`).

## Implicação contratual
Subprocessos não herdam env do processo pai. Env é um dict mínimo
explicitamente construído.

## Artefatos
- `core/executor.py` — `STERILE_ENV`
- `tests/test_executor.py::test_env_sterile`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_executor.py::TestExecutor::test_env_sterile`
