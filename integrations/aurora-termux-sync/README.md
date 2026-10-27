# Aurora Termux Mirror Sync v1.0.0

Este pacote estabelece um espelho **GitHub → Termux** independente do checkout de desenvolvimento.

- Atualiza somente `main` por fast-forward.
- Roda como tarefa do Termux:API a cada aproximadamente 6 horas.
- Não executa código baixado, não envia arquivos locais e não toca em `~/auroraseven77-test`.
- Recusa espelho sujo, divergente ou com origem/branch inesperadas.
- O arquivo ZIP foi validado em ambiente Linux com repositório Git sintético; o agendamento no Android ainda precisa da instalação inicial no aparelho.

## Arquivo

- `aurora-termux-mirror-sync-v1.0.0.zip`
- SHA-256: `678b988b7571358933de64bbac19e7e7b8f2d5d0eb32e0c587b3c890e3649403`

## Bootstrap único no Termux

Depois de esta alteração chegar a `main`, execute uma única vez:

```bash
set -eu
mkdir -p "$HOME/aurora-termux-sync-bootstrap"
cd "$HOME/aurora-termux-sync-bootstrap"
curl -fL -o aurora-termux-mirror-sync-v1.0.0.zip "https://github.com/auroraseven77/auroraseven77/raw/main/integrations/aurora-termux-sync/aurora-termux-mirror-sync-v1.0.0.zip"
curl -fL -o aurora-termux-mirror-sync-v1.0.0.zip.sha256 "https://github.com/auroraseven77/auroraseven77/raw/main/integrations/aurora-termux-sync/aurora-termux-mirror-sync-v1.0.0.zip.sha256"
sha256sum -c aurora-termux-mirror-sync-v1.0.0.zip.sha256
unzip -q aurora-termux-mirror-sync-v1.0.0.zip
cd package/aurora-termux-mirror-sync
bash install_termux_mirror_job.sh
```

O instalador não instala pacotes. Ele exige `git` e `termux-job-scheduler`; se a API do Termux não estiver disponível, o instalador para sem configurar o job.
