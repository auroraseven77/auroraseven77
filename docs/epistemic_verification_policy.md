# Epistemic & Metrological Verification Policy (TUU Engine)

**Versão:** 2.0.0-DEFENSIBLE  
**Status:** ESPECIFICAÇÃO DE REFERÊNCIA  
**Escopo:** TUU Core, Agente Guardião, Agente Sentinela e Camada de Execução Externa (Clássica / HPC / Quantum)

---

## 1. Princípios Fundamentais & Invariantes

1. **Zero-Trust Epistêmico**: Nenhuma intenção, hipótese, autorização ou simulação constitui evidência operacional sem telemetria direta, observável e verificável.
2. **Cadeia de Promoção Epistêmica**:
   $$\text{Proposição} \longrightarrow \text{Autorização} \longrightarrow \text{Preparação} \longrightarrow \text{Execução} \longrightarrow \text{Telemetria} \longrightarrow \text{Evidência Registrada}$$
3. **Verificação em Duas Camadas**:
   * **Camada Criptográfica (Sintática)**: Garante autenticidade, não-repúdio, integridade de trânsito e proveniência do hardware.
   * **Camada Metrológica (Semântica)**: Valida a qualidade física, estatística e experimental do fenômeno observado.

---

## 2. Formalização Matemática do Núcleo Decisório

### 2.1 Função de Pontuação Individual ($S_i$)
Para cada proposta $i \in \{1, \dots, n\}$ gerada pelo enxame:

$$S_i = \text{clamp}\left(0.4 C_i + 0.2 H_{\text{metric}, i} + 0.3 V_i + 0.1(1 - R_i),\, 0,\, 1\right)$$

Onde:
* $C_i$: Confiança da proposta ($[0,1]$).
* $H_{\text{metric}, i}$: Histórico de sucesso da hipótese/agente ($[0,1]$).
* $V_i$: Viabilidade técnica da ação ($[0,1]$).
* $R_i$: Risco estimado ($[0,1]$).

### 2.2 Distribuição de Probabilidade e Casos de Borda
A probabilidade relativa de cada proposta $p_i$ é definida por:

$$p_i = \frac{S_i}{\sum_{j=1}^n S_j}$$

* **Caso de Borda $\sum S_j = 0$**: Se todos os scores forem nulos, define-se $p_i = \frac{1}{n}$ para todos os $i$, forçando dispersão máxima ($H_N = 1.0, K_N = 0.0$) e acionando o estado `REJECTED` ou `RESOLVING`.

### 2.3 Entropia Normalizada ($H_N$) e Pontuação de Consenso ($K_N$)
A dispersão epistêmica do enxame é medida via Entropia Normalizada de Shannon ($H_N$):

$$H_N = \begin{cases} \frac{-\sum_{i=1}^n p_i \log_2 p_i}{\log_2 n} & \text{se } n \ge 2 \\ 0.0 & \text{se } n = 1 \end{cases}$$

O **Score de Consenso** ($K_N$) é formalmente definido como o complemento da entropia normalizada:

$$K_N = 1.0 - H_N$$

* $K_N = 1.0$: Consenso absoluto (uma única proposta concentrou a probabilidade).
* $K_N = 0.0$: Dispersão uniforme máxima (ausência de consenso).

### 2.4 Regra do Colapso e Limiares de Transição
Dada a régua de consenso $\tau_K \in (0, 1]$ e o score mínimo de confiança $S_{\min}$:

$$\begin{cases} K_N \ge \tau_K \;\land\; S_{i^*} \ge S_{\min} \implies \mathbf{consensus} \longrightarrow \text{Aprovar e Colapsar em } i^* \\ K_N < \tau_K \implies \mathbf{resolving} \longrightarrow \text{Retenção / Solicitação de Reavaliação (RETRY)} \\ S_{i^*} < S_{\min} \implies \mathbf{rejected} \longrightarrow \text{Rejeição Normativa por Baixa Qualidade} \end{cases}$$

Onde $i^* = \arg\max_i S_i$. Em caso de empate em $S_i$, o desempate é feito deterministicamente pelo menor índice $i$, respaldado pela ordem lexicográfica do digest SHA-256 da string canônica da intenção.

---

## 3. Especificação Criptográfica (Camada Sintática)

Para que a telemetria receba validação sintática, os artefatos de execução devem atender aos seguintes critérios:

```
+-----------------------------------------------------------------------------------+
| Artefato de Telemetria Criptograficamente Válido                                 |
+-----------------------------------------------------------------------------------+
| 1. JobID          : UUIDv4 vinculado ao ciclo de autorização                       |
| 2. Nonce          : Cryptographic Nonce 128-bit (Prevenção contra Replay)         |
| 3. Timestamp      : RFC 3339 UTC com janela de validade |t_now - t_exec| <= 500ms   |
| 4. HardwareID     : Identificador único do nó/controlador QPU                      |
| 5. Attestation    : Certificate Chain (TPM 2.0 Quote / HSM / QPU Controller)     |
| 6. Payload        : JCS RFC 8787 Canonical JSON (Raw Telemetry Data)              |
| 7. Signature      : Sign(K_sign, SHA-256(JobID || Nonce || Timestamp || ... ))     |
+-----------------------------------------------------------------------------------+
```

### 3.1 Separação de Chaves
* $\text{K}_{\text{sign}}$: Chave privada de assinatura mantida no enclave seguro do nó de execução.
* $\text{K}_{\text{id}}$: Chave de identidade da plataforma.
* $\text{K}_{\text{audit}}$: Chave de validação e auditoria pública mantida pelo Agente Sentinela.

---

## 4. Especificação Metrológica (Camada Semântica)

A aprovação sintática é condição necessária, porém insuficiente. A promoção para **Evidência Registrada** exige o cumprimento dos critérios numéricos metrológicos conforme o destino de execução:

| Domínio de Execução | Critério Metrológico | Limiar de Aceitação |
|---|---|---|
| **Quantum (QPU / VQE)** | Fidelidade de Porta de 2 Qubits ($F_{2Q}$) | $F_{2Q} \ge 99.2\%$ |
| | Taxa de Erro de Leitura ($\epsilon_{\text{readout}}$) | $\epsilon_{\text{readout}} \le 1.5\%$ |
| | Estabilidade Térmica / Deriva de Calibração ($\Delta_{\text{drift}}$) | Dentro da janela de variância estipulada |
| | Amostragem de Disparo ($N_{\text{shots}}$) | $N_{\text{shots}} \ge N_{\min}$ com erro estatístico $\sigma_{\langle H \rangle} < \delta$ |
| **HPC / Supercomputação** | Resíduo Relativo Numérico | $\frac{\Vert{}Ax - b\Vert{}}{\Vert{}b\Vert{}} < 10^{-8}$ |
| | Validação de Reprodutibilidade | Hash SHA-256 do checkpoint e validação da semente PRNG |
| **Clássico Determinístico** | Status de Saída do Processo | `exit_code == 0` |
| | Limites de Recursos | Cumprimento de restrições cgroups (CPU / RAM) |
| | Auditoria de Chamadas de Sistema | Conformidade estrita com o perfil seccomp e allowlist |

---

## 5. Máquina de Estados do Ciclo de Vida

```
[PROPOSED]
│
▼  (K_N >= tau_K AND S_i* >= S_min)
[AUTHORIZED]
│
▼  (Reserva de Hardware / Enclave Isolar)
[PREPARED]
│
▼  (Dispatch do Payload com Signed Nonce)
[SUBMITTED]
│
▼  (Processamento no Nó de Execução / QPU)
[EXECUTING]
│
▼  (Recepção do Payload Canônico JCS)
[TELEMETRY_RECEIVED]
│
├─── (Falha Criptográfica / Metrológica) ──► [QUARANTINED]
│
▼  (Passa na Verificação Criptográfica + Metrológica)
[EVIDENCE_REGISTERED]
```

### 5.1 Transições de Bloqueio e Exceção
* `RESOLVING`: Atingido quando $K_N < \tau_K$. Aciona o `FeedbackLoop` para reavaliação do enxame.
* `REJECTED`: Atingido quando a ação está fora da allowlist ou $S_{i^*} < S_{\min}$.
* `QUARANTINED`: Atingido quando a telemetria é recebida, mas falha na atestação criptográfica ou nos critérios metrológicos.
* `REVOKED`: Intervenção administrativa ou quebra de política de segurança durante a execução.

---

## 6. Persistência e Imutabilidade Forte

Para garantir imutabilidade do registro de auditoria além do ciclo de vida da memória do processo Python:

1. **Serialização Canônica**: Todo evento e resultado é convertido para RFC 8785 (JCS).
2. **Encadeamento Merkle (Hash Chain)**: Cada registro inclui o digest $H_k = \text{SHA-256}(H_{k-1} \parallel \text{Event}_k)$.
3. **Persistência Append-Only**: Gravação em armazenamento WORM (Write-Once-Read-Many) ou livro de razão (ledger) assinado.
