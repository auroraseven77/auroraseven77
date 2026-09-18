# TUU Panel

Painel e contrato de mensagens do motor TUU (Temporal Unified Unit).

## Contrato

O protocolo usa mensagens discriminadas por `type` e payloads Pydantic tipados.

### Estados

`received` → `analyzing` → `predicting` → `superposition` → `resolving` → `collapsed` → `executing` → `completed`

### Mensagens

- `intent` → `IntentPayload`
- `command` → `CommandPayload`
- `state` → `StatePayload`

Envelope comum:

- `type`
- `session_id`
- `request_id`
- `timestamp`
- `observability`
- `payload`

### Segurança

`AuthorizationPolicy.status` inicia em `pending` e aceita:

- `pending`
- `approved`
- `rejected`

`collapsed` não implica autorização automática para execução.

## Pydantic v2

A união é explicitamente discriminada pelo campo `type` e validada fora do FastAPI com `TypeAdapter`.

```python
TUUMessage = Annotated[
    Union[IntentMessage, CommandMessage, StateMessage],
    Field(discriminator="type"),
]

TUUAdapter = TypeAdapter(TUUMessage)

validated_message = TUUAdapter.validate_python(raw_data)
validated_message = TUUAdapter.validate_json(raw_text)
```

## Arquitetura

```text
JSON bruto
   ↓
TUUAdapter
   ↓
discriminação por type
   ↓
payload tipado
   ↓
máquina de estados
   ↓
event bus
   ↓
swarm / agentes
   ↓
consenso
   ↓
autorização
   ↓
execução
```

Responsabilidades:

**Agentes propõem → máquina de estados controla transições → autorização controla execução.**

## Observabilidade

`ObservabilityMetadata` suporta:

- `trace_id`
- `parent_id`
- `started_at`
- `completed_at`
- `duration_ms`
- `resource_usage`
- `error_code`

## Exemplo

```json
{
  "type": "command",
  "session_id": "sess_001",
  "request_id": "req_001",
  "timestamp": "2026-09-18T12:30:00Z",
  "payload": {
    "intent": "pkg_list",
    "args": [],
    "execution_id": "exec_001"
  }
}
```
