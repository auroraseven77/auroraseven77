# Matriz de observação e acesso

| Agente | Origem/caminho | Interface | Escrita |
|---|---|---|---|
| A01 ARGOS_HEALTH | 127.0.0.1:1384 | HTTP GET /healthcheck | JSONL próprio |
| A02 SPEC_API | --source | leitura de arquivo e regex | JSONL próprio |
| A03 AUTH_REVIEW | --source | leitura de arquivo e regex | JSONL próprio |
| A04 SOCKET | /proc/net/tcp e tcp6 | procfs | JSONL próprio |
| A05 PROCESS | /proc/[pid]/cmdline, comm, status, stat | procfs; cmdline apenas filtrado em memória, nunca registrado | JSONL próprio |
| A06 LIFECYCLE | --source | leitura estática de arquivo | JSONL próprio |
| A07 RESOURCE | /proc/self/limits, meminfo, stat | procfs | JSONL próprio |
| A08 INTEGRITY | --source, cada --watch-file e cada --repo | SHA-256 de arquivos; leitura pontual de .git/HEAD, refs ou packed-refs | JSONL próprio |
| A09 NETWORK | /proc/net/dev e route | procfs | JSONL próprio |
| A10 HERMES | resultados A01-A09 | consolidação local | JSONL próprio |

## Separação de caminhos
- Cada agente escreve em uma pasta exclusiva sob observations/.
- --source aponta para um arquivo de código.
- --watch-file pode ser repetido para arquivos independentes.
- --repo pode ser repetido para repositórios locais independentes.
- Para cada repositório, o agente lê somente metadados de HEAD/ref; não percorre o working tree nem executa Git.
- A coleta de sockets, processos, recursos e rede usa interfaces procfs distintas.

## Limite de rede deliberado
Somente A01 faz uma requisição HTTP, e apenas GET para loopback em /healthcheck. Os demais agentes observam arquivos locais e tabelas procfs. Nenhuma rota operacional do Terminal Server é chamada. Isso preserva uma interface de rede mínima enquanto persistirem dúvidas sobre autenticação e lifecycle.

Os agentes compartilham o mesmo processo, usuário e namespace. Caminhos distintos não equivalem a isolamento de segurança.
