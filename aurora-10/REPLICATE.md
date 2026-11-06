# Replicar no outro runtime

## Obter a versão
    git clone --filter=blob:none --no-checkout https://github.com/auroraseven77/auroraseven77.git
    cd auroraseven77
    git fetch origin test/aurora-10-observability
    git checkout --detach FETCH_HEAD

Se já houver clone:
    git fetch origin test/aurora-10-observability
    git switch --detach FETCH_HEAD

## Registrar revisão e hashes
    git rev-parse HEAD
    git status --short
    sha256sum aurora-10/supervisor.py aurora-10/README.md aurora-10/PILOT-POLICY.md aurora-10/REPLICATE.md

## Teste inicial
    python3 --version
    python3 aurora-10/supervisor.py --help
    python3 aurora-10/supervisor.py --once --output ./aurora-10-observations

Revise os resultados da coleta única antes do piloto de 24h.

## Piloto
    python3 aurora-10/supervisor.py --duration-hours 24 --interval-seconds 300 --output ./aurora-10-observations

Parada:
    touch ./aurora-10-observations/STOP

Cada runtime deve registrar commit SHA, hashes dos arquivos, hostname, boot ID, namespaces, horários UTC e hashes dos artefatos. Não compartilhe tokens, variáveis de ambiente ou dados sensíveis no repositório.

A leitura pública desta branch permite obter o mesmo código. Isso não estabelece comunicação direta, filesystem compartilhado ou identidade de host comum.
