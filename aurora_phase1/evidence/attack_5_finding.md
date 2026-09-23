# Finding — Attack 5: Contract Immutability

## Status
CONFIRMED

## Origem
Fase 2 (chat antigo). Reconstruído no Bloco 6.

## Vulnerabilidade descoberta
Ausência de atestado formal contra mutação de contratos. Um agente
podia alterar `contracts/*.json` em disco e o mundo não detectaria.

## Fix aplicado
`AttestationEngine.seal()` no boot: computa SHA-256 de cada arquivo
`.json` em `contracts/`. Armazena em `_attestation: dict[filename, hash]`.

`verify_disk_integrity()` recomputa e compara. Detecta modificação,
deleção, adição.

`boot_verify(degraded=False)` levanta `RuntimeError` em falha. Com
`degraded=True`, aceita mas o mundo entra em modo degradado.

## Decisão de contrato
Opção A (hard stop) por default. Opção B (`--degraded`) explícita.
Opção C (só alerta) banida — seria decorativa.

## Implicação contratual
Contratos são imutáveis durante a vida do mundo. Adulteração em disco
é detectada no próximo boot.

## Achado secundário (Bloco 6)
`seal()` de diretório vazio produzia `{}`, e `verify_disk_integrity`
interpretava `{}` como "nunca selado". Fix: sentinel `None` distingue
"nunca selado" de "selado vazio".

## Artefatos
- `core/attestation.py`
- `tests/test_attestation.py`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_attestation.py`
