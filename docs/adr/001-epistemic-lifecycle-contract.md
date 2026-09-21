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
| **T5** | Comportamento de execução | Mover para testes de `execute_command_securely()` |
| **Unknown Mapping** | Comportamento de execução | Testar no módulo de execução |
| **T1** | Contrato legado de argumentos | Manter sob disposição arquitetural até decisão específica |
| **T6** | Identidade `AuthorizedRequest` | Manter sob disposição arquitetural |
| **M7.4** | Contrato legado de autorização/execução | Manter sob disposição arquitetural |
| **M7.5** | Retrocompatibilidade de `TUUCore` | Manter sob disposição arquitetural |

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

Os testes T1, T6, M7.4 e M7.5 permanecem temporariamente classificados como:

> *Legacy architectural contracts under disposition*

A disposição definitiva de cada contrato deverá ser registrada após a aprovação deste ADR. As possibilidades são:

* Migração para o contrato atual;
* Substituição por um contrato equivalente;
* Arquivamento como comportamento historicamente suportado;
* Decisão arquitetural separada para reintrodução da capacidade.

Nenhuma dessas opções deve ser presumida antecipadamente.

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
