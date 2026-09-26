# Prediction Commitment Contract
**Status:** DRAFT / BLOCK 1
**Scope:** `aurora_phase1/cognitive_poc`

## 1. Objective

O Prediction Commitment registra uma previsão como um estado epistemicamente comprometido.

## 2. Canonical Commitment Object

O conteúdo criptograficamente comprometido é exclusivamente:

```json
{
  "hypothesis_id": "<string>",
  "prediction": <json-value>,
  "conditions": <json-value>,
  "timestamp_logical": <integer>
}
```

Os quatro campos acima são obrigatórios.

## 3. Canonicalization

A canonicalização deve utilizar exclusivamente:

`aurora_phase1.core.crypto.hash_object()`

O Cognitive Core não implementa seu próprio mecanismo de hashing ou canonicalização.

## 4. Prediction Hash

O compromisso é definido por:

`prediction_hash = hash_object(commitment_object)`

O resultado deve possuir 64 caracteres hexadecimais.

## 5. Immutability

Qualquer alteração em:

- `hypothesis_id`
- `prediction`
- `conditions`
- `timestamp_logical`

deve produzir um `prediction_hash` diferente.

O compromisso original nunca é sobrescrito.

## 6. Ledger Integration

O registro utiliza a infraestrutura existente:

`aurora_phase1.core.ledger.Ledger.add_block()`

O tipo de evento será:

`PREDICTION_COMMITTED`

Payload mínimo:

```json
{
  "prediction_hash": "<sha256>",
  "commitment": {
    "hypothesis_id": "<string>",
    "prediction": <json-value>,
    "conditions": <json-value>,
    "timestamp_logical": <integer>
  }
}
```

## 7. Hash Separation

`prediction_hash` e `entry_hash` possuem funções diferentes.

Os campos do Ledger não fazem parte do `prediction_hash`:

- `seq`
- `tick`
- `prev_hash`
- `entry_hash`
- metadata criada pelo Ledger

Não deve existir hashing circular.

## 8. Verification

A verificação recalcula:

`recomputed_hash = hash_object(commitment_object)`

Se o hash recalculado for igual ao hash armazenado, o resultado é `COMMITMENT_VALID`.

Se forem diferentes, o resultado é `COMMITMENT_HASH_MISMATCH`.

Estruturas inválidas produzem `COMMITMENT_MALFORMED`.

## 9. Authority Boundary

O Cognitive Core pode formar e propor um compromisso.

Ele não possui autoridade para:

- EXECUTE
- AUTHORIZE
- WRITE_LEDGER_DIRECTLY
- BYPASS_TUU

## 10. Non-Goals

Block 1 não implementa:

- Bayesian inference
- belief updates
- learning
- error attribution
- active inference
- LLM integration
- quantum integration
- action authorization
- alterações no TUU
- alterações no Ledger
- novo sistema criptográfico
- nova persistência

## 11. Required Tests

Devem existir testes para:

1. hash determinístico;
2. mutação da prediction;
3. mutação das conditions;
4. mutação do hypothesis_id;
5. mutação do timestamp lógico;
6. independência da ordem das chaves;
7. rejeição de valores numéricos inválidos pela API `hash_object()`;
8. integridade do Ledger;
9. compatibilidade com reconstruction;
10. imutabilidade do compromisso original.

## 12. Acceptance Criteria

- schema definido;
- hashing definido;
- separação entre prediction_hash e entry_hash;
- evento definido;
- regra anti-circularidade definida;
- imutabilidade definida;
- estados de verificação definidos;
- autoridade definida;
- testes definidos;
- nenhuma implementação de produção neste bloco.
