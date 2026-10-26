# Finding — Phase 3.4: Filesystem Boundary

## Status
DEFERRED (limite conhecido)

## Origem
Fase 3 (chat antigo). Complementa phase_3_3.

## Comportamento medido
Escrita em path absoluto fora do sandbox via `python3 -c` permitido.
Resultado: `RUNTIME_ESCAPE_CONFIRMED`.

## Fix aplicado
Nenhum. Depende de sandboxing real (Fase 8).

## Implicação contratual
Mesmo que phase_3_3. A contenção do executor cobre validação de
cwd, não contenção de chamadas `open()` arbitrárias.

## Artefatos
- `core/executor.py`
