# Aurora Evidence Ledger 01 — estado do artefato TELOS

**Data de referência:** 2026-10-26  
**Estado:** pacote construído e testado no sandbox; integração TUU/SQLite/WAL e Termux ainda não executadas.

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

## Limites

O SHA-256 demonstra identidade de bytes em relação ao digest informado; por si só não comprova autoria, veracidade nem origem. Os 16 testes são observados neste sandbox, não no Android do usuário. A integração com SQLite/WAL exige uma fase própria, em cópia isolada, com política de backup, migração, orçamento de escritas e validação na versão Python do Termux.

## Próximo passo

Revisão humana do pacote e do PR draft. Depois, handoff para validação no Termux; não executar a integração diretamente nesta sessão.
