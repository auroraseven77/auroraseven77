# aurora_phase1

Laboratório multiagente com governança auditável. Cada ação passa pelo
Centro (TUU). Cada decisão é registrada em um ledger criptográfico
append-only. Cada agente é efêmero. O mundo persiste.

## O que é

Um sistema onde agentes propõem, o Centro arbitra, o ledger registra.
Nada executa fora do Centro. Nada escapa do ledger. O mundo pode ser
reconstruído bit a bit a partir do log.

## Arquitetura

Três regiões:
- OBSERVAÇÃO (ARGOS): coleta, mede, registra
- EXECUÇÃO (HEPHAESTUS): transforma estado, roda processos
- COMUNICAÇÃO (HERMES): propaga intenção, negocia, traduz

Centro único (TUU): toda ação passa por ele. Nada vai direto de
uma região para outra.

Ledger criptográfico: append-only, SHA-256 encadeado, imutável.

Agentes: efêmeros, determinísticos por (seed, contexto, contrato),
mortos ao fim do ciclo. O mundo persiste; os habitantes são ondas.

## O que prova

Fase 1: o mundo pode existir.
- Habitante produz proposta estruturada
- Centro arbitra com base em contrato
- Ledger registra cadeia íntegra
- Habitante morre, memória some
- Reconstrução tabula rasa com 0.00% divergência

Fase 2: o mundo não pode ser enganado.
- Hash mismatch: rejeitado antes de qualquer efeito
- Replay (aprovada ou rejeitada): memória epistêmica total
- Chain corruption: preserva prefixo válido, para no ponto exato
- Temporal anomaly: rejeita tick futuro
- Contract immutability: atestado de boot detecta adulteração em disco

Fase 3: a execução é contida em validação.
- Path traversal: contenção em duas camadas (agente + Centro)
- Command injection: rejeição textual antes de subprocesso
- Runtime boundary: medido, não contido (documentado)
- Environment leakage: medido, não contido (documentado)

Fase 4: o Centro consulta.
- Deferimento multi-hop
- Reformulação solicitada
- Pendências sobrevivem entre sessões

Fase 5: o mundo persiste.
- Hidratação a partir do ledger
- Boot sem agentes em memória
- Zero deriva entre sessões

Fase 6: o mundo escala.
- N agentes concorrentes no mesmo tick
- Ordenação determinística
- Spawn de subagentes
- Cadeias de deferimento
- Órfãos

Fase 7: LLM como habitante.
- Determinismo via temperature=0 + hash de modelo
- Schema-validated output
- Timeout de inferência
- Não bypassa o Centro
- Não modifica contratos

Ponte quântica:
- b1_motor real integrado
- Loop VQE convergindo
- Medição via MPS + Pauli expectation
- Zero materialização de statevector

## O que NÃO prova

- Contenção de runtime em nível de kernel (gVisor sem bwrap/seccomp)
- Validação independente contra oráculo externo
- LLM real (mock determinístico)
- b1_motor canônico (cópia funcional no container; original em GitHub/Termux)

Essas lacunas estão documentadas em evidence/.

## Como rodar

    cd /aurora_phase1
    python3 -m unittest discover -s tests
    python3 demo_phase1.py

Esperado: 66 testes OK, reconstrução tabula rasa 0.00%.

## Estrutura

    contracts/          contratos versionados dos papéis
    core/               TUU, ledger, agentes, bridge, executor
    b1_motor/           motor quântico (cópia funcional)
    evidence/           achados formalizados com hash
    tests/              testes unitários por fase
    logs/tuu_ledger.jsonl  ledger criptográfico append-only
    demo_phase1.py      verificação das 5 provas da Fase 1

## Princípios

1. Validação precede efeito.
2. Contrato é fonte de verdade.
3. Consenso não é autorização.
4. Modelo não é autoridade.
5. Proposta não é execução.
6. Agentes são efêmeros; o mundo persiste.
7. Cada achado é hasheado e ancorado no ledger.
8. Reconstruir do zero é a operação mais importante.
9. Se o mundo não pode ser reconstruído, ele derivou.
10. Teste antes de fix. Falha limpa antes de conserto.

## Estado

- 7 fases seladas
- 66 testes passando
- 20+ achados ancorados no ledger
- Ledger com integridade criptográfica verificada
- mps.py canônico intocado (verificado por hash no Termux)

## Origem

Código-fonte de b1_motor: github.com/auroraseven77/auroraseven77

---


## Reconstruction provenance

Este diretório foi reconstruído a partir do estado documentado anteriormente
no container do AI Studio, após reset do ambiente. O histórico Git preserva
o README original como parte do primeiro commit deste diretório.

Blocos reconstruídos:
- Bloco 0: skeleton + contracts + BOUNDARIES.md

Blocos planejados:
- Bloco 1: core/crypto.py
- Bloco 2: core/ledger.py
- Bloco 3: core/agent.py
- Bloco 4: core/tuu.py
- Bloco 5: core/reconstruct.py
- Bloco 6: core/attestation.py
- Bloco 7: core/executor.py
- Bloco 8: core/quantum_bridge.py
- Bloco 9: core/vqe_loop.py
- Bloco 10: demo_phase1.py
- Bloco 11: tests/
- Bloco 12: evidence/

Cada bloco só avança após validação no Termux e commit no GitHub.

b1_motor NÃO é duplicado aqui. O motor canônico vive em /b1_motor na raiz
do repositório. Este diretório consome o canônico via core/quantum_bridge.py.
