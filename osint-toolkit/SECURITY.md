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
