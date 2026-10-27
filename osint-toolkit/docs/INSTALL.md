# Installation and safe first run

## Requirements

- CPython 3.10 or later.
- An explicit allow-list scope for every collection invocation.
- Use a disposable virtual environment; do not install into shared system Python.

## Install from a checkout

```bash
python -m venv .venv
. .venv/bin/activate  # Termux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest pytest-asyncio
pytest -q
```

The separate test-tool installation matches the current package metadata. A separate packaging proposal adds an optional `test` extra, but this guide does not depend on that proposal having merged.

## Offline smoke test

```bash
osint-toolkit --help
osint-toolkit report --observations examples/observations.jsonl --out report.json
```

The `report` command reads existing JSONL and does not collect network data. Review each target and its authorization before invoking `run`.

## Authorized passive collection

```bash
osint-toolkit run example.com --allow example.com --out run/observations.jsonl --evidence run/evidence
osint-toolkit report --observations run/observations.jsonl --out run/report.json
```

Only use systems you own or for which the written scope explicitly permits collection. A public host is not authorization. The MVP does not bypass authentication, crawl, exploit, brute force, enumerate subdomains, or scan ports.

## Outputs and handling

- `observations.jsonl`: normalized observation records.
- `evidence/`: content-addressed artifacts.
- `report.json`: derived risk/confidence grouping; the heuristic is a triage signal, not a security conclusion.

Do not commit real target data, credentials, cookies, raw private evidence, or unredacted reports. SHA-256 supports integrity checks but does not establish source authenticity.
