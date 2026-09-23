# aurora_phase1 — Fronteiras entre Camadas

Este documento define o que atravessa cada fronteira do sistema.
Contrato explícito é fonte de verdade. Sem fronteira declarada,
não há acoplamento legítimo.

## Diagrama

    aurora_phase1/
    │
    ├── contracts/          (leis — nunca mudam sem versionamento)
    │
    ├── core/
    │   ├── tuu.py          (Centro — único que decide)
    │   ├── ledger.py       (memória — única fonte de verdade histórica)
    │   ├── agent.py        (habitantes — efêmeros)
    │   ├── reconstruct.py  (reconstrução — deriva estado do ledger)
    │   ├── attestation.py  (testemunha de boot)
    │   ├── executor.py     (execução isolada)
    │   ├── quantum_bridge.py  (adapter para /b1_motor)
    │   └── vqe_loop.py     (orquestração VQE multiagente)
    │
    ├── tests/              (verificação)
    │
    ├── evidence/           (achados formalizados)
    │
    └── logs/
        └── tuu_ledger.jsonl  (registro criptográfico)

## Fronteira 1 — Agente → Centro

- Agente NUNCA acessa ledger diretamente.
- Agente NUNCA executa código.
- Agente submete proposta estruturada via `tuu.evaluate_proposal(proposal)`.
- Proposta tem campos obrigatórios:
  - `proposal_id` (hash determinístico)
  - `agent_id`
  - `role`
  - `action_type`
  - `timestamp_logical`
  - `hypothesis`
  - `seed`

## Fronteira 2 — Centro → Ledger

- Centro é o ÚNICO escritor do ledger.
- Toda escrita é precedida por validação.
- Ordem obrigatória dos portões:
  1. Replay check (`seen_proposal_ids`)
  2. Hash check (proposal_id bate com payload?)
  3. Temporal check (tick coerente?)
  4. Contract check (ação permitida pelo contrato?)
  5. Content check (conteúdo do payload permitido?)
  6. Aprovação + sedimentação

Se qualquer portão falha, NENHUM efeito colateral ocorre.

## Fronteira 3 — Centro → Executor

- Centro decide; executor executa.
- Executor NUNCA decide.
- Execução em subprocesso (nunca no processo principal).
- `shell=False` obrigatório.
- `env` esterilizado (nunca herdado).
- `cwd` restrito a `allowed_paths` do contrato.
- `timeout` obrigatório.
- stdout/stderr capturados com limite.
- Resultado volta ao Centro como observação estruturada, não bruto.

## Fronteira 4 — Centro → b1_motor canônico

- `core/quantum_bridge.py` é o ÚNICO ponto de acesso a `/b1_motor`.
- Bridge consome API pública de `/b1_motor` (`observables`, `mps`, `hamiltonian_b12`, `vqe_b12`).
- Bridge NUNCA materializa statevector global.
- Bridge retorna resultado estruturado com hash determinístico.
- `/b1_motor` NÃO é modificado por `aurora_phase1`.
- Configuração experimental (ex: `CHI_MAX=32`) é parâmetro do bridge, não código paralelo.

## Fronteira 5 — Ledger → Reconstruct

- `reconstruct.py` LÊ o ledger, nunca escreve.
- Se o ledger tem corrupção, reconstruct para no último bloco válido.
- Reconstruct retorna estado até o último bloco íntegro.
- Reconstruct reconstrói também:
  - `seen_proposal_ids` (memória de replay)
  - contadores de estado
  - pendências de deferimento

## Fronteira 6 — Attestation → Boot

- `attestation.py` sela os hashes dos contratos no boot.
- Se a integridade falha, o comportamento é:
  - Opção A (default): falha dura, mundo não inicia.
  - Opção B (--degraded): inicia com flag visível, tombstone marcado.
  - Opção C: banida.

## Fronteira 7 — Evidence → Ledger

- Cada achado (`evidence/attack_N_finding.md`) tem hash SHA-256.
- Hash é registrado no ledger como `ATTACK_FINDING_RECORDED`.
- Ledger preserva a cadeia de achados.
- Se um achado é removido, a cadeia quebra e é detectada.

## Fronteira 8 — TUU externo → aurora_phase1

- `TUU/` da raiz do repositório é v1 existente (lifecycle epistêmico).
- `aurora_phase1/core/tuu.py` é v2 (governança multiagente).
- Eles COEXISTEM, não competem.
- `aurora_phase1/core/tuu.py` pode futuramente importar de `TUU/`, mas não agora.
- Migração é decisão futura, não automática.
