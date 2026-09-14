# 🔎 OSINT Toolkit

Arquitetura modular para **OSINT, reconhecimento e auditoria autorizada**, integrada ao ecossistema TUU/Aurora.

> ⚠️ Use somente em ativos próprios, laboratórios ou alvos com autorização explícita. Dados públicos não significam autorização para exploração.

## Arquitetura

```text
OSINT Toolkit
│
├── DNS
│   ├── WHOIS
│   ├── DNS records
│   └── subdomains
│
├── Web
│   ├── headers
│   ├── TLS / SAN / validade
│   ├── technologies
│   └── robots.txt
│
├── Network
│   ├── authorized Nmap
│   ├── Shodan
│   └── Censys
│
├── Identity
│   ├── username
│   ├── email intelligence
│   └── entity correlation
│
├── Evidence
│   ├── timestamp
│   ├── source
│   ├── hash
│   └── confidence
│
└── AI
    ├── classification
    ├── summarization
    ├── correlation
    └── report generation
```

## 🧩 Modelo normalizado

Todos os adaptadores devem convergir para um formato comum, facilitando correlação e auditoria:

```json
{
  "source": "provider-or-tool",
  "query": "authorized-target",
  "timestamp": "ISO-8601",
  "target": "example.org",
  "entity_type": "domain",
  "value": "example.org",
  "confidence": 0.0,
  "evidence_url": "https://example.org/source",
  "hash": "sha256",
  "status": "observed"
}
```

## 📡 DNS

Responsável por descoberta e contextualização de domínio:

- WHOIS: registro e metadados disponíveis publicamente.
- DNS records: A, AAAA, MX, NS, TXT, CNAME e outros registros relevantes.
- Subdomains: descoberta passiva e validação de nomes autorizados.

## 🌐 Web

Camada para caracterizar serviços HTTP/HTTPS sem exploração:

- Headers: políticas, servidores e metadados HTTP.
- TLS/SAN/validade: certificado, nomes alternativos e período de validade.
- Technologies: identificação de tecnologias expostas publicamente.
- robots.txt: leitura das diretivas publicadas pelo próprio site.

## 🌍 Network

- Nmap: somente descoberta/auditoria em redes autorizadas.
- Shodan: inteligência baseada em dados de dispositivos e serviços observados na Internet.
- Censys: descoberta e contextualização de ativos Internet.

A integração deve separar claramente **observação passiva** de **sondagem ativa autorizada**.

## 🪪 Identity

Módulo destinado a correlação de identificadores públicos:

- username: pesquisa de presença pública de identificadores.
- email intelligence: somente informações públicas e não invasivas associadas ao identificador.
- entity correlation: relacionamento entre entidades, fontes e evidências.

Não armazenar credenciais, tokens, dados privados obtidos indevidamente ou informações sem finalidade legítima.

## 🧾 Evidence

Cada observação deve ser rastreável:

1. timestamp da coleta;
2. fonte/provedor;
3. alvo e consulta;
4. evidência de origem;
5. hash do artefato quando aplicável;
6. nível de confiança;
7. status da observação.

Isso permite reprodutibilidade, deduplicação e revisão humana.

## 🤖 AI

A IA funciona como **assistente de análise**, não como autoridade operacional:

- classification — classificar observações;
- summarization — resumir grandes volumes de resultados;
- correlation — sugerir relações entre entidades;
- report generation — produzir relatórios rastreáveis.

Qualquer ação operacional deve passar por política local e supervisão humana.

## 🔗 Integração com TUU/Aurora

```text
Collector
   ↓
Normalizer
   ↓
Evidence Store
   ↓
Correlation Engine
   ↓
AI Analysis
   ↓
Risk / Confidence
   ↓
Human Review
   ↓
Report
```

O objetivo é manter a coleta modular, os dados auditáveis e as conclusões separadas das ações.
