# Cognitive Core - Belief State Contract

**Status:** DRAFT / AUDIT

**Version:** 0.1

**Scope:** Cognitive Core Block 2

---

## 1. Objective

Definir o contrato minimo para representar o estado de crenca do Cognitive Core sem confundir crenca com fato, evidencia ou autorizacao.

O Belief State representa o estado epistemico atual do Cognitive Core.

Ele nao determina acoes e nao possui autoridade sobre o TUU.

---

## 2. Epistemic Separation

O sistema deve manter separadas:

- OBSERVATION — dado observado;
- EVIDENCE — evidencia utilizada para avaliacao;
- HYPOTHESIS — explicacao candidata;
- PREDICTION — consequencia prevista;
- BELIEF — estado de confianca atual sobre uma hipotese;
- INTERPRETATION — interpretacao derivada;
- ACTION_PROPOSAL — acao proposta;
- AUTHORIZATION — sentenca de autorizacao.

Uma crenca MUST NOT ser tratada como observacao ou fato.

---

## 3. Canonical Belief Object

A representacao canonica minima e:

```json
{
  "hypothesis_id": "<string>",
  "belief": <number>,
  "timestamp_logical": <integer>
}
```

Campos canonicos exclusivamente:

1. hypothesis_id
2. belief
3. timestamp_logical

Nenhum outro campo faz parte do objeto canonico nesta versao.

---

## 4. Belief Domain

`belief` MUST ser numero finito no intervalo:

`0.0 <= belief <= 1.0`

Sao invalidos:

- valores menores que 0.0;
- valores maiores que 1.0;
- NaN;
+Infinity;
-Infinity.

A API MUST rejeitar valores numericos invalidos.

---

## 5. Semantic Meaning

`belief` representa confianca epistemica operacional do Cognitive Core.

Nao significa:

- verdade objetiva;
- probabilidade fisica;
- garantia de resultado;
- autorizacao de acao;
- certeza metafisica.

Semantica probabilistica formal sera definida somente por contrato posterior.

---

## 6. BELIEF_UNRESOLVED

Uma hipotese pode existir sem uma crenca numerica resolvida.

`BELIEF_UNRESOLVED` e um estado epistemico valido do Cognitive Core.

`BELIEF_UNRESOLVED` nao e um valor do campo canonico `belief`.

Portanto, `BELIEF_UNRESOLVED` MUST NOT ser codificado como `0.0`, `1.0`, NaN, Infinity ou qualquer outro valor numerico.

O objeto canonico definido na Secao 3 representa somente um Belief State numericamente resolvido.

O estado `BELIEF_UNRESOLVED` pertence ao estado epistemico externo ao objeto canonico e nao deve ser incluido no hash de um Belief State resolvido.


---

## 7. State Updates

Block 2 define a representacao do estado, mas nao implementa inferencia Bayesiana.

Uma atualizacao futura MUST preservar a referencia ao estado anterior e criar um novo estado.

A atualizacao MUST produzir uma transicao que associe o estado anterior, o novo estado e a proveniencia correspondente.

A proveniencia da transicao MUST permanecer fora do objeto canonico do Belief State.

O estado anterior MUST NOT ser sobrescrito.

Historico anterior deve permanecer reconstruivel.

---

## 8. Temporal Ordering

Todo Belief State MUST possuir `timestamp_logical`.

Uma atualizacao posterior MUST possuir timestamp logico estritamente maior que o estado que ela sucede.

Uma tentativa de inserir uma atualizacao temporalmente anterior MUST ser rejeitada.

---

## 9. Immutability

Um estado de crenca comprometido e imutavel.

Uma revisao cria um novo estado temporalmente ordenado.

Nenhuma API de atualizacao pode alterar retroativamente o estado ja registrado.

---

## 10. Provenance

Atualizacoes futuras MUST identificar a evidencia, observacao ou evento que originou a transicao.

A proveniencia pertence ao envelope de transicao ou evento e nao aos tres campos do objeto canonico desta versao.

Uma justificativa criada somente depois do resultado nao pode ser usada para reescrever o estado anterior.

---

## 11. UNKNOWN

O Cognitive Core MUST suportar explicitamente `UNKNOWN` quando o estado do mundo nao puder ser determinado.

`UNKNOWN` e `BELIEF_UNRESOLVED` nao sao equivalentes a `0.0` ou `1.0`.

---

## 12. Cognitive / Authorization Separation

Belief State pertence ao Cognitive Core.

Ele MUST NOT:

- executar acoes;
- autorizar acoes;
- modificar contratos;
- escrever diretamente no Ledger;
- bypassar o TUU;
- alterar politicas de execucao.

A distincao normativa e:

`cognitive_state != authorization_state`

Uma crenca alta nao implica permissao.
Uma crenca baixa nao implica proibicao automatica.

---

## 13. Determinism

Dados os mesmos `hypothesis_id`, `belief` e `timestamp_logical`, deve ser produzida a mesma representacao canonica.

Nenhuma informacao externa implicita pode ser adicionada ao objeto canonico.

---

## 14. Canonical Hash Boundary

Caso um hash seja utilizado futuramente para comprometer um Belief State, ele deve cobrir exclusivamente o objeto canonico da Secao 3.

Metadados do Ledger nao fazem parte do hash do Belief State.

Block 2 nao cria novo mecanismo criptografico.

---

## 15. Invalid Evidence

Evidencia considerada invalida nao deve produzir alteracao retroativa silenciosa.

A consequencia deve ser registrada como nova transicao de estado.

O historico anterior MUST permanecer intacto.

---

## 16. Post-Hoc Rationalization

Nao e permitido:

1. observar o resultado;
2. alterar retroativamente a crenca anterior;
3. registrar a crenca alterada como se fosse a original.

Uma revisao deve aparecer como novo estado temporalmente ordenado.

---

## 17. Non-Goals

Este bloco nao implementa:

- inferencia Bayesiana;
- likelihood;
- prior ou posterior;
- calibracao;
- learning;
- error attribution;
- active inference;
- action selection;
- action authorization;
- integracao com LLM;
- integracao quantica;
- modificacao do TUU;
- modificacao do Ledger;
- nova persistencia;
- nova primitiva criptografica.

---

## 18. Required Tests

A implementacao futura deve testar, no minimo:

1. criacao de Belief State valido;
2. rejeicao de belief < 0;
3. rejeicao de belief > 1;
4. rejeicao de NaN;
5. rejeicao de Infinity;
6. preservacao de hypothesis_id;
7. preservacao de timestamp_logical;
8. suporte a BELIEF_UNRESOLVED;
9. imutabilidade;
10. criacao de novo estado em update;
11. rejeicao de rollback temporal;
12. separacao cognitiva/autorizacao;
13. determinismo da representacao canonica;
14. ausencia de metadados do Ledger no objeto canonico;
15. ausencia de mutacao retroativa.

---

## 19. Acceptance Criteria

Block 2 sera considerado definido quando:

- o objeto canonico estiver definido;
- o dominio de belief estiver definido;
- BELIEF_UNRESOLVED estiver explicitamente permitido;
- a ordem temporal estiver definida;
- a imutabilidade estiver definida;
- a proveniencia estiver separada do objeto canonico;
- a separacao Cognitive Core / TUU estiver preservada;
- os testes especificados estiverem cobertos;
- nenhuma inferencia Bayesiana ou learning prematuro tiver sido introduzido.

---

## 20. Authority Statement

The Belief State defines epistemic representation. It does not grant operational authority.


Cognitive Core
      |
      v
  proposal
      |
      v
     TUU
      |
      v
authorization
      |
      v
HEPHAESTUS

O Belief State pode influenciar uma proposta, mas nunca substitui a autorizacao do TUU.
