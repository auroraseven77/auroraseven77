# Política do piloto Aurora-10

Versão 0.1.0 | Duração máxima 24h | Intervalo padrão 300s | 10 agentes lógicos

## Autorizações técnicas
1. Ler o arquivo-fonte local indicado por --source, limitado a 2 MB.
2. Ler arquivos locais explicitamente indicados por --watch-file, limitados a 2 MB cada.
3. Ler somente metadados HEAD/ref de repositórios explicitamente indicados por --repo.
4. Ler arquivos de informação do kernel em /proc listados no código.
5. Consultar exclusivamente GET 127.0.0.1:1384/healthcheck, com timeout de 2 segundos.
6. Gravar JSONL na pasta de saída local.
7. Encerrar ao atingir 24h, receber Ctrl-C ou detectar STOP.

## Proibições
- Percorrer árvores inteiras de repositórios ou executar comandos Git.
- Qualquer método HTTP diferente de GET.
- Qualquer rota do Terminal Server diferente de /healthcheck.
- Endereços remotos, túneis, interfaces públicas ou testes de exposição.
- Autenticação, enumeração de credenciais ou leitura de tokens/variáveis de ambiente.
- Criação, leitura operacional, escrita ou encerramento de PTY.
- Shell, subprocessos, comandos arbitrários ou sinais a processos.
- Alteração de código, configuração, permissões, serviços ou processos monitorados.
- Instalação automática, agendamento persistente ou publicação dos resultados.

## Gate antes do piloto de 24h
1. Confirmar hostname, boot ID, namespaces PID/NET e identidade do container.
2. Confirmar autorização administrativa sobre o container.
3. Confirmar caminho e hash do arquivo-fonte.
4. Executar primeiro --once e revisar todos os arquivos.
5. Conferir que não houve conexões além do loopback nem leituras fora dos caminhos permitidos.
6. Só então iniciar 24 horas.

## Interpretação
- observed: o coletor conseguiu obter o dado definido; não significa que o serviço esteja seguro.
- unavailable: fonte indisponível.
- error: exceção no coletor.
- SHA-256: integridade do payload serializado; não é assinatura digital nem atestado de host.
- Inspeção estática não prova comportamento efetivo.
- /proc é limitado por namespace e permissões.

O código não implementa monitoramento de consumo detalhado nem isolamento de sistema operacional; supervisão do operador continua necessária.
