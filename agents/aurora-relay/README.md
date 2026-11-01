# Aurora Relay Agent v0.4.0

Agente de retransmissão **one-shot**, controlado pelo usuário, para ligar pedidos publicados nesta branch a operações MCP locais, estritamente allowlisted.

## Fluxo

1. O operador do ChatGPT publica um JSON em **inbox/** nesta branch.
2. O usuário executa o agente no Termux.
3. O agente valida o envelope e conecta ao MCP local por STDIO com o SDK oficial.
4. O agente escreve em **outbox/** somente o resultado normalizado permitido pela ação.
5. Somente com **--approve-publish**, ele faz commit e push da resposta.
6. O operador pode recuperar a resposta pelo conector GitHub autorizado.

## Ações permitidas

- **PING**: teste do transporte GitHub-mailbox; não chama MCP.
- **CAPABILITIES**: publica catálogo gerado pelo próprio código. `implemented: true` identifica somente ações efetivamente habilitadas. Ações de escrita e execução aparecem em `deferred_actions` com `implemented: false`; não são aceitas pelo dispatcher.
- **MCP_DISCOVERY**: executa somente **initialize** e **tools/list**.
- **MCP_LIST_PROJECTS**: verifica se **aurora.list_projects** está anunciada com schema estrito de objeto vazio, chama essa ferramenta fixa com **arguments: {}** e valida os seis registros autorizados. A saída contém apenas **name** e **exists**; caminhos locais e conteúdo de arquivos não são publicados.
- **MCP_READ_EVIDENCE_METADATA**: chama exclusivamente **aurora.read_evidence** para **auroraseven77/README.md**, valida projeto, caminho, tamanho e SHA-256 calculado sobre os bytes UTF-8, e descarta o conteúdo. O outbox publica somente projeto, caminho, tamanho, hash e **content_returned: false**. Limite máximo de 48 KiB.

O relay **não aceita nomes de ferramentas nem argumentos MCP da mensagem**. Nenhuma outra ferramenta MCP é chamada nesta versão.

## Limites e privacidade

- Não acessa nem expõe o sandbox privado que executa uma sessão ChatGPT.
- Não concede acesso às CPUs ou ao runtime interno da OpenAI.
- Não executa shell, scripts, URLs, comandos ou ferramentas arbitrárias recebidas pela fila.
- **MCP_READ_EVIDENCE_METADATA** lê o README.md do projeto principal para calcular metadados, mas nunca publica seu conteúdo. A chamada ainda acessa o conteúdo local em memória no Termux.
- Não há daemon, persistência automática, auto-replicação ou execução em background.
- Este repositório é público: inbox e outbox também são públicos. **MCP_LIST_PROJECTS** publica os nomes allowlisted e o indicador de existência de cada projeto. Não use esta fila para dados privados, tokens, segredos ou conteúdo de evidências.
- SHA-256 detecta alterações acidentais, mas **não é assinatura/autenticação**.
- O usuário controla o momento da execução e autoriza separadamente a publicação com **--approve-publish**.

## Requisitos

- Termux com Node.js 22+ e Git.
- Acesso de leitura ao repositório e credenciais Git já configuradas no Android para fazer push.
- Servidor Aurora MCP local funcional por STDIO.
- Dependência **@modelcontextprotocol/sdk@1.30.0** instalada nesta pasta.

## Configuração

    export AURORA_MCP_COMMAND='["node","/data/data/com.termux/files/home/aurora-labs/v101/aurora_gpt_sandbox/mcp-readonly-safe-v1.0.1.cjs"]'

Ajuste o caminho apenas se necessário. Não inclua tokens ou credenciais nessa variável.

## Executar uma rodada

Primeiro, gere o resultado local sem publicar:

    node relay.mjs --repo "$HOME/aurora-relay"

Inspecione o JSON criado em **outbox/**. A publicação exige uma segunda execução com aprovação explícita:

    node relay.mjs --repo "$HOME/aurora-relay" --approve-publish

A flag autoriza somente o commit/push dos resultados presentes em outbox/; não amplia a allowlist nem habilita operações de escrita no MCP.

## Formato e estados

Veja **message.schema.json** e os exemplos em **inbox/**. A ação `CAPABILITIES` não habilita por si só as ações adiadas; a política atual continua `READ_ONLY`. A ação de leitura é fixa; a fila não fornece caminho ou nome de ferramenta.

- **NO_PENDING_REQUESTS**: nenhuma mensagem nova foi processada.
- **LOCAL_RESULTS_READY**: resultado local criado; ainda não publicado.
- **PUBLISHED**: commit e push concluídos.
- **REJECTED_UNSUPPORTED_ACTION**: ação fora da allowlist.

Nenhuma execução é declarada concluída sem saída observada do agente.