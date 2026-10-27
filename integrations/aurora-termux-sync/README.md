# Aurora Termux Mirror Sync

Sincronização automática, somente GitHub → Termux, usando um clone isolado do repositório `auroraseven77/auroraseven77`.

## Comportamento
- Atualiza `main` em `~/auroraseven77-sync-mirror` (padrão).
- Usa `git fetch` + `git merge --ff-only`; nunca usa reset, clean, force push ou troca branch.
- Recusa espelho sujo, divergente, com origem inesperada ou caminho inseguro.
- Não executa scripts/testes/hooks do código recém-baixado e não envia dados locais ao GitHub.
- Não toca no checkout de desenvolvimento `~/auroraseven77-test`.
- Agendado por Termux:API JobScheduler a cada ~6h. Android pode atrasar jobs por bateria/políticas do SO.
- Após instalação inicial única, sincronizações futuras não pedem aprovação por commit.

## Instalação inicial única (cole o bloco completo no Termux)

```bash
set -eu
D="$HOME/aurora-termux-sync-bootstrap"
mkdir -p "$D"
cd "$D"
BASE="https://raw.githubusercontent.com/auroraseven77/auroraseven77/main/integrations/aurora-termux-sync"
curl -fsSLo aurora_mirror_sync.sh "$BASE/aurora_mirror_sync.sh"
curl -fsSLo install_termux_mirror_job.sh "$BASE/install_termux_mirror_job.sh"
printf '%s\n' \
  '046458b094b899b666a2d67311892864bc609cc2c79b3f3efa3eed83545c00df  aurora_mirror_sync.sh' \
  '31a460f87ade92ea6611510c4a52b4c20660a42230d768a77faada5e748e82f8  install_termux_mirror_job.sh' > SHA256SUMS
sha256sum -c SHA256SUMS
bash install_termux_mirror_job.sh
```

O instalador exige `git` e `termux-job-scheduler`; ele não instala pacotes nem instala o app Termux:API. Se o agendador faltar, instale `termux-api` e o aplicativo companheiro compatível e rode o mesmo bloco de bootstrap outra vez.

## Diagnóstico
```bash
termux-job-scheduler --pending
cat "$HOME/.local/state/aurora-sync-mirror/runner.log"
"$HOME/.local/bin/aurora-mirror-sync"
```

## Limites
Este fluxo mantém um espelho remoto atualizado. Não envia automaticamente modificações locais não commitadas para GitHub, não configura MCP e não executa comandos remotos. Isso é intencional: o espelho serve como fonte de leitura/auditoria sem sobrescrever o checkout de desenvolvimento nem conceder autoridade de execução a código baixado.
