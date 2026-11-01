# Aurora Relay Agent v0.1.0

Agente de retransmissão **one-shot**, controlado pelo usuário, para ligar pedidos publicados nesta branch a operações MCP locais, estritamente allowlisted.

## O que ele faz

1. O operador do ChatGPT publica um JSON em `inbox/` nesta branch.
2. O usuário executa o agente no Termux.
3. O agente valida a mensagem e, quando solicitado, conecta ao servidor MCP local por STDIO usando o SDK oficial.
4. O agente escreve uma resposta sanitizada em `outbox/`.
5. Somente com a flag explícita `--approve-publish`, ele faz commit e push da resposta.
6. O operador do ChatGPT pode então ler o resultado pelo conector GitHub autorizado.

## Limites deliberados

- Não acessa nem expõe o sandbox privado que executa uma sessão ChatGPT.
- Não concede acesso às CPUs ou ao runtime interno da OpenAI.
- Não executa shell, scripts, URLs, comandos ou ferramentas arbitrárias recebidas pela fila.
- A allowlist inicial contém somente `PING` e `MCP_DISCOVERY`.
- `MCP_DISCOVERY` chama apenas `initialize` e `tools/list`; não lê evidências, arquivos ou repositórios.
- Não há daemon, persistência automática, auto-replicação ou execução em background.
- O conteúdo de `inbox/` e `outbox/` fica público neste repositório. Nunca publique tokens, segredos, dados privados ou conteúdo de evidências.
- SHA-256 detecta alterações acidentais, mas **não é assinatura/autenticação**. A branch pública não deve ser usada como fila para comandos sensíveis.
- O usuário mantém o controle do momento de execução e da publicação.

## Requisitos

- Termux com Node.js 22+ e Git.
- Acesso de leitura ao repositório e credenciais Git já configuradas no Android para fazer push.
- Servidor Aurora MCP local já funcional por STDIO.
- Dependência `@modelcontextprotocol/sdk@1.30.0` instalada nesta pasta.

## Instalação no Termux

Use um clone dedicado para não misturar o relay com outros trabalhos:

```bash
git clone --single-branch --branch agent/aurora-relay \
  https://github.com/auroraseven77/auroraseven77.git \
  "$HOME/aurora-relay"

cd "$HOME/aurora-relay/agents/aurora-relay"
npm install --no-audit --no-fund
```

Configure o comando do servidor local como JSON array. Exemplo baseado no caminho do servidor Aurora v1.0.1:

```bash
export AURORA_MCP_COMMAND='["node","/data/data/com.termux/files/home/aurora-labs/v101/aurora_gpt_sandbox/mcp-readonly-safe-v1.0.1.cjs"]'
```

Ajuste o caminho somente se o arquivo estiver em outro local. Não inclua tokens ou credenciais nessa variável.

## Executar uma rodada

Primeiro, veja o que seria processado sem publicar:

```bash
node relay.mjs --repo "$HOME/aurora-relay"
```

Para autorizar a publicação da resposta no GitHub:

```bash
node relay.mjs --repo "$HOME/aurora-relay" --approve-publish
```

A flag aprova apenas o commit/push dos arquivos de resposta gerados pelo agente. Ela não habilita comandos arbitrários nem operações de escrita no MCP.

## Formato de mensagem

Veja `message.schema.json`. A mensagem inicial de teste fica em `inbox/0001-mcp-discovery.json`.

## Estados observáveis

- `NO_PENDING_REQUESTS`: não há mensagens novas.
- `LOCAL_RESULTS_READY`: resultado criado localmente, ainda não publicado.
- `PUBLISHED`: commit e push foram concluídos.
- `REJECTED_UNSUPPORTED_ACTION`: ação fora da allowlist.

Nenhuma execução é declarada concluída sem saída observada do agente.
