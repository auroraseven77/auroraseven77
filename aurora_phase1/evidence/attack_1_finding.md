# Finding — Attack 1: Hash Mismatch

## Status
CONFIRMED

## Origem
Fase 2 (chat antigo do AI Studio, container resetado). Achado preservado
por reconstrução documental.

## Vulnerabilidade descoberta
A TUU da Fase 1 avançava o relógio lógico e escrevia um bloco no ledger
**antes** de validar o hash da proposta. Uma proposta forjada conseguia
induzir efeito colateral (mutação de tick e poluição do ledger) mesmo
sendo rejeitada depois.

## Fix aplicado
Pré-validação criptográfica a frio no topo de `evaluate_proposal`.
O hash é validado antes de qualquer tick, contador ou escrita no ledger.

Ordem dos portões (Bloco 4):
1. Replay check
2. Hash check
3. Temporal check
4. Contract check
5. Content check
6. Aprovação + sedimentação

## Implicação contratual
Validação **precede** efeito. Nenhum portão pode avançar o estado do
mundo antes de sua validação. Isso é load-bearing.

## Artefatos
- `core/tuu.py` — `evaluate_proposal`
- `tests/test_tuu.py::test_hash_mismatch`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_tuu.py::TestTUU::test_hash_mismatch`
Esperado: `REJECTED_HASH_MISMATCH`, ledger inalterado, tick congelado.

## Próximo finding depende de
`attack_2` herda a ordem dos portões (replay antes de hash).
