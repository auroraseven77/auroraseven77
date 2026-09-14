# 🔎 OSINT Toolkit

Toolkit modular de **OSINT, reconhecimento e auditoria autorizada**, integrado ao ecossistema TUU/Aurora.

> ⚠️ Use somente em ativos próprios, laboratórios ou alvos com autorização explícita. Dados públicos não significam autorização para exploração.

## MVP executável

O pacote `0.1.0` implementa somente coleta conservadora:

- DNS: A, AAAA, MX, TXT, NS e CNAME.
- HTTP: uma requisição `HEAD`, sem payload, autenticação ou crawling.
- `robots.txt`: uma leitura direta e parsing local.
- TLS: handshake normal em 443, certificado, SAN e validade.
- Evidence: artefatos content-addressed por SHA-256.
- Policy: alvo precisa pertencer explicitamente ao escopo autorizado.
- Correlator TUU: agrupa observações e gera `report.json` com confiança, risco e revisão humana.

Não há exploração, brute force, AXFR, enumeração de subdomínios, bypass de autenticação ou crawling automático.

## Instalação

```bash
pip install -e .
```

## Uso

O escopo autorizado é obrigatório:

```bash
osint-toolkit run example.com --allow example.com
osint-toolkit run https://example.com --allow example.com -o observations.jsonl
osint-toolkit report -i observations.jsonl -o report.json
osint-toolkit show -o observations.jsonl
pytest -q
```

Subdomínios são aceitos somente quando o domínio pai estiver explicitamente no allow-list. Sem escopo autorizado, a execução é negada.

## Arquitetura

```text
OSINT Toolkit
│
├── Policy
│   └── authorized scope
├── DNS
│   └── passive records
├── Web
│   ├── HEAD headers
│   └── robots.txt
├── TLS
│   ├── certificate
│   ├── SAN
│   └── validity
├── Evidence
│   └── SHA-256 content-addressed artifacts
├── Normalized Observations
│   └── observation.schema.json
└── TUU Correlator
    ├── grouping
    ├── confidence composite
    ├── risk
    └── human review gate
```

## Modelo normalizado

Todos os coletores convergem para o mesmo contrato:

```json
{
  "source": "dns",
  "timestamp": "2026-01-01T00:00:00Z",
  "target": "example.org",
  "entity_type": "dns",
  "value": "A 93.184.216.34",
  "confidence": 0.9,
  "evidence_url": null,
  "hash": null,
  "status": "ok"
}
```

O contrato canônico está em [`schema/observation.schema.json`](schema/observation.schema.json).

## Evidência e eMMC

O evidence store usa SHA-256 como endereço de conteúdo e não reescreve um artefato que já existe. O pipeline usa JSONL append-only, mantendo a persistência simples e adequada a ambientes como Termux; uma futura implementação SQLite pode atuar como índice/event store, sem substituir o artefato bruto.

## Correlator TUU

```text
observations.jsonl
        ↓
   load + validate
        ↓
 group(target, entity_type)
        ↓
confidence_composite + risk
        ↓
 human_review_required
        ↓
     report.json
```

O cálculo de risco no MVP é deliberadamente heurístico e **não representa uma conclusão de segurança**. Ele serve como sinal de triagem. O relatório também marca explicitamente `ai_authority: advisory_only`.

## Protocolo de validação quântica

A ponte entre o pré-processamento clássico e a hipótese quântica agora possui um protocolo explícito em [`docs/TUU_QUANTUM_VALIDATION_PROTOCOL.md`](docs/TUU_QUANTUM_VALIDATION_PROTOCOL.md).

A regra é separar obrigatoriamente quatro classes de informação:

```text
INPUT → ANALYTICAL → SIMULATION → EXPERIMENT
```

Resultados de raciocínio ou simulação **não são evidência de hardware**. Um resultado só pode ser classificado como `EXPERIMENT` quando houver backend identificado, timestamp, circuito/commit, qubits usados, profundidade, gates, shots, protocolo de medição, parâmetros do experimento, artefatos preservados e hashes SHA-256, além de baseline e incerteza estatística.

O protocolo também impede que `56 qubits físicos` seja automaticamente interpretado como `56 qubits lógicos` e exige que o overhead de codificação/ancillas seja explicitado.

## Arquitetura ampliada

```text
DNS
 ├── WHOIS
 ├── DNS records
 └── subdomains

Web
 ├── headers
 ├── TLS / SAN / validade
 ├── technologies
 └── robots.txt

Network
 ├── authorized Nmap
 ├── Shodan
 └── Censys

Identity
 ├── username
 ├── email intelligence
 └── entity correlation

Evidence
 ├── timestamp
 ├── source
 ├── hash
 └── confidence

AI
 ├── classification
 ├── summarization
 ├── correlation
 └── report generation
```

Os módulos futuros de Network e Identity permanecem separados do MVP e devem preservar a distinção entre **observação passiva** e **sondagem ativa autorizada**.

## Fluxo TUU/Aurora

```text
Collector
   ↓
Policy / Authorized Scope
   ↓
Normalizer
   ↓
Evidence Store
   ↓
Correlation Engine
   ↓
AI Analysis (advisory only)
   ↓
Quantum Validation Protocol
   ↓
Risk / Confidence
   ↓
Human Review
   ↓
Report
```

A IA não recebe autoridade operacional implícita. Conclusões devem permanecer rastreáveis às observações e às evidências que as sustentam.
