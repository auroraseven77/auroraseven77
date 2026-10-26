# Contributing

Contributions must preserve the conservative, explicitly authorized and passive-by-default scope.

## Before opening a pull request

1. Open or identify an issue for changes larger than a typo.
2. Keep changes focused; do not include target-specific data, raw evidence, credentials, cookies, access tokens, local environment files, or machine-specific paths.
3. Add tests for behavior changes, especially authorization denial, normalization, malformed input and evidence integrity.
4. Run `python -m compileall -q src tests` and `pytest -q` from `osint-toolkit/` in a disposable environment.
5. Document dependencies, network behavior and filesystem side effects.
6. Keep scientific and security claims no stronger than the available evidence.

## Review requirements

- Changes to target scope, network behavior or evidence persistence require explicit security review.
- Green CI does not authorize collection against a third-party target.
- Do not merge generated or bot-produced changes without human review.
