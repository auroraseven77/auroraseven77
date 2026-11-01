# Aurora Evidence Ledger 01 — estado do artefato TELOS

**Data de referência:** 2026-10-26  
**Estado:** pacote testado no sandbox; teste isolado do pacote em Termux reportado pelo operador; setup persistente e integração TUU/SQLite/WAL ainda não verificados.

## Artefatos locais entregues no chat

| Artefato | SHA-256 | Estado |
|---|---|---|
| `aurora-evidence-ledger-v0.1.0.zip` | `d48b5b1ce57a69174256fad294a311ee0e0a2d4b62c655c6132dd398ec2be3d7` | pacote completo do protótipo |
| `github-evidence-ledger-source.zip` | `621d2589d6f2663e87e31cad683fab6275feee6113d0a497109aed565aa9550c` | pacote de fontes para revisão |
| `PROJECT_TRIAGE.md` (snapshot do sandbox) | `5c8ff53b81976b3fbdbd012c03eaac5af330df2e6e10be5a55be69eedbc6b1b6` | inventário local completo |
| `GITHUB_INVENTORY.json` | `4cb028ae6981de3dbac5f84a2578e891f15d191d069d4ed2a79d8ed5fac0e06c` | metadados e limites observados |

Os ZIPs estão anexados ao turno ChatGPT para download; este documento **não afirma** que os bytes desses ZIPs já foram publicados no GitHub. O branch GitHub desta PR contém o relatório de triagem, não o pacote binário, porque o conteúdo remoto precisa ser verificado byte a byte antes de ser referenciado.

## Verificações executadas localmente

- Runtime observado: Python 3.13.5, CPython, Linux x86_64.
- Testes: `python3 -m unittest discover -s tests -v` — 16/16 passaram; código de saída 0.
- Exemplo: `python3 evidence_ledger.py verify examples/cerberus3_pending.jsonl` — `valid=true`, 1 evento.
- Manifesto SHA-256 do pacote verificado localmente.
- Nenhuma alteração no `~/tuu/data/tuu.db`; nenhuma execução no Termux ou Snowflake.

## Validação isolada em Termux reportada pelo operador (2026-10-26)

- Arquivo de handoff: `aurora_telos_20261026.zip`.
- SHA-256 reportado e conferido no transcript: `d7dfd98da8ad9c7c6f3b27b29ec5347ff90cebee05de1f36d64c850246110d8d`.
- CRC e caminhos do ZIP: aprovados segundo a saída fornecida.
- Testes do pacote isolado: 16/16 aprovados após definir `PYTHONPATH`; `TEST_RC=0`; duração reportada de 0,342 s.
- Verificação do ledger de exemplo: `valid: true`, `event_count: 1`, `VERIFY_RC=0`; head hash `7ea3a0af07b091e1548823117dbde5351c2ebe95d14b955f85475afdb6b5851b`.
- A primeira tentativa de descoberta dos testes falhou com `ModuleNotFoundError: No module named 'evidence_ledger'`; conservar a falha no histórico, seguida da execução corrigida.
- Fonte/limite: transcript fornecido pelo operador, não recolhido de forma independente no aparelho. Versão Python e timestamps exatos dessa execução não foram apresentados.
- Escopo negativo: não demonstra setup persistente, integração SQLite/WAL, acesso ao banco TUU, endpoint MCP ativo ou execução CERBERUS/KRONOS.

## Limites

O SHA-256 demonstra identidade de bytes em relação ao digest informado; por si só não comprova autoria, veracidade nem origem. Os 16 testes registrados no sandbox são resultados dessa execução Linux; os 16 testes citados na seção Termux vêm de transcript reportado pelo operador. Nenhum dos registros comprova a integração com SQLite/WAL, que exige fase própria, cópia isolada, política de backup, migração, orçamento de escritas e validação na versão Python instalada no Termux.

## Próximo passo

Atualização documental H1 registrada nesta branch para revisão. O próximo passo operacional é executar inventário read-only de branches/HEAD locais no Termux. Qualquer integração SQLite/WAL deve começar numa cópia isolada, com plano de backup/recuperação e aprovação humana explícita.
