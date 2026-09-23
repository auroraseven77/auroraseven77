# Finding — Phase 3.1: Path Traversal

## Status
CONFIRMED

## Origem
Fase 3 (chat antigo). Reconstruído no Bloco 7.

## Vulnerabilidade descoberta
A TUU das Fases 1-2 apenas validava se a ação estava em
`allowed_actions`. Quando HEPHAESTUS propunha `PROPOSE_SANDBOX_WRITE`,
o Centro aprovava cegamente mesmo que o payload contivesse
`../../etc/passwd`.

## Fix aplicado
Validação de conteúdo em duas camadas:
- Camada 1 (agente): `_validate_content` no `EphemeralAgent` valida
  contra `denied_patterns` do contrato do papel.
- Camada 2 (Centro): `IsolatedExecutor._validate` valida cwd contra
  `allowed_paths` via `os.path.realpath` + `startswith(canonical_ap + os.sep)`.

A concatenação com `os.sep` evita o bug clássico de `startswith` puro.

## Implicação contratual
Confinamento estrito de caminhos é invariante de segurança. Nenhuma
ação pode tocar o sistema de arquivos fora de `allowed_paths`.

## Artefatos
- `core/executor.py` — `_validate`
- `contracts/hephaestus_role.json` — `allowed_paths`, `denied_patterns`
- `tests/test_executor.py::test_cwd_outside_allowed`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_executor.py::TestExecutor::test_cwd_outside_allowed`
