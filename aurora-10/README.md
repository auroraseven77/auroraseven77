# Aurora-10 — piloto de observabilidade somente leitura

Estado: implementação versionada; não implantada nem executada no container-alvo.

## Objetivo
Dez agentes lógicos com caminhos de observação separados, supervisionados por um único processo Python. O piloto padrão dura 24 horas, coleta a cada 5 minutos e usa somente a biblioteca padrão do Python.

Os agentes são módulos lógicos, não dez processos concorrentes. O supervisor os executa sequencialmente para reduzir carga e manter evidências separadas.

## Limites de segurança
- Somente leitura das fontes locais explicitamente permitidas.
- Única chamada HTTP: GET http://127.0.0.1:1384/healthcheck, com timeout curto.
- Não chama /open, /read, /write, /kill, /docs nem /openapi.json.
- Não abre PTYs, não cria subprocessos, não executa shell e não lê variáveis de ambiente de processos.
- Não tenta autenticar, contornar autenticação, descobrir tokens ou testar exposição externa.
- Falhas de permissão e fontes ausentes são registradas como limitações.
- Não altera configurações do Terminal Server.
- Não publica dados coletados no GitHub.

As observações anteriores apontam dúvidas sobre autenticação e encerramento/reaping de subprocessos. Por isso o piloto não cria sessões PTY nem chama endpoints operacionais.

## Agentes
| ID | Nome | Fonte principal | Observação |
|---|---|---|---|
| A01 | ARGOS_HEALTH | HTTP loopback | GET healthcheck |
| A02 | SPEC_API | código local | rotas e middleware por inspeção estática |
| A03 | AUTH_REVIEW | código local | lógica fail-closed, sem ler segredos |
| A04 | SOCKET | /proc/net/tcp* | sockets LISTEN |
| A05 | PROCESS | /proc/[pid]/cmdline, status, stat | processo servidor, quando legível |
| A06 | LIFECYCLE | código local | Popen, wait/poll/terminate/kill e /kill |
| A07 | RESOURCE | /proc/self/limits, /proc/meminfo, /proc/stat | limites e indicadores |
| A08 | INTEGRITY | código local | SHA-256 da fonte |
| A09 | NETWORK | /proc/net/dev, /proc/net/route | interfaces e rotas locais |
| A10 | HERMES | resultados do ciclo | consolidação e hash |

Cada agente grava em observations/<agent_id>/events.jsonl. O consolidado fica em observations/consolidated/events.jsonl.

## Pré-requisitos e execução
Python 3.10+; sem dependências externas.

Uma coleta:
    python3 aurora-10/supervisor.py --once

Piloto padrão:
    python3 aurora-10/supervisor.py --duration-hours 24 --interval-seconds 300

Outros arquivos e repositórios locais (opções repetíveis):
    python3 aurora-10/supervisor.py --watch-file /caminho/arquivo-a --watch-file /caminho/arquivo-b --repo /caminho/repo-a --repo /caminho/repo-b

O agente de integridade calcula SHA-256 dos arquivos indicados e lê somente metadados HEAD/ref dos repositórios; não executa Git, não faz fetch/checkout e não percorre a árvore.

Outro caminho de código-fonte:
    python3 aurora-10/supervisor.py --source /opt/terminal-server/openai/server.py

Pasta de saída explícita:
    python3 aurora-10/supervisor.py --duration-hours 24 --interval-seconds 300 --output ./aurora-10-observations

Para parar cooperativamente, crie STOP dentro da pasta de saída. Ctrl-C também interrompe.

## Evidência
Cada linha JSON contém run_id, horário UTC, agente, estado, payload e SHA-256 do payload canônico. O supervisor gera um evento consolidado por ciclo.

O hash detecta alterações no conteúdo registrado, mas não prova identidade do host, integridade do filesystem, autenticidade do relógio ou cadeia de custódia externa.

## Limitação de isolamento
Os caminhos e módulos são distintos, mas compartilham processo supervisor, usuário, kernel e permissões do container. É isolamento organizacional de coleta, não isolamento de segurança entre agentes.

Este commit não instala, inicia ou agenda nada remotamente.
