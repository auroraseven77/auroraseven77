# TUU / Aurora — Documentação Técnica e Científica do Projeto

> **Status do documento:** documentação de referência da linha B1.
>
> **Repositório:** `auroraseven77/auroraseven77`
>
> **Base estável:** `main` em `4f5e709f20d6a1f38d6ac20bdfcb6b40688b12f5`
>
> **B1.3 em revisão:** PR #7, commit `00c371d`, branch `feat/b1.3-energy-validation-harness`.

---

## 1. Visão geral

O projeto TUU — **Teoria da Unidade Unificada** — é uma linha de pesquisa e engenharia que procura transformar uma hipótese conceitual sobre unidade, coerência, interação e emergência em modelos computacionais que possam ser **explicitamente definidos, reproduzidos, auditados e falsificados**.

Aurora é o nome operacional associado ao ecossistema de implementação. Neste repositório, a linha B1 concentra uma investigação computacional sobre:

- sistemas quânticos simulados;
- Hamiltonianos do tipo TFIM;
- estados representados por MPS (Matrix Product States);
- circuitos variacionais;
- energia de estados quânticos;
- diagonalização exata como referência independente;
- truncamento de dimensão de vínculo;
- validação experimental reprodutível;
- e, na etapa seguinte, otimização variacional e gradientes.

O princípio metodológico central é:

> **Uma hipótese da TUU não deve ser aceita porque produz uma narrativa coerente. Ela deve produzir uma definição operacional, uma previsão mensurável e um teste capaz de mostrar que a hipótese está errada.**

Por isso, o projeto separa deliberadamente:

1. teoria;
2. modelo matemático;
3. implementação;
4. referência independente;
5. experimento;
6. evidência;
7. interpretação.

Essa separação é fundamental para que resultados positivos não sejam confundidos com confirmação automática da teoria.

---

# 2. Como a linha B1 surgiu da TUU

A TUU começou como uma tentativa de investigar se propriedades de **unidade, coerência e interação entre componentes** poderiam ser expressas de forma quantitativa.

A tradução para computação segue uma cadeia conceitual:

```
TUU
 │
 ├── unidade / interação / coerência
 │
 ├── modelo matemático
 │
 ├── sistema físico/computacional controlado
 │
 ├── observáveis mensuráveis
 │
 ├── experimento reproduzível
 │
 └── hipótese potencialmente falsificável
```

A linha B1 transforma essa ideia em um laboratório computacional mínimo.

O sistema quântico escolhido não é apresentado como prova da TUU. Ele funciona como **ambiente controlado para testar mecanismos matemáticos que a teoria pretende investigar**.

O TFIM fornece:

- graus de liberdade discretos;
- interações locais;
- campo externo;
- energia bem definida;
- Hamiltoniano explícito;
- possibilidade de referência exata em sistemas pequenos;
- e possibilidade de aproximação MPS em sistemas maiores.

Assim, a TUU fornece a motivação conceitual, enquanto o código fornece o mecanismo de teste.

---

# 3. O que já está pronto

A linha B1 já possui uma fundação experimental em camadas.

## 3.1 Motor MPS

O arquivo crítico é:

```
b1_motor/mps.py
```

Ele implementa a representação MPS usada pelo experimento.

Características relevantes:

- tensores na forma `[chi_left, 2, chi_right]`;
- números complexos em `complex128`;
- dimensão de vínculo configurável;
- aplicação de operações locais;
- aplicação de CNOT entre vizinhos;
- truncamento controlado por `chi_max`;
- corte de valores singulares abaixo de `epsilon_trunc = 1e-8`;
- cálculo da massa quadrática descartada.

Este arquivo é tratado como **produção crítica** e permanece congelado durante B1.3.

SHA-256 validado:

```
32bba8dbf2f878e1977616430252d1cd1879f88f68cba549fde69669bbd921bc
```

Nenhuma alteração da B1.3 foi feita nesse arquivo.

---

# 4. Hamiltoniano B1.2

O contrato físico/computacional anterior está em:

```
b1_motor/hamiltonian_b12.py
```

Parâmetros estruturais:

```
B12_N_QUBITS = 64
B12_BOND_DIM = 128
B12_J = 1.0
B12_H = 1.0
B12_AGENT_COUPLING = 0.5
```

O Hamiltoniano possui:

- 64 qubits;
- 63 interações consecutivas (Z_iZ_{i+1});
- 64 termos de campo (X_i);
- dois termos de interface:
  - (0.5 Z_{21}Z_{22})
  - (0.5 Z_{43}Z_{44}).

Total:

```
63 + 64 + 2 = 129 termos
```

Um ponto importante do contrato B1.2 é que os sinais globais do TFIM **não estavam definidos no manifesto como uma escolha experimental única**.

Por isso, a função de construção recebe explicitamente:

```
TFIMSignConvention(
    interaction_sign=...,
    field_sign=...,
)
```

Isso impede que uma convenção seja introduzida silenciosamente pela implementação.

---

# 5. Ansatz variacional

O circuito está em:

```
b1_motor/ansatz_b12.py
```

A implementação é `SymmetricVQEAnsatz`.

Características:

- 3 camadas;
- RY e RZ em cada qubit;
- cadeia linear de CNOT;
- parâmetros determinísticos quando uma seed é fornecida;
- validação de dimensão;
- rejeição de parâmetros não finitos;
- possibilidade de executar sobre um MPS existente.

Para (N) qubits:

```
parâmetros = 6N
```

Portanto:

- N=4 → 24 parâmetros;
- N=6 → 36 parâmetros;
- N=8 → 48 parâmetros;
- N=64 → 384 parâmetros.

As matrizes utilizadas pelo motor MPS são reproduzidas independentemente na referência densa B1.3.

---

# 6. Energia

O contrato energético está em:

```
b1_motor/vqe_b12.py
```

A API principal retorna:

```
EnergyEvaluation
```

contendo:

- energia;
- estado MPS;
- massa quadrática descartada;
- número de truncamentos efetivos.

A avaliação segue:

```
theta
  ↓
ansatz
  ↓
MPS
  ↓
Hamiltoniano
  ↓
<E|H|E>
  ↓
EnergyEvaluation
```

Para sistemas pequenos, a API deve receber explicitamente um:

```
SymmetricVQEAnsatz(n_qubits=N)
```

Isso evita que o ansatz padrão de 64 qubits seja utilizado inadvertidamente.

---

# 7. B1.3 — a camada de validação independente

A B1.3 adiciona uma segunda camada de confiança.

Arquivos:

```
b1_motor/b13/__init__.py
b1_motor/b13/dense_reference.py
b1_motor/b13/ed_reference.py
b1_motor/b13/sign_contract.py
```

Testes:

```
b1_motor/tests/test_b13_energy_validation.py
b1_motor/tests/test_ed_reference_b13.py
b1_motor/tests/test_ed_tfim_contract_b13.py
```

A B1.3 não modifica o motor MPS.

---

# 8. Oráculo ED

```
b1_motor/b13/ed_reference.py
```

O módulo implementa uma referência independente por matriz densa e diagonalização exata.

Uma característica deliberada é:

> **O ED não importa `b1_motor.mps`.**

Isso é importante porque evita validar uma implementação comparando-a contra outra implementação que compartilha a mesma origem de erro.

O ED:

1. constrói operadores Pauli;
2. constrói termos locais;
3. constrói termos de dois sítios;
4. monta a matriz Hamiltoniana;
5. verifica hermiticidade;
6. usa `numpy.linalg.eigvalsh`;
7. retorna espectro ordenado;
8. registra a energia fundamental.

Para sistemas pequenos, essa referência funciona como oracle computacional.

---

# 9. Referência densa do circuito

```
b1_motor/b13/dense_reference.py
```

A referência densa implementa independentemente:

- RY;
- RZ;
- CNOT;
- aplicação de porta de um qubit;
- aplicação de CNOT;
- normalização;
- cálculo da energia.

Ela reproduz o mesmo circuito do ansatz MPS, mas sem utilizar o motor MPS.

Isso permite comparar:

```
mesmos parâmetros
       ↓
 ┌───────────────┐
 │               │
 MPS           DENSE
 │               │
 E_MPS         E_dense
 │               │
 └───────┬───────┘
         ↓
     diferença
```

---

# 10. Contrato de sinais B1.3

A B1.3 fixa explicitamente:

```
interaction_sign = -1
field_sign       = -1
```

Arquivo:

```
b1_motor/b13/sign_contract.py
```

Portanto, a comparação experimental utiliza:

```
H = -J Σ Z_i Z_{i+1}
    -h Σ X_i
    + termos de interface quando aplicáveis
```

Essa escolha pertence ao **experimento B1.3**.

Ela não reescreve o contrato histórico B1.2.

Essa distinção evita misturar:

- especificação original;
- convenção experimental;
- e resultado observado.

---

# 11. Separação dos erros

Uma das partes mais importantes da B1.3 é a separação conceitual dos erros.

Para um conjunto de parâmetros (	heta):

### Erro de truncamento

```
|E_MPS(theta, chi) - E_dense(theta)|
```

Mede o efeito da aproximação MPS para aquele mesmo estado/circuito.

### Erro variacional

```
|E_dense(theta) - E_ground|
```

Mede a distância do estado produzido pelo circuito até a energia fundamental do Hamiltoniano.

### Erro total em relação ao ground state

```
|E_MPS(theta, chi) - E_ground|
```

Combina os dois efeitos.

Essas grandezas não devem ser confundidas.

Em particular:

> A massa quadrática descartada durante truncamento é uma métrica interna do MPS; ela não deve ser apresentada automaticamente como um limite superior universal para o erro energético.

---

# 12. Resultados B1.3 já obtidos

Seed determinística utilizada:

```
20260921
```

Para N=4 e chi=8:

```
E_MPS       = -0.725203732378657
E_dense     = -0.7252037323786601
E_ground    = -4.758770483143637

|MPS-DENSE|  ≈ 3.11e-15
```

Não houve truncamento efetivo.

Resultado:

```
MPS ↔ DENSE SAME-THETA = PASS
```

Foram também observados os seguintes comportamentos experimentais:

| Sistema | chi | Diferença MPS-denso |
|---|---:|---:|
| N=4 | 2 | ~8.17e-3 |
| N=4 | 4 | ~3.11e-15 |
| N=6 | 2 | ~5.34e-1 |
| N=6 | 4 | ~1.80e-1 |
| N=6 | 8 | ~1.76e-15 |
| N=8 | 2 | ~1.83e-1 |
| N=8 | 4 | ~2.83e-2 |
| N=8 | 8 | ~1.83e-15 |

Esses números são resultados dos circuitos determinísticos testados.

Eles **não constituem um teorema geral sobre a dimensão de vínculo mínima necessária**.

---

# 13. Testes

A suíte B1.3 possui:

```
34 testes
```

Resultado local registrado:

```
34 passed
```

A suíte inclui:

- validação do ED;
- contratos do TFIM;
- independência da referência;
- normalização;
- determinismo;
- comparação MPS/denso;
- comportamento sob truncamento;
- separação entre erro variacional e erro de truncamento.

O PR #7 é:

```
test(b1.3): add dense energy validation harness
```

Commit:

```
00c371d
```

Branch:

```
feat/b1.3-energy-validation-harness
```

---

# 14. Estado atual do GitHub

O PR #7 foi aberto contra `main`.

Objetivo:

- oficializar a B1.3;
- permitir revisão independente;
- executar CI;
- verificar Python 3.11;
- verificar Python 3.12;
- confirmar o diff;
- manter `main` intacta até o aceite.

O diff esperado da B1.3 é de 7 arquivos:

```
b1_motor/b13/__init__.py
b1_motor/b13/dense_reference.py
b1_motor/b13/ed_reference.py
b1_motor/b13/sign_contract.py
b1_motor/tests/test_b13_energy_validation.py
b1_motor/tests/test_ed_reference_b13.py
b1_motor/tests/test_ed_tfim_contract_b13.py
```

`b1_motor/mps.py` deve permanecer fora do diff.

---

# 15. Como usar a infraestrutura

## Executar a validação B1.3

No clone local:

```bash
cd ~/auroraseven77-b13-energy

PYTHONPATH="$PWD" \
/data/data/com.termux/files/usr/bin/python -m pytest \
  b1_motor/tests/test_ed_reference_b13.py \
  b1_motor/tests/test_ed_tfim_contract_b13.py \
  b1_motor/tests/test_b13_energy_validation.py \
  -q
```

Resultado esperado no estado validado:

```
34 passed
```

## Verificar a integridade do MPS

```bash
sha256sum b1_motor/mps.py
```

Hash esperado:

```
32bba8dbf2f878e1977616430252d1cd1879f88f68cba549fde69669bbd921bc
```

## Verificar o diff do B1.3

```bash
git diff --stat main...HEAD
git diff --name-only main...HEAD
```

---

# 16. Para que o projeto pode ser usado

A infraestrutura atual pode servir como laboratório para:

### 16.1 Pesquisa de métodos variacionais

Testar circuitos variacionais e observar como:

- parâmetros alteram a energia;
- o bond dimension altera a aproximação;
- o truncamento afeta o resultado;
- diferentes estratégias de otimização convergem.

### 16.2 Validação de implementações MPS

A referência densa fornece um mecanismo independente para testar o motor MPS em sistemas pequenos.

Isso permite detectar regressões sem depender somente de testes internos.

### 16.3 Estudos de convergência

É possível variar:

```
chi
n_qubits
theta
seed
número de camadas
```

e medir os efeitos separadamente.

### 16.4 Estudos da TUU

A infraestrutura pode futuramente testar hipóteses operacionalizadas da TUU desde que cada hipótese produza:

- variável definida;
- observável;
- previsão;
- critério de falsificação;
- experimento;
- controle;
- registro de resultado.

### 16.5 Base para B2

A próxima camada natural é o Loop Variacional:

```
theta
 ↓
E(theta)
 ↓
gradient
 ↓
update(theta)
 ↓
novo E(theta)
 ↓
convergência / falha
```

A B1.3 fornece a infraestrutura para verificar se a função de custo usada nesse loop está correta antes de otimizar.

---

# 17. O que ainda NÃO está pronto

A documentação deve registrar explicitamente as fronteiras.

Ainda não está estabelecido:

- que o ansatz encontra o ground state global;
- que os mínimos encontrados são globais;
- que um determinado (chi) é universalmente suficiente;
- que a TUU foi comprovada;
- que o TFIM representa toda a estrutura física pretendida pela TUU;
- que resultados de sistemas pequenos escalam automaticamente para 64 qubits;
- que a massa descartada seja um bound energético universal;
- que a próxima otimização tenha convergência garantida.

Também ainda não é o momento de congelar um algoritmo de otimização como parte do contrato científico.

Essas questões pertencem às etapas posteriores.

---

# 18. Próxima fronteira: B2

A B2 deverá introduzir o Loop Variacional e os gradientes.

A arquitetura conceitual será:

```
Hamiltoniano
     │
     ▼
Ansatz(theta)
     │
     ▼
Estado
     │
     ▼
E(theta)
     │
     ▼
Gradient(theta)
     │
     ▼
Optimizer
     │
     ▼
theta_new
     │
     └──────────────► E(theta_new)
```

Mas a B2 deverá preservar o princípio da B1.3:

> **Primeiro validar a medição; depois otimizar a medição.**

Antes de qualquer implementação de gradiente, deverão ser definidos:

1. qual derivada está sendo calculada;
2. qual método de gradiente será utilizado;
3. referência independente para o gradiente;
4. tolerância numérica;
5. tratamento de truncamento;
6. critério de convergência;
7. critério de divergência;
8. número máximo de iterações;
9. seed;
10. métricas de reproducibilidade.

---

# 19. Relação com Aurora e agentes externos

Aurora não deve ser confundida com autoridade científica automática.

O princípio arquitetural estabelecido no ecossistema TUU é:

```
Dados
  ↓
evidência
  ↓
análise
  ↓
hipótese
  ↓
experimento
  ↓
resultado
  ↓
decisão humana/política de execução
```

Modelos externos podem atuar como:

- consultores;
- revisores;
- geradores de hipóteses;
- auxiliares de planejamento;
- segunda opinião.

Eles não devem transformar uma sugestão probabilística em evidência experimental.

---

# 20. Papel do Empire LLM for Codex

O Empire deve ser utilizado como **camada de segunda opinião**, mantendo o Codex como agente líder e autoridade de implementação.

Fluxo recomendado:

```
Codex
  │
  ├── define escopo
  │
  ├── seleciona evidências mínimas
  │
  ▼
Empire / modelo externo
  │
  ├── crítica
  ├── hipóteses
  ├── riscos
  └── sugestões
  │
  ▼
Codex
  │
  ├── verifica
  ├── testa
  ├── rejeita ou incorpora
  └── implementa
```

Uma resposta externa nunca deve ser tratada como alteração automática do repositório.

Isso mantém:

- rastreabilidade;
- isolamento;
- revisão humana;
- controle de custo;
- separação entre sugestão e execução.

---

# 21. O princípio científico da linha B1

A contribuição mais importante da B1 não é apenas o código.

É a disciplina de separar três coisas:

```
O QUE A TEORIA DIZ
        ↓
O QUE O MODELO IMPLEMENTA
        ↓
O QUE O EXPERIMENTO REALMENTE MOSTROU
```

Essa separação impede que uma coincidência numérica seja convertida em confirmação teórica.

A linha B1 transforma a TUU em uma sequência de contratos testáveis.

---

# 22. Critério de passagem B1 → B2

O aceite da B1.3 deve exigir:

- CI verde em Python 3.11 e 3.12;
- 34/34 testes;
- ED independente do MPS;
- referência densa independente;
- contrato de sinais explícito;
- diff limitado aos 7 arquivos esperados;
- `mps.py` inalterado;
- SHA preservado;
- distinção formal dos erros;
- nenhuma extrapolação dos resultados experimentais para teoremas gerais.

Somente depois disso a B2 deve começar.

---

# 23. Estado resumido

```
TUU
 │
 ├── conceito
 │
 ├── hipóteses operacionalizáveis
 │
 └── laboratório computacional
        │
        └── B1
             │
             ├── Hamiltoniano B1.2       [PRONTO]
             ├── MPS                     [PRONTO / CONGELADO]
             ├── Ansatz                  [PRONTO]
             ├── Energia                 [PRONTO]
             ├── ED independente         [B1.3]
             ├── referência densa        [B1.3]
             ├── contrato de sinais      [B1.3]
             ├── validação energética    [B1.3]
             └── 34 testes               [PASS LOCAL]
                    │
                    ▼
                 PR #7
                    │
                    ▼
              CI + revisão
                    │
                    ▼
                   B2
                    │
                    ├── gradientes
                    ├── loop variacional
                    ├── otimização
                    └── estudos de convergência
```

---

## Conclusão

O estado atual representa uma fundação experimental, não uma alegação de prova da TUU.

A principal realização da linha B1 é ter transformado uma parte da hipótese em uma infraestrutura onde as afirmações podem ser confrontadas com referências independentes.

A sequência metodológica permanece:

> **teoria → formalização → implementação → referência independente → experimento → evidência → revisão → nova hipótese.**

Esse ciclo é a base para que futuras descobertas atribuídas à TUU sejam sustentadas por evidência reproduzível, e também para que resultados negativos sejam preservados como informação científica em vez de serem ocultados.

**B1.3 deve permanecer congelada até o encerramento da revisão do PR #7.**
