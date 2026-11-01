# 🛡️ Security Boundaries

O OSINT Toolkit foi desenhado para pesquisa, defesa e auditoria autorizada.

## Permitido

- coleta de informações publicamente acessíveis;
- análise de ativos próprios ou autorizados;
- consultas passivas a provedores de inteligência;
- validação de configurações e exposição em ambientes controlados;
- geração de evidências e relatórios reproduzíveis.

## Não permitido pelo projeto

- exploração de vulnerabilidades sem autorização;
- tentativa de obter credenciais, tokens ou dados privados;
- bypass de autenticação ou controles de acesso;
- coleta invasiva de dados pessoais;
- varredura ativa de terceiros sem autorização;
- automação de ações destrutivas ou de intrusão.

## Princípio de execução

```text
PUBLIC DATA
    ↓
AUTHORIZED SCOPE
    ↓
COLLECTION
    ↓
EVIDENCE
    ↓
ANALYSIS
    ↓
HUMAN REVIEW
    ↓
AUTHORIZED ACTION
```

A IA pode classificar, resumir e correlacionar evidências, mas não recebe autoridade implícita para executar ações operacionais.


## Reporting a vulnerability

Do not publish credentials, personal information, raw target evidence, or a reproducible exploit against a third-party system in a public issue. Use GitHub private vulnerability reporting if enabled for this repository. If unavailable, contact the repository owner through an established private channel and provide only minimum sanitized details.

Include the affected commit, file/version/environment, a minimal synthetic reproduction or sanitized test, impact/prerequisites/scope, and a proposed mitigation if known.

## Current limitation

The maintainers must verify whether GitHub private vulnerability reporting or another private contact route is actually available. This document does not claim that such a route is configured.
