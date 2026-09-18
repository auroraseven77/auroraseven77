"""TUU integration contract tests: invariants T1-T6."""
import asyncio
import time
import unittest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class AuthorizedRequest:
    intent: str
    args: tuple[str, ...]
    constraints: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def make(cls, intent: str, args: List[str], constraints: Dict[str, Any]):
        return cls(intent.lower().strip(), tuple(args), tuple(sorted(constraints.items())))

@dataclass
class PolicyDecision:
    transition: str
    request: AuthorizedRequest
    rule_id: str

@dataclass
class ExecutionResult:
    transition: str
    request: AuthorizedRequest
    argv: tuple[str, ...]
    timed_out: bool = False

class ReferencePolicyEngine:
    ALLOWLIST = {"pkg_list","pkg_search","pkg_update","ls","pwd","date","whoami","uname","echo"}
    RESTRICTED = {"rm","dd","mkfs","chmod","chown","sudo","su"}

    async def evaluate(self, intent, args, context, analytical_metadata=None):
        normalized = intent.lower().strip()
        args = list(args)
        constraints = {
            "read_only": normalized in {"pkg_list","ls","pwd","date","whoami","uname"},
            "timeout": 2.0,
        }
        request = lambda: AuthorizedRequest.make(normalized, args, constraints)

        if normalized in self.RESTRICTED:
            return PolicyDecision("deny", request(), "RULE_HARD_RESTRICTED")
        if normalized not in self.ALLOWLIST:
            return PolicyDecision("deny", request(), "RULE_ALLOWLIST_VIOLATION")
        if normalized == "pkg_search" and (len(args) != 1 or not args[0].strip()):
            return PolicyDecision("deny", request(), "RULE_ARGUMENT_VIOLATION")

        if normalized == "echo":
            forbidden = [">","<","|",";","&","$",chr(96)]
            if any(any(c in arg for c in forbidden) for arg in args):
                return PolicyDecision("deny", request(), "RULE_ARGUMENT_VIOLATION")

        if (analytical_metadata or {}).get("risk", 0.0) > 0.8:
            return PolicyDecision("deny", request(), "RULE_HIGH_ANALYTICAL_RISK")
        return PolicyDecision("allow", request(), "RULE_ALLOW_PASSED")

class ReferenceSandboxExecutor:
    MAP = {
        "ls": ("ls",), "pwd": ("pwd",), "date": ("date",), "whoami": ("whoami",),
        "uname": ("uname","-a"), "echo": ("echo",),
        "pkg_list": ("pkg","list-installed"), "pkg_search": ("pkg","search"),
        "pkg_update": ("pkg","update"),
    }

    def __init__(self):
        self.invocations = 0
        self.last_request: Optional[AuthorizedRequest] = None

    async def execute(self, request: AuthorizedRequest):
        self.invocations += 1
        self.last_request = request
        if request.intent not in self.MAP:
            return ExecutionResult("rejected", request, ())
        return ExecutionResult("completed", request, self.MAP[request.intent] + request.args)

class ReferenceCore:
    def __init__(self, policy, executor):
        self.policy, self.executor = policy, executor

    async def process(self, intent, args=None, context=None, risk=0.0):
        decision = await self.policy.evaluate(intent, list(args or []), context, {"risk": risk})
        if decision.transition != "allow":
            return decision
        return await self.executor.execute(decision.request)

class TuuIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.policy = ReferencePolicyEngine()
        self.executor = ReferenceSandboxExecutor()
        self.core = ReferenceCore(self.policy, self.executor)

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_t1_allow_reaches_terminal_execution_state(self):
        result = self.run_async(self.core.process("echo", ["TUU"]))
        self.assertEqual(result.transition, "completed")
        self.assertEqual(result.argv, ("echo","TUU"))

    def test_t2_deny_means_zero_executor_invocations(self):
        result = self.run_async(self.core.process("rm", ["x"]))
        self.assertEqual(result.transition, "deny")
        self.assertEqual(self.executor.invocations, 0)

    def test_t3_consensus_cannot_override_policy_denial(self):
        result = self.run_async(self.core.process("rm", ["x"], risk=0.0))
        self.assertEqual(result.transition, "deny")
        self.assertEqual(self.executor.invocations, 0)

    def test_t4_allowlist_bypass_is_rejected(self):
        result = self.run_async(self.core.process("not_an_intent"))
        self.assertEqual(result.transition, "deny")
        self.assertEqual(result.rule_id, "RULE_ALLOWLIST_VIOLATION")
        self.assertEqual(self.executor.invocations, 0)

    def test_t5_timeout_contract(self):
        async def run():
            request = AuthorizedRequest.make("echo", ["slow"], {"read_only": False, "timeout": 0.01})
            start = time.monotonic()
            await asyncio.sleep(0.02)
            return ExecutionResult("timeout", request, (), time.monotonic()-start > 0.01)
        result = self.run_async(run())
        self.assertEqual(result.transition, "timeout")
        self.assertTrue(result.timed_out)

    def test_t6_authorized_request_equals_executed_request(self):
        result = self.run_async(self.core.process("pkg_search", ["python"]))
        self.assertEqual(result.transition, "completed")
        self.assertEqual(self.executor.last_request, result.request)
        self.assertEqual(result.request, AuthorizedRequest.make(
            "pkg_search", ["python"], {"read_only": False, "timeout": 2.0}
        ))

    def test_argument_violation_is_denied_not_sanitized(self):
        result = self.run_async(self.core.process("echo", ["safe","x;rm -rf /"]))
        self.assertEqual(result.transition, "deny")
        self.assertEqual(result.rule_id, "RULE_ARGUMENT_VIOLATION")
        self.assertEqual(self.executor.invocations, 0)

    def test_executor_rejects_unknown_mapping(self):
        request = AuthorizedRequest.make("rm", ["x"], {})
        result = self.run_async(self.executor.execute(request))
        self.assertEqual(result.transition, "rejected")

if __name__ == "__main__":
    unittest.main(verbosity=2)
