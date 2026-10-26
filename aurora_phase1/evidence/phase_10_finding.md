# Finding — Phase 10: Payload insuficiente para reconstrução

## Status
CONFIRMED (achado novo, Bloco 10)

## Origem
Reconstrução do Bloco 10, durante implementação do `demo_phase1.py`.

## Comportamento descoberto
A Prova 5 (reconstrução tabula rasa) falhou. Os hashes divergiram:

    original (TUU RAM):       50174cbc4d90058002...
    reconstruído (ledger):    04abfba9f5169e2af8...

Causa: o bloco `PROPOSAL_PROCESSED_AND_APPROVED` gravava apenas
`proposal_id`, `agent_id`, `action_type`, `state_hash`. Não gravava
`observation_data` nem `hypothesis`.

O reconstructor não podia preencher `observations[key]["data"]` nem
`hypotheses_sedimented`, então o `state` reconstruído era diferente do
`state` em RAM.

## Fix aplicado
- `core/tuu.py::_approve`: enriquecer o payload com `observation_data`
  e `hypothesis`.
- `core/reconstruct.py::_apply_block`: consumir esses campos para
  reconstruir `observations[key]["data"]` e `hypotheses_sedimented`.

Após o fix: divergência 0.00%.

## Implicação contratual
O ledger deve carregar informação suficiente para reconstruir todo
o estado do mundo. Se um campo do `world_state` não pode ser derivado
dos blocos, o mundo não é reconstruível. Isso é invariante.

Cada novo evento do ledger deve declarar quais campos do `world_state`
ele reconstrói.

## Artefatos
- `core/tuu.py` — `_approve`
- `core/reconstruct.py` — `_apply_block`
- `aurora_phase1/demo_phase1.py` — Prova 5
- `tests/test_reconstruct.py::test_state_hash_matches_tuu`

## Verificação
`python3 aurora_phase1/demo_phase1.py` — Prova 5 deve mostrar
divergência 0.00%.

## Nota
Este é o achado mais importante da reconstrução: expõe que a
auditabilidade do mundo depende de cada evento do ledger carregar
informação suficiente. Sem a Prova 5, isso ficaria invisível.
