# B7 — Belief Update Contract

**Status:** DRAFT / BLOCK 7
**Version:** 0.1
**Scope:** `aurora_phase1/cognitive_poc`

## Purpose

Definir normativamente como uma nova crença pode ser derivada de uma crença anterior sem modificar o estado cognitivo anterior e sem transformar atualização epistêmica em autoridade de execução.

O contrato estabelece a separação entre:
- crença anterior;
- evidência;
- proveniência da evidência;
- regra de atualização;
- resultado da atualização;
- nova crença sucessora;
- ausência justificada de atualização.

A atualização deve ser reconstruível a partir dos artefatos que a originaram.

---

## 0. Contract Rules

Este documento é a referência normativa do B7.

Nenhum valor deve ser inferido por convenção.

Cada item deve possuir um dos estados:
- **DEFINED** — decidido formalmente;
- **UNKNOWN** — ainda não definido;
- **IMPLEMENTED** — definido e implementado;
- **VERIFIED** — definido, implementado e verificado por testes/evidência;
- **PROXY** — representação provisória explicitamente identificada.

Neste bloco, o contrato é normativo. A implementação não faz parte deste documento.

---

# 1. Core Objects

## 1.1 Prior Belief

**Status:** DEFINED

Uma atualização deve referenciar explicitamente uma única crença anterior.

A crença anterior:
- possui identidade estável;
- é imutável;
- não pode ser sobrescrita pela atualização;
- permanece reconstruível após qualquer atualização posterior.

## 1.2 Evidence

**Status:** DEFINED

Toda atualização efetiva deve possuir evidência identificável.

A evidência deve possuir:
- identidade estável;
- conteúdo ou referência determinística;
- proveniência;
- temporalidade;
- relação explícita com o processo que produziu a evidência.

A existência de evidência não implica automaticamente que ela seja suficiente para atualizar uma crença.

## 1.3 Evidence Provenance

**Status:** DEFINED

A proveniência deve permitir determinar de onde a evidência veio.

Quando aplicável, deve identificar:
- fonte;
- identificador da fonte;
- tempo lógico;
- tempo de observação;
- produtor/evaluator;
- método de aquisição;
- referência ao artefato originário.

A proveniência não deve ser confundida com o conteúdo epistemicamente observado.

## 1.4 Belief State Identity

**Status:** DEFINED

A identidade determinística de um Belief State é definida por B7 sobre o objeto canônico do Belief State definido pelo Block 2. O Block 2 define a representação canônica e seu limite de hashing; B7 define a semântica de identidade derivada dessa representação.

A regra é:

`belief_identity = hash_object(belief_state.canonical_object)`

O objeto canônico do Belief State permanece exatamente:

```json
{
  "hypothesis_id": "<string>",
  "belief": <number>,
  "timestamp_logical": <integer>
}
```

A identidade deve possuir representação SHA-256 hexadecimal de 64 caracteres, conforme a infraestrutura criptográfica existente em `aurora_phase1.core.crypto.hash_object()`.

A identidade do Belief State:

- cobre exclusivamente o objeto canônico do Belief State;
- inclui `hypothesis_id`, `belief` e `timestamp_logical`;
- exclui provenance;
- exclui metadata do Ledger;
- exclui `seq`;
- exclui `tick`;
- exclui `prev_hash`;
- exclui `entry_hash`;
- não é a identidade do Ledger;
- não é a identidade da transição;
- não é a identidade da evidência;
- não é a identidade da regra de atualização;
- não é equivalente a `hypothesis_id`.

A identidade é determinística: estados com objetos canônicos idênticos produzem a mesma identidade.

Uma alteração no objeto canônico MUST resultar em uma identidade distinta sob a propriedade de resistência a colisões do SHA-256.

Como `timestamp_logical` pertence ao objeto canônico do Block 2, dois estados de crença com o mesmo `hypothesis_id` e o mesmo valor de `belief`, mas timestamps lógicos diferentes, possuem identidades distintas.

Exemplo:

```text
B1 = (H1, 0.50, t=10)
B2 = (H1, 0.50, t=30)

identity(B1) != identity(B2)
```

A sucessão de estados permanece:

```text
B_prior → Belief Update → B_successor
```

e não:

```text
B_prior → modified(B_prior)
```

A exigência de identidade distinta entre predecessor e sucessor é satisfeita pela criação de um novo objeto canônico temporalmente ordenado. A implementação MUST rejeitar qualquer atualização que não produza um novo estado canônico válido.

A identidade do Belief State MUST NOT ser usada como autorização, decisão operacional ou comando de execução.

B7 não cria um novo mecanismo criptográfico. Ele reutiliza a infraestrutura canônica existente.

## 1.5 Belief Lineage

**Status:** DEFINED

A linhagem de uma crença é a relação histórica explícita entre uma crença predecessora e uma crença sucessora produzida por um Belief Update.

A linhagem não constitui uma identidade adicional do Belief State.

Para uma atualização efetiva:

```text
B_prior
    │
    │ prior_identity
    ▼
Belief Update
    │
    │ successor_identity
    ▼
B_successor
```

O Belief Update MUST referenciar explicitamente:

- `prior_identity`;
- `successor_identity`.

As referências devem resolver deterministicamente para os respectivos Belief States.

A direção da relação é obrigatória:

```text
prior → successor
```

e não:

```text
successor → prior
```

A identidade do predecessor é derivada exclusivamente do objeto canônico do predecessor.

A identidade do sucessor é derivada exclusivamente do objeto canônico do sucessor.

A referência de linhagem ao predecessor NÃO deve ser incorporada ao objeto canônico do Belief State.

Consequentemente, adicionar ou alterar informação de linhagem não pode alterar a identidade criptográfica do Belief State.

A linhagem deve preservar:

```text
identity(B_prior)
        ↓
Belief Update
        ↓
identity(B_successor)
```

O predecessor MUST permanecer imutável após a criação da relação de linhagem.

Uma atualização efetiva MUST produzir um sucessor cuja identidade seja distinta da identidade do predecessor.

A ordem histórica MUST ser consistente com os timestamps lógicos dos estados relacionados:

```text
timestamp_logical(B_prior)
    <
timestamp_logical(B_successor)
```

A linhagem é distinta da identidade:

```text
Belief State Identity
    = identidade do estado individual

Belief Lineage
    = relação entre estados

Belief Update
    = artefato que registra a transformação epistemicamente justificável
```

Uma linhagem não constitui evidência.

Uma linhagem não constitui uma regra de atualização.

Uma linhagem não constitui autorização.

Uma linhagem não constitui execução.

`NO_UPDATE` não cria uma nova linhagem de Belief State, pois não existe sucessor efetivo.

O sistema MUST NOT inferir uma relação de linhagem apenas pela proximidade temporal ou pela igualdade de `hypothesis_id`. A relação deve ser explicitamente registrada pelo Belief Update.

Uma crença sucessora pode compartilhar o mesmo `hypothesis_id` da crença predecessora sem que isso torne as duas crenças a mesma identidade.

A linhagem deve permitir reconstruir a sucessão histórica:

```text
B_0
 ↓
BU_1
 ↓
B_1
 ↓
BU_2
 ↓
B_2
```

sem modificar retrospectivamente qualquer estado anterior.

## 1.6 Update Rule

**Status:** DEFINED

Toda atualização deve identificar explicitamente a regra utilizada para transformar a crença anterior em uma crença sucessora.

A regra deve possuir:
- identidade estável;
- versão;
- representação determinística;
- parâmetros necessários à reprodução do cálculo, quando aplicável.

Uma regra de atualização não pode ser criada retroativamente apenas para justificar um resultado desejado.

### B8.3 — Evidence Identity Bridge

**Status: DEFINED**

Todo Belief Update efetivo MUST registrar explicitamente a identidade da Cognitive Evidence que contribuiu para a atualização.

Quando uma ocorrência histórica específica da evidência for utilizada, o Belief Update MUST registrar também a identidade da ocorrência correspondente.

Envelope mínimo:

```text
Belief Update
├── prior_identity
├── evidence_id
├── occurrence_id
├── update_rule + version
└── successor_identity
```

`prior_identity` identifica o Belief State predecessor.
`evidence_id` identifica a Cognitive Evidence utilizada.
`occurrence_id` identifica a ocorrência histórica específica utilizada, quando registrada.
`update_rule` e sua versão identificam a regra aplicada.
`successor_identity` identifica o Belief State produzido.

`evidence_id` MUST NOT ser tratado como sinônimo de `occurrence_id`.

Quando `occurrence_id` estiver presente e resolvido para uma `CognitiveEvidenceOccurrence`, `occurrence.evidence_id` MUST ser igual a `belief_update.evidence_id`.

Uma referência `occurrence_id` ausente, inválida ou ambígua MUST NOT ser convertida silenciosamente em inferência.

As identidades de evidência e ocorrência são referências de linhagem e reconstrução e NÃO componentes adicionais da identidade canônica do Belief State.

Os algoritmos de `evidence_id` e `occurrence_id` permanecem definidos pelo contrato de Cognitive Evidence e pelas consolidações D12/D13.

A presença dessas identidades NÃO determina suficiência, qualidade, confiabilidade ou peso epistêmico da evidência.

### B8.3 — Temporal Boundary

**Status: DEFINED / BRIDGE OPEN**

O Belief Update MUST preservar a compatibilidade temporal necessária entre a evidência utilizada e a atualização.

`evidence_id` ou `occurrence_id` NÃO autorizam assumir equivalência entre `t_available` e `timestamp_logical`.

A relação normativa entre `t_occurrence`, `t_production`, `t_available`, `t_registration`, `t_consumption` e `timestamp_logical` permanece aberta e MUST ser definida antes de qualquer conversão ou validação automática.

Até essa definição, a implementação MUST NOT introduzir equivalência implícita entre esses campos.

Uma evidência que não possa ser demonstrada como temporalmente admissível NÃO PODE ser tratada como evidência válida de uma atualização retroativa.

### B8.5 — Temporal Admissibility Boundary

**Status: DEFINED / BRIDGE OPEN**

Para o contrato atual, a admissibilidade temporal é uma **pré-condição normativa**, mas NÃO constitui ainda um predicado operacional fechado.

Um Belief Update SOMENTE PODE declarar que a evidência utilizada é temporalmente admissível quando a relação temporal normativa aplicável estiver explicitamente definida pelo contrato correspondente.

Enquanto essa relação permanecer aberta:

- a implementação MUST NOT inferir admissibilidade por igualdade entre campos temporais;
- a implementação MUST NOT inferir admissibilidade pela ordenação entre relógios semanticamente distintos;
- `t_registration`, `t_consumption`, `Ledger tick` ou ordem de registro NÃO PODEM ser usados como substitutos implícitos da relação normativa ainda não definida;
- o tipo de ocorrência, isoladamente, NÃO constitui prova de admissibilidade em relação a `timestamp_logical`;
- ausência de uma regra normativa suficiente MUST ser tratada como semântica temporal não resolvida, e NÃO como autorização para escolher uma convenção de implementação.

D13 fecha os papéis temporais constitutivos das ocorrências, mas NÃO fecha a relação normativa entre esses papéis e o tempo lógico do processo consumidor.

Qualquer futura validação automática de admissibilidade temporal MUST ser precedida pela definição explícita dessa relação normativa.

### B8.3 — Evidence Lineage Consistency

**Status: DEFINED**

Para cada Belief Update efetivo:

1. `evidence_id` MUST estar presente.
2. `evidence_id` MUST resolver deterministicamente para a Cognitive Evidence correspondente.
3. Se `occurrence_id` estiver presente, MUST resolver deterministicamente para uma CognitiveEvidenceOccurrence.
4. Quando resolvida, `occurrence.evidence_id == belief_update.evidence_id` MUST ser verdadeiro.
5. A referência da evidência MUST permanecer histórica e imutável.
6. Correções ou novos eventos históricos MUST produzir novo artefato conforme Cognitive Evidence e MUST NOT reescrever retroativamente o Belief Update existente.

Nenhuma ordem de armazenamento, proximidade temporal, igualdade de `hypothesis_id` ou identidade de avaliador pode substituir essas referências explícitas.


## 1.7 Belief Update

**Status:** DEFINED

Um Belief Update é um artefato imutável que registra:

```text
prior belief
    +
evidence
    +
update rule
    =
successor belief
```

O Belief Update não substitui a crença anterior.
Ele cria uma relação histórica explícita entre o estado anterior e o estado sucessor.

## 1.8 Successor Belief

**Status:** DEFINED

Toda atualização efetiva deve produzir uma nova identidade de crença.

A crença sucessora:
- não pode reutilizar a identidade da crença anterior;
- deve ser imutável;
- deve ser reconstruível a partir do Belief Update;
- deve preservar referência à sua origem.

## 1.9 NO_UPDATE

**Status:** DEFINED

O sistema deve permitir representar explicitamente que uma evidência foi considerada, mas não foi suficiente ou apropriada para produzir uma nova crença.

`NO_UPDATE` não significa falha do sistema.

Pode representar:
- evidência insuficiente;
- evidência inconclusiva;
- evidência irrelevante;
- atribuição de erro à observação;
- condição experimental incompatível;
- ausência de regra válida de atualização;
- necessidade de nova experimentação.

---

# 2. Epistemic Invariants

## INV-BU-01 — Prior Belief Immutability
**Status:** DEFINED

Uma atualização não pode modificar a crença anterior.

## INV-BU-02 — Exactly One Prior Belief
**Status:** DEFINED

Cada Belief Update deve identificar exatamente uma crença anterior.

## INV-BU-03 — Identifiable Evidence
**Status:** DEFINED

Nenhuma atualização efetiva pode ocorrer sem referência identificável à evidência utilizada.

## INV-BU-04 — Verifiable Evidence Provenance
**Status:** DEFINED

A evidência utilizada em uma atualização deve possuir proveniência verificável ou explicitamente marcada como `PROXY` ou `UNKNOWN`.

## INV-BU-05 — Explicit Update Rule
**Status:** DEFINED

Nenhuma atualização efetiva pode ocorrer sem identificar explicitamente a regra de atualização utilizada.

## INV-BU-06 — Stable Rule Identity
**Status:** DEFINED

A regra utilizada deve possuir identidade e versão estáveis.

## INV-BU-07 — Prediction Commitment Preservation
**Status:** DEFINED

Uma atualização de crença não pode modificar um Prediction Commitment existente.

## INV-BU-08 — Prediction Error Preservation
**Status:** DEFINED

Uma atualização de crença não pode modificar um Prediction Error existente.

## INV-BU-09 — Attribution Preservation
**Status:** DEFINED

Uma atualização de crença não pode modificar retroativamente uma atribuição de erro existente.

## INV-BU-10 — Divergence Is Not Automatic Falsification
**Status:** DEFINED

A divergência entre previsão e observação não deve, por si só, ser interpretada como falsificação automática da hipótese.

A interpretação da divergência deve respeitar a atribuição de erro e as condições experimentais.

## INV-BU-11 — New Belief Identity
**Status:** DEFINED

Uma atualização efetiva deve produzir uma nova identidade de crença.

## INV-BU-12 — Reconstructible Update Chain
**Status:** DEFINED

Deve ser possível reconstruir:

```text
prior belief
→ evidence
→ update rule
→ belief update
→ successor belief
```

sem depender de memória implícita do agente.

## INV-BU-13 — Insufficient Evidence
**Status:** DEFINED

Evidência insuficiente deve poder resultar em `NO_UPDATE`.

## INV-BU-14 — No Execution Authority
**Status:** DEFINED

Belief Update não possui autoridade para:
- autorizar ações;
- executar ações;
- alterar políticas TUU;
- chamar diretamente HEPHAESTUS;
- contornar o TUU Center.

## INV-BU-15 — LLM Is Not Canonical State Authority
**Status:** DEFINED

Um modelo externo, incluindo LLM, pode propor:
- hipótese;
- interpretação;
- regra candidata;
- atualização candidata.

Porém, não pode alterar diretamente o estado canônico.

A proposta deve passar por validação determinística antes de se tornar artefato canônico.

## INV-BU-16 — Evidence Precedes Update
**Status:** DEFINED

A evidência utilizada deve possuir tempo lógico compatível com a atualização.

## INV-BU-17 — Prior Precedes Successor
**Status:** DEFINED

A crença anterior deve preceder logicamente a crença sucessora.

## INV-BU-18 — No Post-Hoc Evidence
**Status:** DEFINED

Evidência produzida posteriormente não pode ser reclassificada retroativamente como evidência disponível no momento da decisão anterior.

## INV-BU-19 — Immutable Historical Ordering
**Status:** DEFINED

Uma atualização posterior não pode alterar a ordenação temporal já registrada de artefatos anteriores.

## INV-BU-20 — Belief Is Not Evidence
**Status:** DEFINED

Uma crença não pode ser utilizada como substituto implícito da evidência que deveria sustentá-la.

## INV-BU-21 — Evidence Is Not Belief
**Status:** DEFINED

A existência de uma observação ou evidência não determina automaticamente uma crença.

## INV-BU-22 — Attribution Is Not Update
**Status:** DEFINED

A atribuição da causa de um Prediction Error não constitui automaticamente uma atualização de crença.

## INV-BU-23 — Update Is Not Authorization
**Status:** DEFINED

Uma crença atualizada não possui autoridade para autorizar qualquer ação.

## INV-BU-24 — Update Is Not Execution
**Status:** DEFINED

Um Belief Update não pode produzir diretamente um resultado de execução.

## INV-BU-25 — No Mutation Across Cognitive Blocks
**Status:** DEFINED

O B7 não pode alterar retroativamente:
- Prediction Commitment;
- Belief State anterior;
- Prediction Error;
- Error Attribution;
- Competing Hypotheses;
- Decision Assessment;
- Action Proposal.

---

# 3. Update Semantics

## 3.1 Evidence Does Not Imply Update
**Status:** DEFINED

O sistema deve distinguir:

```text
evidence observed
```

de:

```text
evidence sufficient for update
```

A segunda conclusão requer uma regra explícita.

## 3.2 Attribution Before Update
**Status:** DEFINED

Quando uma divergência entre previsão e observação possuir atribuição conhecida, a decisão de atualização deve considerar essa atribuição.

Fluxo conceitual:

```text
Prediction
    ↓
Observation
    ↓
Prediction Error
    ↓
Attribution
    ↓
Update Decision
```

Não:

```text
Prediction Error
    ↓
automatic belief change
```

## 3.3 Multiple Possible Outcomes
**Status:** DEFINED

Uma evidência pode produzir:

```text
UPDATE
NO_UPDATE
REJECT_UPDATE
REQUIRE_MORE_EVIDENCE
```

A escolha deve ser determinada pela regra aplicável e pelos artefatos disponíveis.

---

# 4. Determinism

## INV-BU-26 — Deterministic Canonical Representation
**Status:** DEFINED

Objetos canônicos de atualização devem possuir representação determinística.

## INV-BU-27 — Stable Serialization
**Status:** DEFINED

A serialização canônica deve produzir o mesmo resultado para o mesmo conteúdo lógico.

## INV-BU-28 — Stable Identity
**Status:** DEFINED

A identidade de cada artefato não pode depender de ordem arbitrária de execução.

## INV-BU-29 — No Semantic Ranking by Storage Order
**Status:** DEFINED

A ordem de armazenamento de múltiplos candidatos não deve ser interpretada como ranking semântico.

---

# 5. Provenance

## INV-BU-30 — Provenance Separation
**Status:** DEFINED

Proveniência deve permanecer separada do estado cognitivo canônico quando a inclusão direta puder alterar sua identidade semântica.

## INV-BU-31 — Evaluator Identity
**Status:** DEFINED

Quando uma regra determinística ou avaliador produzir um resultado, sua identidade deve poder ser registrada.

## INV-BU-32 — External Model Provenance
**Status:** DEFINED

Quando um LLM ou modelo externo participar da proposta de atualização, sua participação deve ser distinguível da regra determinística que canonizou o resultado.

---

# 6. Reconstruction

## INV-BU-33 — Historical Reconstruction
**Status:** DEFINED

O sistema deve permitir reconstruir a sequência de atualizações sem depender do estado atual como única fonte de verdade.

## INV-BU-34 — Successor Lineage
**Status:** DEFINED

Toda atualização efetiva deve registrar explicitamente, no Belief Update, a identidade da crença predecessora e a identidade da crença sucessora.

As referências `prior_identity` e `successor_identity` devem resolver deterministicamente para os respectivos Belief States.

A relação deve preservar a direção histórica:

```text
prior → successor
```

## INV-BU-35 — Evidence Lineage
**Status:** DEFINED

Toda atualização efetiva deve registrar explicitamente a evidência que contribuiu para ela.

A referência à evidência deve permitir resolução determinística para a evidência correspondente.

A evidência referenciada deve possuir identidade estável e proveniência conforme definido nas seções 1.2 e 1.3.

A identidade da evidência não é definida por este invariante como um novo mecanismo criptográfico.

## INV-BU-36 — Rule Lineage
**Status:** DEFINED

Toda atualização efetiva deve registrar explicitamente a regra de atualização utilizada e sua versão.

A referência à regra deve permitir resolução determinística para a regra correspondente e para a versão utilizada.

A regra referenciada deve possuir identidade estável, versão, representação determinística e, quando aplicável, os parâmetros necessários à reprodução do cálculo, conforme definido na seção 1.6.

A identidade da regra não é definida por este invariante como um novo mecanismo criptográfico.

---

# 7. Security / Governance Boundary

## INV-BU-37 — No TUU Bypass
**Status:** DEFINED

O B7 não pode substituir ou contornar a decisão de autorização do TUU.

## INV-BU-38 — No HEPHAESTUS Authority
**Status:** DEFINED

O B7 não pode executar ou solicitar diretamente execução operacional.

## INV-BU-39 — Cognitive State Is Not Authorization
**Status:** DEFINED

Nenhum valor de crença, probabilidade, confiança ou status cognitivo pode ser interpretado como autorização operacional.

## INV-BU-40 — Human/Policy Gate Preservation
**Status:** DEFINED

A atualização cognitiva não elimina gates humanos ou políticos definidos pelo sistema.

---

# 8. Required Relationships

**Status:** DEFINED

Uma atualização efetiva deve permitir representar:

```text
Prior Belief
    │
    ├── Evidence
    │      └── Provenance
    │
    ├── Update Rule
    │      └── Rule Version
    │
    └── Belief Update
             │
             └── Successor Belief
```

Para reconstrução completa:

```text
Hypothesis
    ↓
Prediction Commitment
    ↓
Observation
    ↓
Prediction Error
    ↓
Error Attribution
    ↓
Update Decision
    ↓
Belief Update / NO_UPDATE
    ↓
Successor Belief
```

---

# 9. Non-Goals

**Status:** DEFINED

B7 não implementa:
- execução de ações;
- autorização TUU;
- alteração automática de políticas;
- chamada direta de HEPHAESTUS;
- alteração automática de Prediction Commitments;
- alteração automática de Prediction Errors;
- alteração automática de Attribution;
- aprendizado não auditável;
- treinamento de modelo;
- alteração dos pesos de qualquer LLM;
- inferência de verdade exclusivamente a partir de LLM;
- atualização obrigatória após toda observação.

---

# 10. Formal Update Model

**Status:** DEFINED

O modelo conceitual mínimo é:

```text
BU = F(B_prior, E, R, P)
```

onde:

```text
B_prior = crença anterior
E       = evidência
R       = regra de atualização
P       = proveniência
BU      = Belief Update
```

Uma atualização efetiva produz:

```text
B_successor = G(BU)
```

A relação de sucessão exige identidade distinta:

```text
identity(B_prior) ≠ identity(B_successor)
```

A igualdade ou diferença de conteúdo entre as crenças não substitui a exigência de identidade distinta.

O processo não deve ser interpretado como mutação:

```text
B_prior → modified(B_prior)
```

mas como sucessão:

```text
B_prior → BU → B_successor
```

---

# 11. Canonical State Principle

**Status:** DEFINED

O estado cognitivo histórico deve ser tratado como uma sequência de artefatos imutáveis.

Exemplo:

```text
B17
 │
 ├── E104
 │
 ├── R7
 │
 └── BU22
       │
       └── B18
```

`B17` permanece válido como estado histórico mesmo depois da criação de `B18`.

A existência de `B18` não apaga nem reescreve `B17`.

---

# 12. Open Questions

**Status:** UNKNOWN

Os seguintes pontos permanecem deliberadamente abertos:

1. representação matemática exata de crenças;
2. escolha inicial entre atualização Bayesiana e outras famílias de atualização;
3. representação de distribuições probabilísticas;
4. política para evidência conflitante;
5. tratamento de múltiplas evidências simultâneas;
6. modelo formal de confiança da fonte;
7. semântica de regras adicionais além da identidade e versão exigidas por este contrato;
8. política para `REQUIRE_MORE_EVIDENCE`;
9. integração formal com World Model;
10. integração com Experiment Contract;
11. formato de persistência no ledger;
12. política de garbage collection, caso aplicável;
13. mecanismo de comparação entre crenças sucessoras.

Nenhuma dessas questões deve ser preenchida por convenção durante a implementação.

---

# 13. Verification Requirements

Antes de B7 ser considerado **VERIFIED**, os testes deverão demonstrar pelo menos:

1. crença anterior permanece imutável;
2. atualização exige crença anterior;
3. atualização exige evidência identificável;
4. proveniência permanece verificável;
5. regra possui identidade estável;
6. crença sucessora recebe nova identidade;
7. `NO_UPDATE` é representável;
8. Prediction Commitment não é mutado;
9. Prediction Error não é mutado;
10. Attribution não é mutada;
11. atualização não autoriza ações;
12. atualização não executa ações;
13. TUU não pode ser contornado pelo B7;
14. HEPHAESTUS não pode ser acionado diretamente;
15. representação canônica é determinística;
16. reconstrução prior → evidence → update → successor é possível;
17. evidência posterior não pode ser apresentada como evidência anterior;
18. LLM externo não possui autoridade sobre estado canônico;
19. atualizações sucessivas preservam a linhagem histórica;
20. nenhuma atualização automática ocorre apenas pela existência de Prediction Error.

---

# 14. Architectural Boundary

**Status:** DEFINED

B7 ocupa exclusivamente a fronteira:

```text
EVIDENCE
   ↓
EPISTEMIC UPDATE
   ↓
SUCCESSOR BELIEF
```

A fronteira operacional permanece:

```text
DECISION
   ↓
ACTION PROPOSAL
   ↓
TUU AUTHORIZATION
   ↓
HEPHAESTUS
   ↓
EXECUTION
```

B7 não pode atravessar essa fronteira.

---

# 15. Acceptance Criterion

**Status:** DEFINED

B7 poderá ser considerado concluído somente quando existir evidência verificável de que:

> uma crença pode evoluir para uma nova crença por meio de uma atualização explícita, imutável, determinística e reconstruível, sustentada por evidência identificável e regra versionada, sem modificar retroativamente qualquer artefato cognitivo anterior e sem adquirir autoridade de autorização ou execução.

---

**End of Contract**

**Status:** DRAFT / BLOCK 7
**Implementation:** NOT STARTED
**Verification:** NOT STARTED
