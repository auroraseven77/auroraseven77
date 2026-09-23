# aurora_phase1 — Roadmap selado

Roadmap completo do laboratório multiagente reconstruído no repo
`auroraseven77/auroraseven77`, subdiretório `aurora_phase1/`.

## Estado final

11 de 12 blocos selados em `main`. Cada bloco tem commit próprio,
testes passando, e CI verde.

## Blocos

| Bloco | Commit | Descrição | Testes |
|---|---|---|---|
| 0 | `1afe879` | skeleton + contracts + BOUNDARIES | — |
| 1 | `1de94c7` | core/crypto.py — hash canônico | 8 |
| 2 | `5026f26` | core/ledger.py — cadeia append-only | 9 |
| 3 | `19831ee` | core/agent.py — habitante efêmero | 12 |
| 4 | `6988226` | core/tuu.py — Centro com portões | 11 |
| 5 | `5a0d9fc` | core/reconstruct.py — parada estrita | 8 |
| 6 | `31989a8` | core/attestation.py — testemunha de boot | 10 |
| 7 | `3478207` | core/executor.py — execução isolada | 12 |
| 8 | `8828208` | core/quantum_bridge.py — ponte b1_motor | 10 |
| 9 | `4c308f6` | core/vqe_loop.py — loop VQE | 7 |
| 10 | `d76fa29` | demo_phase1.py — 5 provas | 1 |
| 11 | `d3a928c` | tests/ — suíte formal | 87 total |
| 12 | (este) | evidence/ — findings + ledger | — |

## O que o sistema faz

**Camada de governança:**
- TUU como ponto único de passagem
- Ordem dos portões: Replay → Hash → Temporal → Contract → Content → Aprovação
- Validação precede efeito (load-bearing)
- Circuit breaker em N propostas inválidas

**Camada de memória:**
- Ledger criptográfico append-only (SHA-256 encadeado)
- Reconstrução tabula rasa a partir do ledger (0.00% divergência)
- Parada estrita em prefixo válido quando há corrupção

**Camada de habitantes:**
- EphemeralAgent determinístico por (seed, context, contract)
- propose() valida contra contrato (camada 1)
- Centro valida de novo (camada 2)
- Morte idempotente com tombstone

**Camada de execução:**
- IsolatedExecutor com shell=False
- Env esterilizado, portável via sys.executable
- Timeout + truncation
- cwd restrito por contrato

**Camada quântica:**
- QuantumBridge consome o b1_motor canônico (não cópia)
- Medição de Pauli via expectation
- VQELoop multiagente com proposer/measurer/communicator/observer

**Camada epistêmica:**
- Findings formalizados em `evidence/*.md`
- Ledger persistente com hash de cada finding
- Master attestation hash

## Achados importantes

1. **Validação precede efeito** (`attack_1`) — ordem dos portões é load-bearing.
2. **Memória epistêmica total** (`attack_2`) — replay de rejeitadas conta.
3. **Memória parcial válida** (`attack_3`) — parada estrita em corrupção.
4. **Vazio ≠ ausente** (`phase_6`) — sentinel None em attestation.
5. **Portabilidade do PATH** (`phase_7`) — sys.executable, não hardcode.
6. **Payload suficiente** (`phase_10`) — ledger carrega o que reconstrói.
7. **Circuit breaker seletivo** (`phase_11`) — malformed não conta.

## O que NÃO está provado

- Contenção de runtime em nível de kernel (gVisor sem bwrap/seccomp)
- Validação independente contra oráculo externo para os observables do b1_motor
- LLM real como habitante (mock determinístico)
- b1_motor byte-idêntico no container (cópia funcional documentada)

Essas lacunas estão documentadas nos findings correspondentes.

## Como rodar

    cd auroraseven77-b12-audit

    # 87 testes do aurora_phase1
    python3 -m unittest discover -s aurora_phase1/tests -v

    # Demo das 5 provas da Fase 1
    python3 aurora_phase1/demo_phase1.py

    # Constrói o ledger persistente a partir dos findings
    python3 aurora_phase1/evidence/build_ledger.py

## Estrutura

    aurora_phase1/
    ├── __init__.py
    ├── README.md
    ├── BOUNDARIES.md
    ├── demo_phase1.py
    ├── contracts/
    │   ├── argos_role.json
    │   ├── tuu_policy.json
    │   ├── quantum_observer_role.json
    │   └── vqe_loop_policy.json
    ├── core/
    │   ├── __init__.py
    │   ├── crypto.py
    │   ├── ledger.py
    │   ├── agent.py
    │   ├── tuu.py
    │   ├── reconstruct.py
    │   ├── attestation.py
    │   ├── executor.py
    │   ├── quantum_bridge.py
    │   └── vqe_loop.py
    ├── tests/
    │   ├── __init__.py
    │   └── test_*.py (10 arquivos, 87 testes)
    ├── evidence/
    │   ├── README.md
    │   ├── ROADMAP.md
    │   ├── build_ledger.py
    │   └── *_finding.md (14 arquivos)
    └── logs/
        └── tuu_ledger.jsonl (gerado por build_ledger.py)

## Nota sobre a reconstrução

O projeto foi originalmente construído no container do AI Studio,
que reseta entre sessões. Este repo contém a reconstrução documental,
feita bloco a bloco, com validação incremental no Termux e commit no
GitHub a cada passo.

Os achados de Fase 2 e Fase 3 (attack_1..5, phase_3_*) vêm do chat
antigo preservado pelo usuário. Os achados phase_6, phase_7, phase_10,
phase_11 emergiram durante a própria reconstrução.
