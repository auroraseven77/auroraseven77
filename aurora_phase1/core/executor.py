"""Execução isolada.

O executor recebe uma ação estruturada e a traduz para subprocess.run
com isolamento. Nunca usa shell. Nunca herda env do processo pai.
Nunca executa dentro do processo principal.

Invariantes:
- shell=False sempre
- args como lista, nunca string
- env esterilizado (PATH, USER, HOME, LC_ALL, LANG fixos)
- cwd dentro de allowed_paths
- timeout obrigatório
- stdout/stderr truncados em max_output_bytes
- command_hash determinístico
- NUNCA executa dentro do processo principal

Formato do ExecutionResult:
    exit_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool
    truncated: bool
    command_hash: Optional[str]
    duration_ms: float
    error_type: Optional[str]   # se rejeitado antes de executar
    error_message: Optional[str]
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from aurora_phase1.core.crypto import hash_object


import sys as _sys

# PATH derivado do Python atual — portável entre ambientes.
# Em produção, o contrato pode sobrescrever via chave "sterile_env".
_DEFAULT_PATH = ":".join(filter(None, [
    os.path.dirname(_sys.executable),
    "/usr/bin",
    "/bin",
]))

STERILE_ENV = {
    "PATH": _DEFAULT_PATH,
    "USER": "aurora_sandbox",
    "HOME": "/tmp/aurora_sandbox",
    "LC_ALL": "C.UTF-8",
    "LANG": "C.UTF-8",
}


@dataclass
class ExecutionResult:
    exit_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool
    truncated: bool
    command_hash: Optional[str]
    duration_ms: float
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
            "truncated": self.truncated,
            "command_hash": self.command_hash,
            "duration_ms": self.duration_ms,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


def _reject(
    error_type: str,
    error_message: str,
) -> ExecutionResult:
    return ExecutionResult(
        exit_code=None,
        stdout="",
        stderr="",
        timed_out=False,
        truncated=False,
        command_hash=None,
        duration_ms=0.0,
        error_type=error_type,
        error_message=error_message,
    )


class IsolatedExecutor:
    """Executa comandos estruturados em subprocesso isolado."""

    def __init__(self, contract: dict):
        if not isinstance(contract, dict):
            raise TypeError("contract deve ser dict")

        self._contract = contract
        self._allowed_paths = [
            Path(p) for p in contract.get("allowed_paths", [])
        ]
        self._allowed_commands = set(contract.get("allowed_commands", []))
        self._max_runtime_ms = contract.get("max_runtime_ms", 5000)
        self._max_output_bytes = contract.get("max_output_bytes", 65536)
        self._denied_patterns = contract.get("denied_patterns", [])
        # env esterilizado pode ser sobrescrito pelo contrato
        self._sterile_env = {**STERILE_ENV, **contract.get("sterile_env", {})}

    # ---- validação pré-execução ----

    def _validate(self, command: str, args: list, cwd: Optional[str]) -> Optional[ExecutionResult]:
        """Retorna ExecutionResult de rejeição, ou None se passa."""

        if not isinstance(command, str) or not command:
            return _reject(
                "REJECTED_MALFORMED",
                "command deve ser string não vazia",
            )

        if not isinstance(args, list):
            return _reject(
                "REJECTED_MALFORMED",
                "args deve ser lista",
            )

        for a in args:
            if not isinstance(a, str):
                return _reject(
                    "REJECTED_MALFORMED",
                    f"arg não-string: {a!r}",
                )

        if command not in self._allowed_commands:
            return _reject(
                "REJECTED_COMMAND_NOT_ALLOWED",
                f"command '{command}' não está em allowed_commands",
            )

        # denied_patterns nos args
        import json
        import re
        flat = json.dumps({"command": command, "args": args}, ensure_ascii=False)
        for pat in self._denied_patterns:
            if re.search(pat, flat):
                return _reject(
                    "REJECTED_CONTENT_VIOLATION",
                    f"args batem em denied_pattern: {pat}",
                )

        # cwd deve estar em allowed_paths
        if cwd is None:
            if not self._allowed_paths:
                return _reject(
                    "REJECTED_PATH_ESCAPE",
                    "sem allowed_paths, cwd é obrigatório",
                )
            cwd = str(self._allowed_paths[0])
        else:
            canonical_cwd = os.path.realpath(os.path.abspath(cwd))
            ok = False
            for ap in self._allowed_paths:
                canonical_ap = os.path.realpath(str(ap))
                if (canonical_cwd == canonical_ap or
                        canonical_cwd.startswith(canonical_ap + os.sep)):
                    ok = True
                    break
            if not ok:
                return _reject(
                    "REJECTED_PATH_ESCAPE",
                    f"cwd '{cwd}' fora de allowed_paths",
                )

        return None

    # ---- execução ----

    def execute(
        self,
        command: str,
        args: Optional[list] = None,
        *,
        cwd: Optional[str] = None,
    ) -> ExecutionResult:
        """Executa comando permitido com isolamento estrito."""
        args = args or []

        rejection = self._validate(command, args, cwd)
        if rejection is not None:
            return rejection

        # Hash determinístico do comando
        command_hash = hash_object({
            "command": command,
            "args": args,
            "cwd": cwd,
        })

        # cwd definitivo
        if cwd is None:
            cwd = str(self._allowed_paths[0])

        # garantir que cwd existe (senão subprocess.run falha)
        cwd_path = Path(cwd)
        cwd_path.mkdir(parents=True, exist_ok=True)

        # subprocess.run com isolamento
        started = time.perf_counter()
        timed_out = False
        try:
            proc = subprocess.run(
                [command, *args],
                shell=False,
                cwd=cwd,
                env=self._sterile_env,
                capture_output=True,
                timeout=self._max_runtime_ms / 1000.0,
                check=False,
            )
            stdout_bytes = proc.stdout
            stderr_bytes = proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as e:
            timed_out = True
            stdout_bytes = e.stdout or b""
            stderr_bytes = e.stderr or b""
            exit_code = 124  # SIGTERM-like convention
        except FileNotFoundError as e:
            return _reject(
                "REJECTED_BINARY_NOT_FOUND",
                f"binário não encontrado: {command}",
            )

        duration_ms = (time.perf_counter() - started) * 1000.0

        # trunca output
        truncated = False
        if len(stdout_bytes) > self._max_output_bytes:
            stdout_bytes = stdout_bytes[:self._max_output_bytes]
            truncated = True
        if len(stderr_bytes) > self._max_output_bytes:
            stderr_bytes = stderr_bytes[:self._max_output_bytes]
            truncated = True

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        return ExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            truncated=truncated,
            command_hash=command_hash,
            duration_ms=duration_ms,
        )


__all__ = ["IsolatedExecutor", "ExecutionResult", "STERILE_ENV"]
