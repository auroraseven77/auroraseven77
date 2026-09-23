# aurora_phase1/evidence

Artefatos epistêmicos do projeto. Cada arquivo é um finding formal
com hash SHA-256 ancorado em `logs/tuu_ledger.jsonl`.

## Findings

### Fase 2 — Hardening (reconstruído do chat antigo)

| Finding | Status | Foco |
|---|---|---|
| `attack_1_finding.md` | CONFIRMED | Hash mismatch antes de efeito |
| `attack_2_finding.md` | CONFIRMED | Replay (aprovadas + rejeitadas) |
| `attack_3_finding.md` | CONFIRMED | Chain corruption com prefixo válido |
| `attack_4_finding.md` | CONFIRMED | Temporal anomaly (tick futuro) |
| `attack_5_finding.md` | CONFIRMED | Contract immutability |

### Fase 3 — Execução contida

| Finding | Status | Foco |
|---|---|---|
| `phase_3_1_finding.md` | CONFIRMED | Path traversal (duas camadas) |
| `phase_3_2_finding.md` | CONFIRMED | Command injection |
| `phase_3_3_finding.md` | DEFERRED | Runtime boundary (limite do host) |
| `phase_3_4_finding.md` | DEFERRED | Filesystem boundary (limite do host) |

### Fase 4 — Environment

| Finding | Status | Foco |
|---|---|---|
| `phase_4_finding.md` | CONFIRMED | Environment leakage |

### Achados novos (reconstrução)

| Finding | Status | Foco |
|---|---|---|
| `phase_6_finding.md` | CONFIRMED | Attestation: sentinel None |
| `phase_7_finding.md` | CONFIRMED | STERILE_ENV PATH portável |
| `phase_10_finding.md` | CONFIRMED | Payload suficiente para reconstrução |
| `phase_11_finding.md` | CONFIRMED | Circuit breaker e malformed |

## Construção do ledger

    cd auroraseven77-b12-audit
    python3 aurora_phase1/evidence/build_ledger.py

Produz `aurora_phase1/logs/tuu_ledger.jsonl` com:
- Bloco genesis
- Um bloco `ATTACK_FINDING_RECORDED` por finding (com hash SHA-256)

O topo da cadeia é o `master_attestation_hash`.

## Estrutura de um finding

    # Finding — <título>
    
    ## Status
    CONFIRMED | DEFERRED
    
    ## Origem
    <contexto>
    
    ## Vulnerabilidade/comportamento descoberto
    <descrição>
    
    ## Fix aplicado
    <descrição>
    
    ## Implicação contratual
    <regra load-bearing>
    
    ## Artefatos
    <arquivos>
    
    ## Verificação
    <como reproduzir>
