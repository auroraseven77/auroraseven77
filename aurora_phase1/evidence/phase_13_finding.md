# Finding — Phase 13: canonical_json e complex

## Status
CONFIRMED (achado novo, integração b1_motor)

## Origem
Integração real do `quantum_bridge` com o `b1_motor` canônico.

## Comportamento descoberto
Três bugs latentes foram expostos quando o bridge começou a usar
coeficientes complexos reais:

1. `quantum_bridge.py` usava `json.dumps(obs_data)` sem `default=str`
   para checar `denied_patterns`. Complex não é JSON-serializable.

2. `quantum_bridge._validate` usava `isinstance(coefficient, (int, float))`
   que rejeita `complex` como `REJECTED_MALFORMED`.

3. `crypto.canonical_json` (usado por `hash_object`) não serializava
   complex. Este é o mais sério: o bug estava latente desde o Bloco 1
   porque nenhum teste unitário chamava `hash_object` com complex.

## Fix aplicado
- `quantum_bridge.py`: `json.dumps(..., default=str)` na checagem
- `quantum_bridge.py`: `isinstance(coefficient, (int, float, complex))`
- `crypto.py`: encoder `_json_default` que converte complex para string
  determinística `"(re+imj)"`

## Implicação contratual
`hash_object` deve lidar com qualquer tipo numericamente válido,
incluindo complex. Coeficientes complexos são parte do domínio do
`b1_motor.PauliTerm` e devem ser serializáveis.

## Artefatos
- `core/crypto.py` — `_json_default`
- `core/quantum_bridge.py` — `_validate`, `execute_measurement`
- `tests/test_quantum_bridge_b1_integration.py` — 7 testes

## Verificação
`python3 -m unittest aurora_phase1/tests/test_quantum_bridge_b1_integration.py`

## Nota
Integração real expõe o que teste unitário esconde. Este é o terceiro
bug real (após phase_6 e phase_7) que emergiu durante a reconstrução.
