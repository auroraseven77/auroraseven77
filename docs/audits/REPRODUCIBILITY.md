# Reprodução experimental — comando, ambiente e limites

## Experimento-piloto escolhido

**B1-GEN-01A**, porque o trabalho de continuidade já define a separação necessária entre sintetizador, oráculo e avaliador independente, além de critérios de aceitação e testes unitários.

## Estado atual: BLOQUEADO nesta branch

A busca de arquivos no repositório e na branch `docs/audits-2026-10-14` não encontrou:

- `experiments/B1-GEN-01A/target-manifest.json`;
- `experiments/B1-GEN-01A/TARGET-MANIFEST-SHA256SUMS`;
- `experiments/B1-GEN-01A/tests/`.

Por isso, não é correto alegar que o experimento foi reproduzido em ambiente limpo. O próximo passo é importar os artefatos originais, sem modificar seus bytes, confirmar os hashes e registrar o commit de origem.

## Comando de teste previsto

Depois que o pacote e os testes forem publicados, a verificação unitária deve usar a biblioteca padrão Python e o diretório de testes isolado:

```bash
python -m unittest discover -s experiments/B1-GEN-01A/tests -v
```

Esse comando testa a suíte; **não é, por si só, um benchmark**. O benchmark só pode ser executado após integração do runner com o oráculo e avaliador independente e congelamento prévio de sementes, orçamento, métricas e critérios de aceite.

## Execução controlada com um único comando

O wrapper `scripts/reproduce-b1-gen-01a.sh` faz a verificação de pré-condições e, se os testes estiverem presentes, executa a suíte acima. Se os artefatos estiverem ausentes, deve terminar explicitamente como BLOQUEADO, sem substituir arquivos nem invocar o runner legado.

```bash
bash scripts/reproduce-b1-gen-01a.sh
```

Na revisão atual, espera-se que o wrapper indique BLOQUEADO até que os artefatos sejam publicados. Esse resultado negativo é uma verificação de pré-condição, não uma reprodução experimental bem-sucedida.

## Ambiente limpo

A CI documental deve executar em checkout limpo com Python 3.12 e sem instalar ou importar `b1_motor`. A suíte B1-GEN-01A deve rodar somente quando os arquivos de teste estiverem presentes. A ausência da suíte deve ficar visível como pré-requisito pendente, não ser descrita como teste aprovado.

## Critérios para declarar REPRODUZIDO

- Manifesto e hashes presentes e validados.
- Commit e origem dos artefatos registrados.
- Dependências documentadas e ambiente identificado.
- Testes de integração demonstram uso real do oráculo e avaliação independente.
- Entradas, sementes, orçamento, trace e resultados registrados.
- Uma execução independente satisfaz os critérios definidos antes da execução.
- Relatório preserva diferenças entre identificação dentro da família, equivalência no domínio e generalização.

Não executar nem usar o runner legado como evidência de benchmark. Não alterar `b1_motor/`.
