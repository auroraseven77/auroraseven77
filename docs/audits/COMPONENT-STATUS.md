# Inventário de componentes — Aurora × TUU

**Data de referência:** 2026-10-14  
**Branch de auditoria:** `docs/audits-2026-10-14`  
**Política:** inventário documental; nenhuma alteração em `b1_motor/`.

## Convenção de estados

- **IMPLEMENTADO (documentado):** há código ou contrato identificado no repositório.
- **TESTES EXISTEM:** arquivos de teste estão presentes; isso não significa que foram executados nesta auditoria.
- **TESTADO (reportado):** há um resultado relatado, mas a execução não foi reproduzida independentemente neste trabalho.
- **BLOQUEADO:** faltam artefatos necessários para executar a reprodução a partir desta branch.
- **NÃO DEMONSTRADO:** as evidências atuais não sustentam a conclusão mais ampla.

## Matriz

| Componente/frente | Estado sustentado | Evidência disponível | Limite / próximo passo |
|---|---|---|---|
| `b1_motor/mps.py` — representação MPS | IMPLEMENTADO (documentado); produção crítica congelada | [Documentação B1](../TUU_B1_PROJECT_DOCUMENTATION.md), seção 3; SHA-256 histórico registrado ali | Não alterar nesta auditoria. O hash citado no documento deve ser revalidado contra o arquivo exato antes de nova selagem. |
| B1.2 — Hamiltoniano TFIM e ansatz | IMPLEMENTADO (documentado) | [Documentação B1](../TUU_B1_PROJECT_DOCUMENTATION.md), seções 4–6; módulos `b1_motor/hamiltonian_b12.py`, `b1_motor/ansatz_b12.py`, `b1_motor/vqe_b12.py` | Parâmetros estruturais e convenções devem ser vinculados a manifestos e execução específica. Não inferir escalabilidade só a partir da configuração N=64. |
| B1.3 — referência densa / diagonalização exata | IMPLEMENTADO; testes reportados | [Commit de harness](https://github.com/auroraseven77/auroraseven77/commit/00c371d3f3ebbcdc0d02f8fb89b5bb9110278825); testes descritos na [documentação B1](../TUU_B1_PROJECT_DOCUMENTATION.md) | Os 34 testes aprovados são resultado reportado, não uma execução limpa realizada por este inventário. Evidência descrita para N≤8 não demonstra N=64 nem vantagem quântica. |
| B1-GEN-01A — síntese por consultas | IMPLEMENTAÇÃO/11 testes **reportados localmente**; reprodução nesta branch BLOQUEADA | [Rascunho de continuidade](issue-drafts/B1-GEN-01A.md) e [snapshot](../../STATUS.md) | `experiments/B1-GEN-01A/`, manifesto e hashes não foram encontrados nesta branch. Importar os artefatos originais e verificar hashes antes de declarar execução reproduzível. Não usar o runner legado como benchmark. |
| AC4-R2 — episódio histórico | Integridade do ledger reportada; recuperação histórica NÃO DEMONSTRADA | [Rascunho AC4-R2](issue-drafts/AC4-R2.md) | Localizar artefatos históricos v0–v08 e estabelecer proveniência. Integridade estrutural não prova autenticidade nem reprodução do episódio. |
| B11 — Navier–Stokes P14–P19 | BLOQUEADO por artefatos não confirmados; prova global NÃO DEMONSTRADA | [Rascunho B11](issue-drafts/B11.md) | Localizar versões originais, hashes e dependências matemáticas. Não reconstruir lacunas como se fossem originais. |
| RCS Nighthawk | Resultados de auditoria reportados; reprodução independente NÃO DEMONSTRADA | [Rascunho RCS Nighthawk](issue-drafts/RCS-Nighthawk.md) | Recuperar job IDs, logs, entradas/saídas e ambiente antes de reexecutar. |
| `aurora_phase1/` — laboratório multiagente | Código, documentação e testes presentes | [README do componente](../../aurora_phase1/README.md); [finding Phase 13.1](../../aurora_phase1/evidence/phase_13_1_finding.md) | Os resultados documentados no finding precisam ser verificados contra configurações/logs atuais antes de tratá-los como estado operacional atual. |
| `osint-toolkit/` | README e arquivos de teste presentes; fora do escopo TUU/B1 | [README do toolkit](../../osint-toolkit/README.md) | Não executar reconhecimento de rede como parte desta auditoria. Nenhum resultado de teste foi executado neste inventário. |

## Limites do inventário

1. Este arquivo registra evidências localizadas no repositório e relatos existentes; não transforma relatos em reprodução independente.
2. Componentes que não estão publicados nesta branch não devem ser considerados disponíveis apenas porque foram mencionados em sessões ou relatórios.
3. Os diretórios e caminhos são referenciados para navegação; sua presença deve ser revalidada no commit-alvo antes de uma execução.
4. `b1_motor/` permanece fora do escopo de alteração. A CI de B1-GEN-01A deve se limitar a `experiments/B1-GEN-01A/tests` quando os arquivos forem publicados.
