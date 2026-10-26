# Finding — Attack 4: Temporal Anomaly

## Status
CONFIRMED

## Origem
Fase 2 (chat antigo). Reconstruído no Bloco 4.

## Vulnerabilidade descoberta
Propostas com `timestamp_logical` de ticks futuros arbitrários eram
aceitas, distorcendo o fluxo causal.

## Fix aplicado
Portão 3 de `evaluate_proposal`: `proposal_tick > current_tick + max_future_ticks`
é rejeitado com `REJECTED_TEMPORAL_ANOMALY`. `max_future_ticks = 1` no
contrato `tuu_policy.json`.

Também rejeita ticks negativos se `allow_negative_ticks = false`.

## Implicação contratual
Consistência causal obrigatória. Nenhuma proposta pode referenciar um
tick que ainda não aconteceu (além do horizonte permitido).

## Artefatos
- `core/tuu.py` — portão 3
- `tests/test_tuu.py::test_temporal_anomaly`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_tuu.py::TestTUU::test_temporal_anomaly`

## Próximo finding depende de
`attack_5` assume que o tick é consistente.
