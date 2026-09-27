# Cognitive Evidence Contract

**Status:** DRAFT / NORMATIVE CONSOLIDATION
**Version:** 0.2
**Scope:** Cognitive Core
**Purpose:** Definir a representação normativa de evidência cognitiva utilizada por processos epistemicamente auditáveis.

> Este contrato é normativo para Cognitive Evidence.
> Nenhuma implementação deve ser inferida apenas por convenção.
> Itens ainda não determinados devem permanecer explicitamente `UNKNOWN`.

---

## 0. Contract Rules

Cada requisito deve possuir um dos estados:

- **DEFINED** — decidido normativamente;
- **UNKNOWN** — ainda não decidido;
- **DEFERRED** — decisão deliberadamente postergada;
- **PROXY** — representação que não possui equivalência plena com o objeto epistemicamente pretendido.

---

## 1. Cognitive Evidence

**Status:** DEFINED

Cognitive Evidence é um artefato epistemicamente identificável utilizado como entrada de um processo cognitivo.

Cognitive Evidence não é:

- Belief State;
- Prediction Commitment;
- Prediction Error;
- Error Attribution;
- Hypothesis Set;
- Decision Assessment;
- Action Proposal;
- autorização;
- execução;
- estado canônico de outro bloco.

A existência de Cognitive Evidence não implica automaticamente uma atualização de crença.

---

## 2. Evidence Identity

**Status:** DEFINED

A Cognitive Evidence MUST possuir identidade estável e determinística.

A identidade cognitiva é conceitualmente separada da identidade de uma ocorrência histórica.

São referências distintas:

- `evidence_id` — identidade da evidência enquanto representação epistemicamente identificável;
- `occurrence_id` — identidade de uma ocorrência histórica específica dessa evidência.

O mecanismo criptográfico ou algorítmico concreto de geração desses identificadores permanece **SUPERSEDED BY D12**.
A decisão normativa posterior D12 define a construção de `evidence_id`.

O contrato MUST NOT assumir:

`Superseded draft statement: Cognitive Evidence Identity = Ledger evidence_hash`

Também MUST NOT assumir:

`Superseded draft statement: Cognitive Evidence Identity = Ledger entry_hash`

A identidade cognitiva é definida pelo contrato de Cognitive Evidence e não herdada por analogia de outros artefatos.

---

## 3. Canonical Representation

**Status:** SUPERSEDED BY D12

A Cognitive Evidence MUST possuir uma representação canônica determinística antes da implementação.

O objeto canônico deve conter somente os campos que constituem sua identidade ou conteúdo epistemicamente definido.

Provenance MUST NOT ser incorporada silenciosamente ao objeto canônico.

A lista exata de campos canônicos permanece **SUPERSEDED BY D12**.
A representação canônica normativa foi posteriormente fechada por D12.

A representação canônica não deve depender de:

- ordem de registro no Ledger;
- `seq`;
- `tick`;
- `prev_hash`;
- `entry_hash`;
- identidade do avaliador;
- metadados operacionais;
- estado interno de um LLM.

---

## 4. Evidence Content

**Status:** DEFINED

A Cognitive Evidence MUST separar conteúdo epistemicamente observado de sua provenance.

A representação do conteúdo é uma camada de transporte, armazenamento e reconstrução do conteúdo
epistemicamente relevante. Ela MUST permanecer semanticamente separada da identidade da evidência,
da provenance, da ocorrência e de metadados operacionais.

A representação MAY utilizar, quando compatível com a semântica do tipo:

- conteúdo diretamente incorporado;
- referência determinística a conteúdo externo;
- combinação de conteúdo incorporado e referência determinística.

Nenhuma dessas formas de representação define, por si só, identidade ou equivalência semântica.

A escolha da forma de representação MAY depender do tipo semântico e de suas regras constitutivas.
Nenhuma forma deve ser assumida por convenção quando a semântica do tipo exigir uma regra diferente.

Toda representação utilizada por um processo cognitivo MUST permitir resolução determinística do conteúdo
necessário para aquele processo.

Uma referência externa MUST ser estável e determinística o suficiente para permitir a resolução do conteúdo
correspondente segundo as regras aplicáveis.

Uma referência ausente, ambígua, inválida ou não resolvível MUST NOT ser silenciosamente substituída por
inferência, conteúdo aproximado ou outra representação não autorizada.

A indisponibilidade posterior de uma representação externa MUST NOT alterar retroativamente o conteúdo
histórico, o `evidence_id`, a ocorrência histórica ou qualquer outro artefato já registrado.

Quando o conteúdo necessário não puder ser deterministicamente reconstruído, a evidência MUST ser tratada
como não resolvível para aquele consumo, sem fabricação ou substituição silenciosa do conteúdo.

A representação utilizada para transportar ou reconstruir o conteúdo MUST NOT ser incorporada à identidade
epistêmica apenas por ser a representação escolhida.

A identidade da Cognitive Evidence permanece determinada pela estrutura semântica constitutiva aplicável,
conforme D10 e D12.

---

## 5. Evidence Provenance

**Status:** DEFINED

A provenance da Cognitive Evidence deve permanecer separada de seu conteúdo epistemicamente observado.

Quando aplicável, a provenance deve permitir reconstruir:

- origem;
- fonte;
- identificador da fonte;
- produtor ou evaluator;
- método de aquisição;
- artefato originário;
- referências a outros artefatos cognitivos;
- informação temporal necessária à reconstrução.

Provenance não constitui automaticamente conteúdo epistemicamente observado.

---

## 6. System Artifact Reference

**Status:** DEFINED

Uma Cognitive Evidence MAY possuir referência explícita a um artefato de sistema associado.

Quando existir um artefato registrado no Ledger, sua referência poderá apontar para o respectivo `evidence_hash`.

A referência ao artefato do sistema não transforma o `evidence_hash` em identidade da Cognitive Evidence.

---

## 7. Temporal Semantics

**Status:** REQUIRED

A temporalidade da Cognitive Evidence MUST distinguir, quando aplicável:

- `t_occurrence` — quando a ocorrência epistemicamente relevante aconteceu;
- `t_production` — quando a representação foi produzida;
- `t_registration` — quando foi registrada pelo sistema;
- `t_available` — quando estava disponível para consumo cognitivo;
- `t_consumption` — quando um processo cognitivo a utilizou.

Esses tempos NÃO são automaticamente equivalentes.

Nem todos precisam existir em toda evidência.

A representação temporal exata, os tipos, os campos obrigatórios e suas regras de validação permanecem
**PARTIALLY OPEN** onde não foram fechados por D13.

D13 define especificamente os papéis temporais constitutivos das ocorrências e seu mapeamento para
`normalized_occurrence_semantics`, sem fechar toda a semântica temporal da Cognitive Evidence.

`timestamp_logical` dos demais blocos cognitivos e `Ledger tick` permanecem semanticamente separados desses tempos.

Uma ocorrência específica deve possuir `occurrence_id` próprio, mesmo quando duas ocorrências estejam associadas ao mesmo `evidence_id`.

---

## 8. Occurrence Identity

**Status:** DEFINED

Uma ocorrência é uma instância historicamente identificável na qual uma evidência foi observada, adquirida, produzida ou disponibilizada para um processo cognitivo.

Cada ocorrência MUST possuir `occurrence_id` próprio.

`occurrence_id` MUST NOT ser tratado como sinônimo de `evidence_id`.

Uma mesma `evidence_id` MAY possuir múltiplas ocorrências quando o contrato determinar que representam a mesma evidência epistemicamente identificável em instâncias históricas distintas.

O mecanismo concreto de geração de `occurrence_id` permanece **SUPERSEDED BY D13**.
D13 define normativamente `occurrence_id` por SHA-256 da representação canônica da ocorrência.

A equivalência semântica entre ocorrências e evidências deve ser determinística e explicitamente definida antes da implementação.

---

## 9. Deterministic Resolution

**Status:** DEFINED

Uma Cognitive Evidence utilizada por uma atualização efetiva MUST ser deterministicamente resolvível.

Uma referência ausente ou ambígua MUST NOT ser silenciosamente substituída por uma inferência.

---

## 10. Temporal Integrity

**Status:** DEFINED

Cognitive Evidence MUST preservar a temporalidade necessária para reconstruir quando a evidência foi observada, produzida, registrada ou disponibilizada a um processo cognitivo, conforme as semânticas específicas que forem definidas neste contrato.

Uma evidência posterior MUST NOT ser representada como se estivesse disponível para um processo cognitivo anterior quando essa disponibilidade não puder ser sustentada pela provenance e pelas regras temporais aplicáveis.

A existência posterior de uma evidência não autoriza, por si só, a reclassificação retroativa de um estado cognitivo anterior.

A semântica exata de disponibilidade e a relação entre os diferentes tempos permanecem em aberto e devem ser definidas na Seção 7 antes da implementação.

---

## 11. Evidence Is Not Update

**Status:** DEFINED

A existência de Cognitive Evidence não implica automaticamente:

- Belief Update;
- alteração de Belief State;
- falsificação de hipótese;
- autorização;
- decisão operacional;
- execução.

A suficiência da evidência para uma atualização pertence à regra/processo de atualização explicitamente declarado.

---

## 12. Provenance and Canonical Boundary

**Status:** DEFINED

Referências a outros artefatos devem permanecer referências.

O sistema MUST NOT copiar silenciosamente o conteúdo canônico de outro artefato para dentro da Cognitive Evidence apenas para facilitar rastreabilidade.

A rastreabilidade deve ser obtida por referências determinísticas.

---

## 13. Identity Equivalence

**Status:** SUPERSEDED BY D10

Este bloco preserva a formulação histórica da questão de equivalência
presente no contrato inicial.

A questão normativa foi posteriormente consolidada por D10.

D10 estabelece que equivalência semântica MUST ser decidida por meio
das estruturas semânticas constitutivas aplicáveis ao tipo da
Cognitive Evidence, independentemente de:

- `evidence_id`;
- `occurrence_id`;
- hashes do Ledger;
- serialização canônica;
- provenance;
- igualdade de conteúdo isoladamente;
- igualdade de representação;
- concordância de modelos externos ou LLMs.

A formulação histórica acima NÃO permanece como requisito aberto.
A consolidação normativa aplicável encontra-se em D10.

---

## 14. Sufficiency

**Status:** UNKNOWN

O contrato ainda não define um critério matemático ou operacional de suficiência de evidência.

A presença de evidência identificável não deve ser interpretada como suficiência.

---

## 15. Confidence

**Status:** UNKNOWN

Não está definido se confidence pertence à Cognitive Evidence, à provenance, ao avaliador ou a outro artefato.

Nenhum campo de confidence deve ser introduzido por convenção.

---

## 16. External Model Involvement

**Status:** DEFINED

Participação de modelo externo, quando existente, deve ser tratada como provenance e não como autoridade canônica da Cognitive Evidence.

Um modelo externo não constitui, por si só, autoridade para alterar o estado cognitivo canônico.

---

## 17. Non-Goals

Este contrato não define:

- algoritmo de Belief Update;
- Bayes;
- regra de suficiência;
- falsificação automática;
- decisão;
- autorização;
- execução;
- HEPHAESTUS;
- alteração de pesos de LLM;
- treinamento;
- mecanismo de consenso;
- persistência definitiva;
- política de retenção;
- mecanismo criptográfico específico de identidade.

---

## 18. Open Questions

1. Qual mecanismo de identidade será utilizado?
2. Quais campos pertencem ao objeto canônico?
3. Conteúdo inline, referência ou ambos? **SUPERSEDED BY B8.4.**
4. Qual a semântica exata de cada campo temporal?
5. Quando duas evidências são semanticamente equivalentes?
6. Evidências idênticas em ocorrências diferentes possuem a mesma identidade?
7. Qual a relação formal entre Cognitive Evidence e artefato do Ledger?
8. Confidence pertence à evidência ou à avaliação?
9. Como representar evidência composta?
10. Como representar evidência conflitante?
11. Como representar ausência de evidência?
12. Qual o critério formal de suficiência?
13. Como representar evidência `PROXY`?
14. Como representar evidência `UNKNOWN`?
15. Quais parâmetros são necessários para reprodução de uma avaliação da evidência?

---

## 19. Required Verification

Antes da implementação, devem existir testes ou verificações para pelo menos:

1. identidade determinística;
2. separação entre identidade e provenance;
3. separação entre conteúdo e provenance;
4. resolução determinística;
5. ausência de equivalência automática com Ledger `evidence_hash`;
6. preservação temporal;
7. rejeição de classificação retroativa;
8. ausência de atualização automática;
9. ausência de autoridade operacional;
10. preservação da referência a artefato externo sem copiar seu conteúdo canônico.

---

## 20. Normative Invariants

**Status:** DEFINED

### INV-CE-01 — Stable Evidence Identity
Uma Cognitive Evidence MUST possuir identidade estável e determinística.

### INV-CE-02 — Separate Occurrence Identity
A ocorrência histórica MUST possuir identidade separada da evidência.

### INV-CE-03 — Identity Separation
`evidence_id` MUST NOT ser tratado como `occurrence_id`.

### INV-CE-04 — Ledger Identity Separation
`evidence_id` MUST NOT ser automaticamente igual a `evidence_hash` ou `entry_hash`.

### INV-CE-05 — Canonical Boundary
Campos de provenance e metadados do Ledger não podem ser incorporados silenciosamente ao objeto canônico.

### INV-CE-06 — Historical Reconstruction
Uma ocorrência deve permanecer historicamente reconstruível por sua identidade e provenance.

### INV-CE-07 — Temporal Integrity
A relação temporal relevante para consumo cognitivo deve ser preservada.

### INV-CE-08 — No Retroactive Availability
Evidência posterior não pode ser representada como disponível anteriormente sem suporte de provenance e das regras temporais aplicáveis.

### INV-CE-09 — Historical Immutability
Correções ou novas informações devem produzir novos artefatos ou avaliações; histórico anterior não deve ser mutado.

### INV-CE-10 — No Automatic Belief Update
A existência de evidência não implica automaticamente Belief Update.

### INV-CE-11 — No Automatic Attribution
A existência de evidência não determina automaticamente causa ou atribuição.

### INV-CE-12 — No Automatic Truth
A existência de evidência não estabelece automaticamente verdade.

### INV-CE-13 — Conflict Preservation
Evidências conflitantes podem coexistir e não devem ser silenciosamente descartadas.

### INV-CE-14 — Absence Separation
Ausência de evidência não deve ser automaticamente interpretada como evidência negativa.

### INV-CE-15 — Deterministic Resolution
Referências de evidência devem ser deterministicamente resolvíveis.

### INV-CE-16 — External Model Non-Authority
Saída de modelo externo pode ser provenance ou conteúdo avaliado, mas não é autoridade canônica por si só.

### INV-CE-17 — Cross-Block Separation
Referências entre blocos devem permanecer referências determinísticas, sem cópia silenciosa de conteúdo canônico.

### INV-CE-18 — Correction as New Artifact
Uma correção não pode reescrever retroativamente a identidade ou o conteúdo histórico da evidência anterior.

### INV-CE-19 — Composite Traceability
Evidência composta deve permitir rastrear seus constituintes quando essa distinção for epistemicamente relevante.

### INV-CE-20 — Semantics Before Implementation
A implementação não pode decidir silenciosamente semânticas ainda classificadas como `UNKNOWN`.

---


## D10 — Typed Constitutive Semantics

### Status

D10 = CONSOLIDATED

### Normative Supersession Rule

This section and the subsequent D12/D13 closure sections are the
authoritative consolidation layer for decisions made after the
initial contract draft.

Where an earlier section of this contract is marked `UNKNOWN` and a
later D10, D12, or D13 section explicitly closes the same normative
question, the later consolidated decision supersedes the earlier
`UNKNOWN` status.

This supersession applies only to the specific normative question
explicitly closed by the later section.

`UNKNOWN` items not explicitly closed by D10, D12, or D13 remain
`UNKNOWN` and MUST NOT be resolved by implementation convention.

Accordingly:

- D10 supersedes earlier unresolved semantic-equivalence statements
  within its stated scope;
- D12 supersedes earlier unresolved `evidence_id` construction
  statements;
- D13 supersedes earlier unresolved `occurrence_id` construction,
  occurrence taxonomy, and canonical occurrence representation
  statements.

This rule does not close sufficiency, confidence, or other questions
that remain outside those closure decisions.

The external-content representation question was subsequently closed
by B8.4. B8.4 defines representation as a transport, storage, and
reconstruction layer that is type-governed and semantically separate
from epistemic identity, provenance, occurrence, and operational
metadata.

D10 formalizes the typed constitutive semantics required by the
semantic relation established in D03-R02.

This section defines the semantic boundary needed before any
normative generation of `evidence_id` or `occurrence_id`.

### Constitutive Semantic Principle

A Cognitive Evidence object is treated as a typed epistemic object.

Its identity-bearing semantic structure is determined by the
constitutive dimensions specified by its semantic type.

Semantic equivalence MUST therefore be evaluated through the
typed constitutive semantics of the evidence object.

Semantic equivalence MUST NOT be defined by:

- `evidence_id` equality;
- `occurrence_id` equality;
- Ledger hash equality;
- canonical JSON equality;
- representation equality;
- provenance equality;
- external-referent equality alone;
- content equality alone;
- agreement between external models or LLMs.

The semantic relation MUST remain independently decidable before
identifier generation.

### Typed Semantic Dimensions

The following dimensions are recognized by D10:

| Dimension | Classification |
|---|---|
| REFERENT | DEPENDENT / TYPE-GOVERNED |
| ASSERTION | CONSTITUTIVE |
| CONTENT | CONSTITUTIVE WHEN TYPE-DETERMINED |
| CONTEXT | DEPENDENT |
| TEMPORAL_ASSERTION | CONSTITUTIVE WHEN ASSERTED |
| OBSERVATIONAL_BASIS | DEPENDENT / TYPE-GOVERNED |
| MEASUREMENT_STRUCTURE | DEPENDENT / TYPE-GOVERNED |
| DERIVATION | RELATIONAL |
| COMPOSITION | RELATIONAL |
| CORRECTION_STATE | HISTORICAL RELATION |

A dimension classified as DEPENDENT or TYPE-GOVERNED MUST NOT be
promoted to a universal constitutive rule.

A relational dimension describes a relation between epistemic
objects and MUST NOT by itself collapse those objects into one
identity.

A historical relation MUST preserve the historical event and MUST
NOT rewrite the prior evidence object.

### Semantic Separation

The following separations are normative:

1. Representation is distinct from epistemic identity.
2. Provenance is distinct from epistemic identity.
3. Occurrence is distinct from epistemic identity.
4. Operational metadata is distinct from constitutive semantics.
5. A shared external referent does not by itself establish semantic
   equivalence.
6. Equal content does not by itself establish semantic equivalence.
7. Different representation does not by itself establish semantic
   difference.
8. Derivation does not collapse source and derived evidence.
9. Composition does not collapse a composite object with its
   constituents.
10. Correction does not retroactively mutate historical evidence.
11. Temporal information is constitutive only when the semantic type
    makes the temporal assertion part of what is asserted.
12. Measurement and observational structure are constitutive only
    where required by the semantic type.
13. External-model or LLM agreement is evidence or provenance only;
    it is not canonical epistemic authority.

### R02 Compatibility

D10 is compatible with the D03-R02 relation:

`R02(A,B)` holds only when A and B are valid Cognitive Evidence
objects whose constitutive semantic structures are equivalent under
their applicable semantic types.

R02 MUST NOT be defined through identifier equality, occurrence
equality, Ledger hashes, canonical serialization equality, or any
other downstream representation.

R02 remains upstream of identifier generation.

### Anti-Circularity Requirements

D10 MUST satisfy all of the following:

- semantic equivalence does not depend on `evidence_id`;
- semantic equivalence does not depend on `occurrence_id`;
- semantic equivalence does not depend on Ledger `entry_hash`;
- semantic equivalence does not depend on Ledger `evidence_hash`;
- provenance does not silently determine identity;
- occurrence does not silently determine identity;
- canonical serialization does not define semantic equivalence;
- content equality does not define semantic equivalence;
- external-referent equality does not define semantic equivalence;
- external-model agreement does not define semantic equivalence.

### Historical Preservation

Corrections, transformations, derivations, observations, and
subsequent assessments are historical epistemic events.

They MUST NOT rewrite previously recorded Cognitive Evidence.

A later correction MAY establish a relation to prior evidence, but
the historical record remains preserved.

### Identifier Boundary

D10 does NOT define the algorithms for:

- `evidence_id`;
- `occurrence_id`.

Those algorithms remain downstream of the semantic closure established
by D03-R02 and D10.

Therefore:

`D12 evidence_id = CLOSED`

`D13 occurrence_id = NORMATIVELY DEFINED`

`IMPLEMENTATION = NEXT`

No implementation MUST be introduced solely to resolve an unresolved
normative semantic decision.

### Implementation Gate

No normative implementation of Cognitive Evidence identity,
occurrence identity, or semantic equivalence may be introduced until
the corresponding contract requirements are explicitly satisfied.

Tests MUST derive from the normative contract.

Tests MUST NOT convert an implementation choice into a normative
semantic rule.

External LLMs or other models MAY provide hypotheses, analyses,
transformations, or provenance-bearing input, but MUST NOT become
canonical authority over Cognitive Evidence semantics.


## D13 — Normative Occurrence Identity

**Status:** CONSOLIDATED

D13 define `occurrence_id` como a identidade determinística de uma ocorrência histórica específica de uma Cognitive Evidence.

### Occurrence Identity

`occurrence_id` MUST NOT ser tratado como sinônimo de `evidence_id`.

Uma mesma `evidence_id` MAY possuir múltiplas ocorrências históricas distintas, cada uma com seu próprio `occurrence_id`.

### Normative Occurrence Types

O vocabulário normativo inicial é:

- `OBSERVATION` — ocorrência na qual a evidência foi observada ou adquirida;
- `PRODUCTION` — ocorrência na qual uma representação foi produzida;
- `AVAILABILITY` — ocorrência na qual a evidência tornou-se disponível;
- `COMPOSITE` — ocorrência explicitamente composta por múltiplos eventos históricos.

`REGISTRATION` e `CONSUMPTION` são eventos de ciclo de vida e NÃO definem `occurrence_id` por si mesmos.

Um tipo desconhecido MUST NOT receber semântica de identidade implícita.

### Occurrence Identity Envelope

A entrada normativa de `occurrence_id` é composta por:

- `evidence_id`;
- `occurrence_type`;
- `type_version`;
- `normalized_occurrence_semantics`.

`normalized_occurrence_semantics` MUST conter somente dimensões constitutivas da ocorrência determinadas pelo tipo normativo.

Mapeamento temporal:

- `OBSERVATION` → `t_occurrence`;
- `PRODUCTION` → `t_production`;
- `AVAILABILITY` → `t_available`.

`occurrence_context` MAY ser constitutivo quando exigido pela semântica do tipo.

Para `COMPOSITE`, a estrutura dos componentes MUST ser preservada quando constitutiva da ocorrência.

### Excluded Identity Inputs

Os seguintes elementos NÃO definem `occurrence_id` por si mesmos:

- `t_registration`;
- `t_consumption`;
- Ledger `seq`;
- Ledger `tick`;
- `prev_hash`;
- `entry_hash`;
- ordem de registro;
- ordem de consumo;
- proveniência incidental;
- identidade ou concordância de LLM;
- diferenças puramente representacionais.

Correções ou novos eventos históricos MUST produzir novos artefatos históricos, sem reescrever ocorrências anteriores.

### Canonical Construction

A representação canônica MUST ser determinística e independente de Ledger, proveniência operacional ou estado interno de modelos externos.

`canonical_occurrence = canonical_json(occurrence_identity_envelope)`

`occurrence_id = SHA-256(UTF-8(canonical_occurrence))`

A normalização MUST ser governada pelo tipo e pela sua versão semântica.

### D13 Closure

D12 evidence identity is CLOSED.

D13 occurrence boundary is CLOSED.

D13 occurrence taxonomy is CONSOLIDATED.

D13 canonical occurrence representation is CLOSED.

D13 occurrence_id algorithm is SHA-256.

D13 occurrence_id is NORMATIVELY DEFINED.

Implementation is the next stage.

Tests MUST derive from this contract.

Tests MUST NOT convert implementation choices into normative semantic rules.

External LLMs or other models MAY provide hypotheses, analyses, transformations, or provenance-bearing input, but MUST NOT become canonical authority over Cognitive Evidence semantics.

## 21. Implementation Gate

**Status:** NEXT — CONTRACT COMPLETION SATISFIED

The normative prerequisites for Cognitive Evidence identity and
occurrence identity have been consolidated:

- semantic equivalence: D03-R02 / D10 CONSOLIDATED;
- typed constitutive semantics: D10 CONSOLIDATED;
- `evidence_id`: D12 CLOSED;
- `occurrence_id`: D13 NORMATIVELY DEFINED;
- canonical identity representation: CLOSED;
- canonical occurrence representation: CLOSED;
- deterministic canonical serialization: DEFINED;
- SHA-256 identity construction: DEFINED;
- temporal occurrence roles: DEFINED;
- Ledger and provenance exclusion boundaries: DEFINED.

Implementation MAY proceed only as an implementation of the normative
contract already established above.

Tests MUST derive from the normative contract.

Tests MUST NOT convert an implementation choice into a normative
semantic rule.

Implementation MUST NOT introduce execution authority, authorization
authority, retroactive mutation, implicit semantic equivalence, or
external-model canonical authority.

External LLMs or other models MAY provide hypotheses, analyses,
transformations, or provenance-bearing input, but MUST NOT become
canonical authority over Cognitive Evidence semantics.

Implementation remains subject to the existing TUU authorization and
architectural boundaries.

## 22. Architectural Boundary

A fronteira permanece:

`EVIDENCE → EPISTEMIC PROCESS → BELIEF UPDATE`

e não:

`EVIDENCE → EXECUTION`

A Cognitive Evidence não possui autoridade de execução.

