# Finding — Phase 3.3: Runtime Boundary

## Status
DEFERRED (limite conhecido)

## Origem
Fase 3 (chat antigo). Medição reconstruída no Bloco 7.

## Comportamento medido
Execução de comando permitido (`python3 -c`) que, durante runtime,
tenta escrever fora de `allowed_paths`. Resultado: `RUNTIME_ESCAPE_CONFIRMED`.

O subprocesso roda sem namespace de filesystem. Um `open()` com path
relativo escapa do cwd.

## Fix aplicado
Nenhum. Isso é limite do design, não bug.

O Centro garante:
- validação textual de comando e args
- env esterilizado (PATH, USER, HOME, LC_ALL, LANG)
- cwd restrito
- timeout com SIGKILL + exit_code 124
- captura de stdout/stderr com limite

O Centro NÃO garante:
- contenção de runtime fora do cwd
- bloqueio de syscalls
- isolamento de rede
- isolamento de filesystem

## Implicação contratual
Contenção de runtime requer sandboxing real (bwrap, nsjail, firejail).
Fica como Fase 8, dependente do host.

## Artefatos
- `core/executor.py`
