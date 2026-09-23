# Finding — Phase 6: Attestation sentinel None

## Status
CONFIRMED (achado novo, Bloco 6)

## Origem
Reconstrução do Bloco 6.

## Comportamento descoberto
`AttestationEngine.seal()` de um diretório `contracts/` vazio produz
`_attestation = {}`. `verify_disk_integrity()` interpretava `{}` como
"nunca selado" e retornava `integrity=False` mesmo após `seal()`.

Isso é semântica errada: um diretório vazio selado é válido ("não há
contratos a proteger").

## Fix aplicado
Inicializar `_attestation = None` (sentinel distingue "nunca selado"
de "selado vazio"). `verify_disk_integrity` e `master_attestation_hash`
checam `is None` em vez de `not _attestation`.

## Implicação contratual
Vazio não é o mesmo que ausente. O contrato deve distinguir "nunca foi
selado" de "selado com zero contratos". São estados epistêmicos
diferentes.

## Artefatos
- `core/attestation.py`
- `tests/test_attestation.py::test_empty_dir_ok`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_attestation.py::TestAttestation::test_empty_dir_ok`
