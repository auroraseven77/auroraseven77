# AC4-R2: localizar artefatos do episódio histórico e verificar proveniência

## Objetivo
Localizar, se ainda existirem, cópias locais/privadas dos artefatos históricos v0–v08 associados ao episódio AC4-R2 e determinar se permitem reconstrução e reprodução histórica.

## Estado TUU
- **Implementado:** ledger append-only com cadeia de hashes, conforme os artefatos atuais.
- **Verificado (reportado):** integridade de 16 blocos do ledger.
- **Em investigação:** localização e cadeia de proveniência dos artefatos do episódio original.
- **Não demonstrado:** recuperação/reprodução histórica do episódio. Integridade interna do ledger, isoladamente, não prova a existência nem a autenticidade dos artefatos ausentes.

## Tarefas
- [ ] Pesquisar repositórios locais, branches, arquivos privados e backups autorizados por nomes v0–v08 e identificadores AC4-R2.
- [ ] Registrar cada local consultado, data, resultado e limites da busca.
- [ ] Para cada artefato encontrado, preservar bytes originais e calcular SHA-256.
- [ ] Comparar timestamps, referências cruzadas, commits e cadeia de custódia sem reescrever os originais.
- [ ] Separar explicitamente reprodução histórica, reprodução documental e teste sintético.

## Critérios de aceite
- [ ] Inventário reproduzível de fontes consultadas.
- [ ] Artefatos encontrados preservados com hashes e proveniência; ou relatório negativo limitado às fontes efetivamente consultadas.
- [ ] Conclusão classificada como recuperado, parcialmente recuperado ou não localizado.
- [ ] Nenhuma alegação de recuperação histórica baseada somente na integridade do ledger.
