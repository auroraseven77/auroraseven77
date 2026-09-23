# Finding — Phase 7: STERILE_ENV PATH no Termux

## Status
CONFIRMED (achado novo, Bloco 7)

## Origem
Reconstrução do Bloco 7.

## Comportamento descoberto
`STERILE_ENV` com `PATH=/usr/bin:/bin` funciona em Linux padrão mas
falha silenciosamente no Termux. O `python3` real vive em
`/data/data/com.termux/files/usr/bin/python3`, não em `/usr/bin`.

Com o PATH errado, o `subprocess.run` encontra um binário em `/usr/bin`
que retorna `exit_code=0` sem output. Falha silenciosa.

## Fix aplicado
`STERILE_ENV["PATH"]` é derivado de `sys.executable`:

    _DEFAULT_PATH = ":".join(filter(None, [
        os.path.dirname(sys.executable),
        "/usr/bin",
        "/bin",
    ]))

Portável entre ambientes. Se rodar em Python X, o path do Python X
está no PATH do subprocesso.

O contrato pode sobrescrever via chave `sterile_env`:

    self._sterile_env = {**STERILE_ENV, **contract.get("sterile_env", {})}

## Implicação contratual
Portabilidade do executor. O PATH do env esterilizado não pode ser
hardcoded porque ambientes variam (Termux, Android, containers).

## Artefatos
- `core/executor.py` — `STERILE_ENV`, `_DEFAULT_PATH`
- `tests/test_executor.py::test_output_truncated`

## Verificação
`python3 -m unittest aurora_phase1/tests/test_executor.py::TestExecutor::test_output_truncated`
(antes do fix, este teste passava com `truncated=False` e `stdout=''`
— falha silenciosa)
