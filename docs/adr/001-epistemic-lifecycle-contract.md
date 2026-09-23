# ADR-001: Contrato Canônico de Ciclo de Vida Epistêmico (`process_intent_lifecycle`)

## Status

Proposto / Em Análise

## Contexto

Durante a auditoria do Integration Pipeline, foi identificada uma divergência estrutural entre a suíte de testes histórica (`TUU/tests/test_tuu_integration.py` e `TUU/tests/test_tuu_m7_integration.py`) e a API atualmente implementada.

O ponto de divergência determinístico foi introduzido no commit `53b247f1877cd9873c8903e8ffc77eeb4f329dbc`, que removeu a classe `TUUCore` de `TUU/tuu_core.py` e introduziu o orquestrador assíncrono `process_intent_lifecycle`.

A arquitetura histórica era orientada a requisições de execução:

```text
REQUEST(intent, args, context)
        ↓
     TUUCore
        ↓
  PolicyDecision
        ↓
 AuthorizedRequest
        ↓
 SandboxExecutor
```

A arquitetura atual é orientada à avaliação epistemológica antes da autorização normativa e da execução:

```text
AgentMetricOutput
        ↓
CandidateEvaluation
        ↓
K_N / consenso epistemológico
        ↓
AuthorizationDecision
        ↓
execute_command_securely()
        ↓
ExecutionResult
```

A divergência entre essas duas arquiteturas não deve ser resolvida simplesmente adaptando os testes históricos até que o CI fique verde. Primeiro é necessário estabelecer qual contrato representa a arquitetura canônica do TUU.

## Decisão

### 1. Contrato Canônico

`process_intent_lifecycle` é estabelecido como a interface oficial para o fluxo completo do ciclo de vida epistêmico:

$$\text{Intenção} \longrightarrow \text{Avaliação Epistemológica} \longrightarrow \text{Consenso} \longrightarrow \text{Autorização Normativa} \longrightarrow \text{Execução} \longrightarrow \text{Resultado}$$

Isso não impede a existência de funções ou classes internas auxiliares, desde que não criem uma segunda interface pública concorrente para o mesmo fluxo.

### 2. Separação entre Consenso e Autorização

O consenso epistemológico não constitui autorização de execução. A fronteira normativa é representada por `AuthorizationDecision`, e somente uma decisão autorizada pode ser encaminhada a `execute_command_securely()`.

Consequentemente:

* $\text{Consensus} \neq \text{Authorization}$
* $\text{Authorization} \neq \text{Execution}$

O resultado do consenso determina o candidato selecionado; a autorização continua sendo uma etapa normativa independente.

### 3. Interfaces Legadas

As seguintes abstrações do modelo anterior deixam de fazer parte do contrato canônico:

* `TUUCore`;
* `AuthorizedRequest`;
* O envelope genérico de `REQUEST(intent, args, context)` como interface do ciclo completo;
* A passagem de argumentos desestruturados baseada no contrato legado.

Essas interfaces não serão reintroduzidas apenas para preservar compatibilidade com testes históricos.

### 4. Argumentos Parametrizados

A implementação atual utiliza `shlex.split(decision.intent)` para transformar a intenção textual em tokens de execução.

Isso constitui o mecanismo de transporte atualmente implementado, mas não estabelece uma especificação arquitetural definitiva para intenções parametrizadas complexas.

A necessidade de representar de maneira explícita, determinística e auditável comandos com argumentos estruturados permanece uma questão arquitetural aberta. Este ADR, portanto, não declara que argumentos parametrizados deixaram de ser uma capacidade desejada do TUU.

### 5. Imutabilidade da Fronteira Normativa

`AuthorizationDecision` permanece como uma fronteira normativa imutável. A decisão não deve permitir mutação posterior capaz de alterar:

* O status de autorização;
* A intenção autorizada;
* A política avaliada;
* O motivo;
* Os metadados associados à decisão.

A imutabilidade recursiva de `metadata` faz parte desse contrato.

---

## Consequências

A adoção deste contrato implica que a suíte de testes deve refletir a arquitetura atual, e não preservar automaticamente contratos que foram removidos.

| Teste / Suíte | Classificação | Ação |
| :--- | :--- | :--- |
| **T2, T3, T4** | Propriedades de segurança preservadas | Migrar para `AuthorizationDecision` e autorização atual |
| **M7.1, M7.2** | Testes unitários de motores | Manter diretamente em `CollapseEngine` / `SwarmEngine` |
| **M7.3** | Barreira normativa | Reescrever para a semântica de `process_intent_lifecycle` |
| **T1** | Fluxo legado `TUUCore` + `AuthorizedRequest` + argumentos | Retirar do Integration Pipeline; a propriedade de execução autorizada é coberta por M7.4. A representação estruturada de argumentos permanece questão arquitetural separada |
| **T5** | Timeout do executor | Migrar para teste direto de `execute_command_securely()` usando `AuthorizationDecision` / `ExecutionResult` atuais |
| **T6** | Identidade `AuthorizedRequest` | Retirar como contrato não equivalente; não há identidade equivalente no modelo atual |
| **Argument violation** | Sanitização/validação de argumentos do contrato legado | Retirar do Integration Pipeline; não existe propriedade equivalente no contrato atual até que a representação estruturada de argumentos seja especificada |
| **Unknown Mapping** | Defesa de execução contra executável fora da allowlist | Migrar para teste direto de `execute_command_securely()` como defesa em profundidade |
| **M7.4** | Contrato legado de autorização/execução | Substituído por teste de continuidade `collapsed_candidate.intent → authorization.intent → execution.intent` |
| **M7.5** | Retrocompatibilidade de `TUUCore` | Retirar/arquivar como contrato histórico; `TUUCore` não é contrato canônico e não possui equivalente atual |

Os testes classificados como contratos arquiteturais legados não devem ser apagados ou alterados para mascarar a divergência antes da aprovação deste ADR.

---

## Não-Decisões

Este ADR **não**:

1. Define uma nova representação de argumentos parametrizados;
2. Declara que comandos parametrizados são permanentemente proibidos;
3. Especifica uma nova política de allowlist;
4. Altera os limiares de consenso $K_N$;
5. Altera a fórmula de avaliação dos candidatos;
6. Reintroduz `TUUCore` por compatibilidade;
7. Determina, por si só, a remoção física dos testes legados.

Esses pontos exigem decisões ou mudanças independentes.

---

## Disposição dos Contratos Legados

A auditoria final do Integration Pipeline confirmou que os contratos remanescentes não formam um único bloco migrável. Eles foram separados entre propriedades preserváveis no contrato atual, testes que devem ser deslocados para a camada de execução e contratos históricos sem equivalente.

### M7.5 — decisão explícita

M7.5 será **retirado/arquivado como contrato histórico** e não será migrado para `process_intent_lifecycle`. Seu objeto é verificar retrocompatibilidade de `TUUCore`, `PolicyEngine`, `AuthorizedRequest` e `core.process()`. Essas abstrações foram removidas do contrato canônico no commit `53b247f1877cd9873c8903e8ffc77eeb4f329dbc`. Não existe uma propriedade normativa equivalente que justifique recriar essa API.

A propriedade operacional de continuidade de uma intenção autorizada até a execução já é coberta pelo M7.4 atual.

### Testes legados de `test_tuu_integration.py`

- **T1:** retirar do Integration Pipeline; sua parte de execução autorizada é coberta por M7.4, enquanto argumentos estruturados continuam sem contrato definitivo.
- **T5:** migrar para teste direto de `execute_command_securely()`, preservando a propriedade de timeout sob o contrato atual.
- **T6:** retirar como contrato de identidade de `AuthorizedRequest`; não há equivalente atual.
- **Argument violation:** retirar como contrato legado de validação/sanitização de argumentos; não há equivalente atual até uma especificação explícita de argumentos estruturados.
- **Unknown Mapping:** migrar para teste direto de `execute_command_securely()`, preservando a defesa em profundidade da allowlist de execução.

Esta decisão não reintroduz `TUUCore`, `AuthorizedRequest` ou `PolicyDecision`, e não altera produção.

---

## Evidência Histórica

* O commit `53b247f1877cd9873c8903e8ffc77eeb4f329dbc` é considerado o primeiro ponto determinístico da divergência porque removeu `TUUCore` e estabeleceu o fluxo baseado em `process_intent_lifecycle`.
* O commit anterior `23257f2b3ec2fcbb824146104c416ed6e2209619` já introduzia testes orientados ao novo ciclo de vida, demonstrando que a migração arquitetural estava em andamento.
* Alterações posteriores de consenso e fixtures não são consideradas a origem da remoção de `TUUCore`.

---

## Critério de Aceitação

O ADR será considerado implementado quando:

1. O contrato canônico estiver aprovado;
2. Os testes preservados tiverem sido classificados segundo esse contrato;
3. Os testes legados sob disposição tiverem uma decisão explícita;
4. O Integration Pipeline testar a arquitetura atualmente suportada;
5. Nenhum teste for alterado exclusivamente para produzir um CI verde sem correspondência com um contrato arquitetural declarado.
