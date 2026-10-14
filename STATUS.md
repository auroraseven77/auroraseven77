# TUU — Estado de auditoria e evidências

**Data de referência:** 2026-10-14  
**Escopo:** rastreabilidade documental, estado reportado dos experimentos e limites das conclusões.  
**Política:** documentação e evidências apenas; nenhuma alteração em `b1_motor/` é autorizada por este registro.

## Matriz de estado

| Frente | Implementado | Verificado / evidência disponível | Em investigação | Não demonstrado |
|---|---|---|---|---|
| **B1.3 — validação de energia** | Harness de referência densa e diagonalização exata para sistemas pequenos; commit `00c371d3f3ebbcdc0d02f8fb89b5bb9110278825` | 34 testes aprovados foram reportados pelo operador; cobertura declarada até N≤8. Tratar como evidência reportada, não como execução independente deste documento. | Preservação e publicação do relatório de closeout/contrato selado; confirmação de que os artefatos estão vinculados à branch e ao commit corretos. | Escalonamento para N=64; vantagem quântica; liberação para produção; validação de topologia de interfaces N=64 por extrapolação de N≤8. |
| **B1-GEN-01A — síntese por consultas** | Família finita candidata de 70 tabelas-verdade distintas; `engine_v2.py`, oráculo e testes locais. | 11/11 testes unitários foram reportados como aprovados em Termux/Python 3.14.6. O resultado ainda é evidência local reportada. | Integração real entre runner, oráculo e avaliador independente; congelamento final do protocolo antes do benchmark. | Benchmark comparativo válido; vantagem de consultas; generalização fora da família; síntese universal ou zero-shot. O runner legado que acessa diretamente o alvo não é evidência válida. |
| **AC4-R2 — episódio histórico** | Ledger/hash-chain descrito no repositório; integridade de 16 blocos foi reportada. | Integridade estrutural do ledger, conforme relato anterior. | Localizar artefatos históricos v0–v08 e reconstruir a cadeia de proveniência do episódio. | Recuperação ou reprodução histórica do episódio AC4-R2; equivalência entre integridade do ledger e autenticidade do episódio ausente. |
| **B11 — Navier–Stokes** | Nenhum artefato P14–P19 confirmado neste registro. | Nenhuma prova matemática de regularidade global foi confirmada. | Procurar cópias privadas/localizadas de P14–P19 e verificar sua proveniência. | Fechamento das lacunas matemáticas; prova de regularidade global; validação de qualquer alegação de solução geral. |
| **RCS Nighthawk — auditoria de circuitos** | Artefatos e rotinas de regeneração foram descritos em relatórios anteriores. | Foi reportada correspondência de 12.031 operações QPY/QASM e regeneração de 232/233 circuitos. | Localizar IDs dos jobs, logs de execução e a origem da divergência histórica em 1.576 parâmetros (diferença máxima reportada de aproximadamente 3,55×10⁻¹⁵). | Causa da discrepância; reprodução independente completa; vantagem quântica universal. |

## Regras de leitura

1. **Implementado não significa demonstrado.** Existência de código, harness ou documento não comprova a alegação científica associada.
2. **Teste reportado não significa reprodução independente.** Os resultados locais acima preservam a proveniência declarada e precisam ser ligados aos logs e hashes originais.
3. **Integridade não significa recuperação histórica.** Um ledger internamente consistente não substitui os artefatos ausentes do episódio.
4. **Resultados em N≤8 não demonstram escalabilidade para N=64.**
5. **Resultados dentro de uma família finita não demonstram síntese universal, generalização fora da família nem zero-shot.**
6. Nenhum benchmark B1-GEN-01A deve ser tratado como resultado pré-registrado até que runner, oráculo, avaliador, sementes, orçamento e métricas estejam integrados e congelados antes da execução.
7. Esta branch não deve alterar `b1_motor/`, executar o runner legado como evidência, fazer merge automático em `main` ou autorizar a liberação de produção.

## Artefatos pendentes de vinculação

Os JSONs de auditoria, contratos selados, logs de testes e relatórios mencionados em conversas anteriores ainda precisam ser copiados a partir da fonte original e verificados por SHA-256 antes de serem listados como arquivos publicados nesta branch. Não se presume que um artefato esteja no GitHub apenas porque foi gerado localmente.

## Próximos passos

- Adicionar os artefatos de auditoria sem modificar seus bytes, mantendo uma lista de hashes e a origem de cada arquivo.
- Isolar o B1-GEN-01A em branch própria, após validar o pacote local e excluir caches/arquivos temporários.
- Criar uma tag anotada para B1.3 somente após confirmar o alvo exato da branch `feat/b1.3-energy-validation-harness`.
- Manter os PRs de documentação em draft até a revisão humana.
- Executar CI apenas para os testes de `experiments/B1-GEN-01A/tests`, sem instalar ou importar `b1_motor`.
