"""
TUU/execution.py
================
Camada de execução isolada do TUU Core.
Garante a execução determinística e auditável de comandos autorizados,
impondo defesa em profundidade, isolamento de subprocesso (shell=False) e limites de tempo.
"""

from typing import Literal
import shlex
import subprocess
from pydantic import BaseModel, ConfigDict
from TUU.authorization import AuthorizationDecision

HARDCODED_ALLOWLIST: frozenset[str] = frozenset({
    "ls", "pwd", "uname", "whoami", "date", "ping", "echo"
})


class ExecutionResult(BaseModel):
    """Resultado imutável da execução de um comando."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str
    executed: bool
    returncode: int
    stdout: str
    stderr: str
    error_message: str | None = None


def execute_command_securely(
    decision: AuthorizationDecision,
    timeout: float = 5.0,
    override_allowlist: frozenset[str] | None = None,
) -> ExecutionResult:
    """Executa somente uma decisão aprovada e um executável presente na allowlist."""
    if decision.status != "approved":
        raise PermissionError(
            f"Execução negada: a decisão de autorização possui status '{decision.status}'."
        )

    try:
        tokens = shlex.split(decision.intent)
    except Exception as e:
        return ExecutionResult(
            intent=decision.intent, executed=False, returncode=-1,
            stdout="", stderr="", error_message=f"Falha na tokenização da intenção: {str(e)}",
        )

    if not tokens:
        return ExecutionResult(
            intent=decision.intent, executed=False, returncode=-1,
            stdout="", stderr="", error_message="Intenção vazia ou inválida.",
        )

    executable = tokens[0]
    allowlist = override_allowlist if override_allowlist is not None else HARDCODED_ALLOWLIST

    if executable not in allowlist:
        raise PermissionError(
            f"Execução negada: o executável '{executable}' não consta na allowlist de execução."
        )

    try:
        completed = subprocess.run(
            tokens, shell=False, capture_output=True, text=True, timeout=timeout,
        )
        return ExecutionResult(
            intent=decision.intent, executed=True, returncode=completed.returncode,
            stdout=completed.stdout, stderr=completed.stderr,
            error_message=None if completed.returncode == 0 else f"Processo finalizado com código {completed.returncode}",
        )
    except subprocess.TimeoutExpired as exc:
        return ExecutionResult(
            intent=decision.intent, executed=False, returncode=-1,
            stdout=exc.stdout if isinstance(exc.stdout, str) else "",
            stderr=exc.stderr if isinstance(exc.stderr, str) else "",
            error_message=f"Timeout atingido após {timeout}s na execução do comando.",
        )
    except Exception as exc:
        return ExecutionResult(
            intent=decision.intent, executed=False, returncode=-1,
            stdout="", stderr="", error_message=f"Erro de execução em subprocesso: {str(exc)}",
        )
