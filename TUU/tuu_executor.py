import asyncio
import time
from dataclasses import dataclass
from typing import Optional

try:
    from .tuu_policy import AuthorizedRequest, PolicyDecision
except ImportError:
    from tuu_policy import AuthorizedRequest, PolicyDecision


@dataclass(frozen=True)
class ExecutionResult:
    transition: str
    intent: str
    executed_request: Optional[AuthorizedRequest]
    return_code: Optional[int]
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    error: Optional[str] = None


class SandboxExecutor:
    def __init__(self, max_timeout: float = 5.0):
        self.max_timeout = max_timeout
        self.command_map = {
            "ls": ["ls"],
            "pwd": ["pwd"],
            "date": ["date"],
            "whoami": ["whoami"],
            "uname": ["uname", "-a"],
            "echo": ["echo"],
            "pkg_list": ["pkg", "list-installed"],
            "pkg_search": ["pkg", "search"],
            "pkg_update": ["pkg", "update"],
        }
        self.invocations = 0
        self.last_executed_request: Optional[AuthorizedRequest] = None

    async def execute(self, policy_decision: PolicyDecision) -> ExecutionResult:
        if (
            policy_decision.transition != "allow"
            or policy_decision.authorized_request is None
        ):
            return ExecutionResult(
                "rejected",
                policy_decision.intent,
                policy_decision.authorized_request,
                None,
                "",
                "Executor invoked with non-allow policy decision.",
                0.0,
                error="UNAUTHORIZED_EXECUTION",
            )

        self.invocations += 1
        auth_req = policy_decision.authorized_request
        self.last_executed_request = auth_req

        intent = auth_req.intent
        args = list(auth_req.args)
        constraints = dict(auth_req.constraints)

        if intent not in self.command_map:
            return ExecutionResult(
                "rejected",
                intent,
                auth_req,
                None,
                "",
                "No canonical executor mapping found for intent.",
                0.0,
                error="UNKNOWN_INTENT_MAPPING",
            )

        argv = self.command_map[intent] + args
        timeout = min(float(constraints.get("timeout", 2.0)), self.max_timeout)

        start = time.perf_counter()
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()
                return ExecutionResult(
                    "timeout",
                    intent,
                    auth_req,
                    None,
                    "",
                    "",
                    (time.perf_counter() - start) * 1000.0,
                    timed_out=True,
                    error=f"Execution exceeded maximum allowed timeout of {timeout}s.",
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            return ExecutionResult(
                "completed" if process.returncode == 0 else "failed",
                intent,
                auth_req,
                process.returncode,
                stdout,
                stderr,
                (time.perf_counter() - start) * 1000.0,
            )
        except Exception as exc:
            return ExecutionResult(
                "failed",
                intent,
                auth_req,
                None,
                "",
                str(exc),
                (time.perf_counter() - start) * 1000.0,
                error=str(exc),
            )
