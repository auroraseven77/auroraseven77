# Índice de evidências — Aurora × TUU

**Data de referência:** 2026-10-14  
**Branch de auditoria:** `docs/audits-2026-10-14`

Este índice separa evidência publicada, referência a código/commit e relato ainda pendente de artefatos originais. Um link para código não equivale a prova de uma alegação científica.

| ID | Frente/afirmação limitada | Referência rastreável | Tipo de evidência | Estado de verificação nesta auditoria |
|---|---|---|---|---|
| E-001 | O harness B1.3 foi introduzido em um commit identificável | [Commit `00c371d3f3ebbcdc0d02f8fb89b5bb9110278825`](https://github.com/auroraseven77/auroraseven77/commit/00c371d3f3ebbcdc0d02f8fb89b5bb9110278825) | Código/diff versionado | Commit recuperado pelo conector GitHub; testes não executados novamente nesta auditoria |
| E-002 | O contrato e os limites B1 estão descritos | [TUU_B1_PROJECT_DOCUMENTATION.md](../TUU_B1_PROJECT_DOCUMENTATION.md) | Documentação de projeto | Documento presente; hashes e execução precisam ser verificados contra os artefatos da execução |
| E-003 | A proteção de branch e o histórico operacional foram descritos | [Finding Phase 13.1](../../aurora_phase1/evidence/phase_13_1_finding.md) | Relatório documental com saída de comandos transcrita | Relato registrado; estado atual das configurações GitHub não foi consultado neste passo |
| E-004 | O estado de auditoria distingue resultados reportados de conclusões não demonstradas | [STATUS.md](../../STATUS.md) | Snapshot de auditoria | Publicado na branch documental |
| E-005 | B1-GEN-01A tem família candidata e testes locais reportados | [Rascunho B1-GEN-01A](issue-drafts/B1-GEN-01A.md) | Relato/documento de continuidade | **Não reproduzido aqui.** Busca na branch não localizou `experiments/B1-GEN-01A/target-manifest.json` nem `TARGET-MANIFEST-SHA256SUMS` |
| E-006 | O protocolo B1-GEN-01A ainda não sustenta benchmark comparativo | [STATUS.md](../../STATUS.md) e [rascunho B1-GEN-01A](issue-drafts/B1-GEN-01A.md) | Limitação metodológica explicitada | Mantido como não demonstrado até integração runner–oráculo–avaliador e congelamento do protocolo |
| E-007 | AC4-R2 teve integridade estrutural do ledger reportada | [Rascunho AC4-R2](issue-drafts/AC4-R2.md) | Relato de integridade | Logs/arquivos v0–v08 não vinculados nesta branch; recuperação histórica não demonstrada |
| E-008 | P14–P19 não foram confirmados neste registro | [Rascunho B11](issue-drafts/B11.md) | Inventário negativo limitado | Artefatos e proveniência continuam pendentes |
| E-009 | Divergências de RCS Nighthawk foram reportadas | [Rascunho RCS Nighthawk](issue-drafts/RCS-Nighthawk.md) | Relato de auditoria | Job IDs, logs e artefatos de origem não estão vinculados neste índice |

## Regra para adicionar evidências

Cada nova entrada deve registrar:

- identificador estável;
- afirmação estrita que o artefato realmente sustenta;
- URL do arquivo, commit, workflow ou log;
- SHA-256 para artefatos binários/JSON exportados quando aplicável;
- ambiente, comando, data e código de saída para execuções;
- classificação: **publicado**, **reportado**, **reproduzido** ou **não demonstrado**.

### Lacunas atuais

- Os manifestos, JSONs e logs originais do B1-GEN-01A ainda não estão publicados nos caminhos esperados nesta branch.
- Nenhuma execução limpa do B1-GEN-01A foi possível com os artefatos atualmente visíveis.
- Os resultados reportados para B1.3 e outras frentes não foram reexecutados durante esta atualização documental.
- Nenhuma afirmação de vantagem quântica, generalização universal ou prova matemática global é validada por este índice.
