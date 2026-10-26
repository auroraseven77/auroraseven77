# Finding — Phase 11: Circuit breaker e malformed

## Status
CONFIRMED (achado novo, Bloco 11)

## Origem
Formalização dos testes, Bloco 11.

## Comportamento descoberto
O teste `test_circuit_breaker_opens` falhou inicialmente porque usava
`evaluate_proposal({"garbage": i})` para acionar rejeições. Mas
malformed tem `count_invalid=False` — não conta para o circuit breaker.

Isso é design, não bug. Malformed é lixo de entrada, não ataque
real. Se malformed contasse, um cliente enviando JSON inválido
repetidamente abriria o circuito do mundo — negação de serviço trivial.

## Fix aplicado
Corrigir o teste para usar replays (que contam) em vez de
malformed.

## Implicação contratual
Circuit breaker conta apenas rejeições de propostas estruturalmente
válidas. Malformed é descartado a frio sem contar.

## Achado secundário
`ledger.count()` não fechava o arquivo. Fix: `with self.path.open()`.

## Artefatos
- `tests/test_tuu.py::test_circuit_breaker_opens`
- `core/ledger.py::count`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_tuu.py::TestTUU::test_circuit_breaker_opens`
