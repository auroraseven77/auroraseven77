# Aurora Relay Agent v0.4.1 — hotfix candidate

Agente one-shot, controlado pelo operador, para encaminhar pedidos públicos de uma branch Git a um servidor MCP local por STDIO. Esta versão mantém a política **READ_ONLY**. Nenhuma ação de escrita, exclusão ou execução de tarefas foi habilitada.

## Estado da versão

Esta é a implementação candidata da Fase A. A versão não deve receber tag de release nem avançar para as Fases B/C até que os testes de segurança passem também no Termux.

## Ações implementadas

- `PING`: verifica apenas a fila Git; não chama MCP.
- `CAPABILITIES`: publica o catálogo read-only.
- `MCP_DISCOVERY`: chama `initialize` e `tools/list`.
- `MCP_LIST_PROJECTS`: chama apenas `aurora.list_projects` com argumentos vazios e valida a lista allowlisted.
- `MCP_READ_EVIDENCE_METADATA`: chama apenas `aurora.read_evidence` para `auroraseven77/README.md`, valida tamanho e SHA-256 e descarta o conteúdo.

O relay não aceita o nome de ferramenta nem argumentos MCP arbitrários da inbox.

## Hotfixes da Fase A

- `safeWriteAtomic` rejeita symlinks no destino e em diretórios ancestrais, cria temporário exclusivo com `O_EXCL`/`O_NOFOLLOW`, grava com modo `0600`, sincroniza o arquivo e faz rename atômico.
- Inbox: somente arquivos regulares; rejeita symlink, UTF-8 inválido, JSON inválido, tamanho superior a 64 KiB e pedidos com mais de 24 horas (mtime ou `created_at`).
- Limite de 100 pedidos JSON por rodada.
- Publicação exige `--approve-publish req_<12 hex>` e publica somente o resultado daquele ID.
- O outbox inclui `request_sha256`, calculado sobre os bytes exatos da mensagem da inbox. Antes do push, o relay reabre e valida o pedido e confere o vínculo do hash.
- O executável MCP deve resolver para o mesmo binário Node que executa o relay; seu SHA-256 deve corresponder a `AURORA_MCP_NODE_SHA256` fornecido pelo operador.
- Timeouts: 10 s para `initialize`/connect e `tools/list`; 30 s para `tools/call`. Em timeout, o relay solicita fechamento do cliente/transporte MCP.

**Limite da proteção de filesystem:** a validação rejeita symlinks estáticos e protege contra a exploração reproduzida no hotfix. Node.js não expõe uma API portátil de `openat2`/`renameat` com descritores de diretório para eliminar toda condição de corrida contra outro processo local concorrente com o mesmo UID. Não execute a fila num diretório compartilhado com processos locais não confiáveis.

## Configuração no Termux

O servidor continua sendo configurado por JSON array, sem shell:

```sh
export AURORA_MCP_COMMAND='["node","/data/data/com.termux/files/home/aurora-labs/v101/aurora_gpt_sandbox/mcp-readonly-safe-v1.0.1.cjs"]'
```

Obtenha o hash observado do Node uma única vez:

```sh
sha256sum "$(command -v node)"
```

Compare o caminho com `node -p 'process.execPath'`. Depois de verificar e registrar o hash de confiança, defina-o literalmente para a sessão (não calcule dinamicamente a cada execução):

```sh
export AURORA_MCP_NODE_SHA256='COLE_AQUI_O_HASH_SHA256_DE_64_CARACTERES'
```

O relay falha fechado se a variável faltar, tiver formato inválido, o comando apontar para outro executável ou o hash não corresponder. Não coloque tokens ou credenciais nessas variáveis.

## Formato de IDs

Novos pedidos devem usar `req_` seguido por 12 caracteres hexadecimais minúsculos, por exemplo:

```sh
ID="req_$(openssl rand -hex 6)"
```

O formato legado de envelope continua aceito para leitura de pedidos já existentes, mas a publicação nesta versão exige o novo formato `req_<12hex>`.

## Execução e publicação

Gere resultados locais sem publicar:

```sh
node relay.mjs --repo "$HOME/aurora-relay"
```

Inspecione o resultado escolhido em `outbox/<ID>.json`. Para publicar um único resultado:

```sh
node relay.mjs --repo "$HOME/aurora-relay" --approve-publish "$ID"
```

A aprovação publica apenas o arquivo correspondente ao ID e exige que `request_sha256` corresponda aos bytes exatos da inbox. Resultados anteriores ou outros JSON presentes na outbox não são adicionados ao commit.

## Testes

```sh
npm run test:security
```

Os testes cobrem symlinks no destino e em diretórios ancestrais, gravação atômica, symlink/tamanho/idade na inbox, limite de contagem, aprovação por ID, hash do binário Node e timeouts.

## Limites e privacidade

- O repositório e a fila GitHub são públicos; nunca publique segredos, tokens, dados privados ou conteúdo de evidências.
- O relay não acessa o sandbox privado que executa uma sessão ChatGPT nem concede acesso ao runtime interno da OpenAI.
- Não há daemon, persistência automática, auto-replicação nem execução em background.
- O SHA-256 da resposta vincula os dados e detecta alteração acidental; não é assinatura criptográfica nem autenticação do autor da inbox.
- Esta versão não habilita FS_WRITE, FS_DELETE, TASK_EXECUTE, shell remoto ou aprovação de mutações.
