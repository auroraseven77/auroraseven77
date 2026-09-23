# Finding — Attack 3: Chain Corruption

## Status
CONFIRMED

## Origem
Fase 2 (chat antigo). Reconstruído no Bloco 5.

## Vulnerabilidade descoberta
O `WorldReconstructor` original descartava **todo** o estado ao
encontrar um bloco com hash anterior inválido. Perdia o prefixo válido.

## Fix aplicado
Parada estrita: o reconstructor valida bloco a bloco. Ao encontrar
quebra no seq N, retorna o estado reconstruído até seq N-1.

`audit_chain()` retorna estrutura:
- `chain_integrity: bool`
- `failed_seq: int | None`
- `last_valid_seq: int`
- `diagnostic: str`

## Implicação contratual
O mundo tem memória parcial válida. Não é tudo-ou-nada. O reconstructor
recusa avançar além do último bloco íntegro.

## Artefatos
- `core/ledger.py` — `audit_chain`
- `core/reconstruct.py` — parada estrita
- `tests/test_ledger.py::test_chain_corruption_detected`
- `tests/test_reconstruct.py::test_strict_stop_on_corruption`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_reconstruct.py::TestReconstruct::test_strict_stop_on_corruption`

## Próximo finding depende de
`attack_4` assume que o ledger é auditável por prefixo.
