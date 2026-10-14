# B1-GEN-01A: integrar runner, oráculo e avaliador independente

## Objetivo
Concluir a integração de B1-GEN-01A sem importar nem alterar `b1_motor/`, mantendo separação entre síntese por consultas, oráculo e avaliação independente.

## Estado TUU
- **Implementado:** família candidata finita e `engine_v2.py`; 11/11 testes unitários foram reportados como aprovados localmente em Termux.
- **Em investigação:** runner integrado e avaliador independente; pré-registro final do benchmark.
- **Não demonstrado:** benchmark comparativo, vantagem de consultas, generalização fora da família, síntese universal ou zero-shot.

## Tarefas
- [ ] Ligar `synthesize(query_fn, hypotheses, ...)` ao `TruthTableOracle.query`; não passar a tabela do alvo ao sintetizador.
- [ ] Implementar avaliação independente da equivalência exata sobre as 16 entradas.
- [ ] Rejeitar respostas inválidas, consultas repetidas e parâmetros de orçamento/semente inválidos.
- [ ] Registrar semente, orçamento, trace, hipóteses remanescentes, métricas por prefixo, ambiente, commit e hashes.
- [ ] Preservar o runner legado como artefato histórico, mas não executá-lo nem usá-lo como evidência: ele recebe o alvo diretamente via `run_trial`.
- [ ] Congelar protocolo, métricas, sementes e critérios de aceite antes do primeiro benchmark.
- [ ] Adicionar CI limitado a `python -m unittest discover -s experiments/B1-GEN-01A/tests`, sem instalar/importar `b1_motor`.

## Critérios de aceite
- [ ] Testes de integração demonstram uso real do oráculo e avaliação separada.
- [ ] Um caso conhecido identifica corretamente a tabela-alvo; um caso ambíguo abstém-se.
- [ ] Cada consulta é registrada, única e dentro do orçamento.
- [ ] Resultado é reproduzível com a mesma semente e conjunto congelado.
- [ ] Nenhuma alteração em `b1_motor/`; nenhum benchmark é executado antes do congelamento.
- [ ] Relatório distingue identificação dentro da família de equivalência no domínio e não alega generalização universal.

## Limites
O conjunto candidato público não é um alvo cego criptograficamente; a separação por módulos é arquitetural, não uma barreira de segurança contra acesso aos arquivos do experimento.
