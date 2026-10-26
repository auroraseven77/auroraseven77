# Finding — Attack 2: Replay

## Status
CONFIRMED

## Origem
Fase 2 (chat antigo). Reconstruído no Bloco 4.

## Vulnerabilidade descoberta
A TUU aceitava e reprocessava a mesma proposta repetidas vezes,
gerando blocos duplicados no ledger e avançando o tick artificialmente.
Replay de propostas rejeitadas também não era detectado.

## Fix aplicado
Índice em memória (`_seen_proposal_ids`) que rastreia toda proposta
processada — aprovada ou rejeitada. O índice é populado no boot via
`_hydrate_from_ledger()` lendo todos os blocos do ledger.

Portão 1 de `evaluate_proposal`: se `proposal_id in _seen_proposal_ids`,
retorna `REJECTED_REPLAY` sem qualquer efeito colateral.

Decisão arquitetural: **replay de rejeitadas conta como ataque**. Uma
proposta vista uma vez é memória epistêmica do Centro.

## Implicação contratual
Memória epistêmica total. O Centro lembra de tudo o que viu, não apenas
do que aceitou. O índice de replay sobrevive a reconstruções porque é
reconstruído do ledger.

## Artefatos
- `core/tuu.py` — `_hydrate_from_ledger`, portão 1
- `core/reconstruct.py` — `seen_proposal_ids` na reconstrução
- `tests/test_tuu.py::test_replay`, `test_replay_after_hydrate`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_tuu.py::TestTUU::test_replay`

## Próximo finding depende de
`attack_3` assume que o ledger é consultável como fonte de verdade.
