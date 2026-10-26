# RCS Nighthawk: recuperar job IDs e investigar discrepância histórica de parâmetros

## Objetivo
Localizar os job IDs, logs de execução e artefatos de auditoria necessários para reproduzir a discrepância reportada na regeneração de circuitos e determinar sua origem.

## Estado TUU
- **Implementado:** artefatos e rotinas de regeneração foram descritos em relatórios anteriores.
- **Verificado (reportado):** 12.031 operações QPY/QASM correspondentes; 232 de 233 circuitos regenerados.
- **Em investigação:** uma divergência reportada em 1.576 parâmetros, com diferença máxima aproximada de 3,55×10⁻¹⁵; job IDs e logs de origem.
- **Não demonstrado:** causa da discrepância, reprodução independente completa ou vantagem quântica.

## Tarefas
- [ ] Localizar IDs de jobs, timestamps, versões de ferramentas, seeds e ambiente original.
- [ ] Recuperar os arquivos de entrada/saída exatos e preservar seus hashes.
- [ ] Reexecutar apenas após confirmar disponibilidade e integridade dos artefatos necessários.
- [ ] Comparar os 1.576 parâmetros por índice, tipo numérico, tolerância, serialização e ordem de geração.
- [ ] Distinguir divergência de ponto flutuante, diferença de serialização, não determinismo e diferença semântica do circuito.

## Critérios de aceite
- [ ] Cadeia de proveniência completa para os artefatos comparados.
- [ ] Relatório reproduzível com lista de parâmetros divergentes, tolerância explícita e hashes de entradas/saídas.
- [ ] Causa classificada como confirmada, provável ou indeterminada, com evidências.
- [ ] Nenhuma conclusão de vantagem quântica inferida da contagem de operações ou de uma divergência numérica.
