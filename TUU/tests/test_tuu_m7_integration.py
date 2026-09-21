"""M7 integration tests for collapse -> swarm -> policy isolation."""

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tuu_collapse import CandidateEvaluation, CollapseEngine
from tuu_core import TUUCore
from tuu_policy import PolicyEngine
from tuu_swarm import AgentOpinion, SwarmEngine


class SpyExecutor:
    def __init__(self):
        self.calls = 0

    async def execute(self, decision):
        self.calls += 1
        raise AssertionError("Executor.execute must not be called.")


class TuuM7IntegrationTests(unittest.TestCase):
    def run_async(self, coro):
        return asyncio.run(coro)

    def test_m7_1_collapse_isolation(self):
        engine = CollapseEngine(entropy_threshold=0.5)
        decision = engine.evaluate(
            [
                CandidateEvaluation("echo", 0.99, score=0.98),
                CandidateEvaluation("pwd", 0.80, score=0.01),
            ]
        )

        self.assertEqual(decision.transition, "collapse")
        self.assertIsNotNone(decision.selected_intent)
        self.assertEqual(decision.selected_intent.intent, "echo")
        self.assertLess(decision.normalized_entropy, 0.5)
        self.assertEqual(decision.score, 0.98)
        self.assertEqual(decision.confidence, 0.99)
        self.assertFalse(hasattr(decision, "authorized_request"))

    def test_m7_2_unanimous_swarm_consensus(self):
        engine = SwarmEngine()
        state = engine.resolve(
            [
                AgentOpinion("a1", "echo", 1.0),
                AgentOpinion("a2", "echo", 1.0),
                AgentOpinion("a3", "echo", 1.0),
                AgentOpinion("a4", "echo", 1.0),
            ]
        )
        self.assertEqual(state.transition, "consensus")
        self.assertEqual(state.selected_intent, "echo")
        self.assertEqual(state.quorum, 1.0)
        self.assertEqual(state.agreement, 1.0)
        self.assertEqual(state.margin, 1.0)
        self.assertFalse(hasattr(state, "authorized_request"))

    def test_m7_3_high_entropy_consensus_then_policy_deny_blocks_executor(self):
        collapse = CollapseEngine(entropy_threshold=0.5)
        swarm = SwarmEngine()
        executor = SpyExecutor()
        core = TUUCore(
            PolicyEngine(),
            executor,
            collapse_engine=collapse,
            swarm_engine=swarm,
        )

        message = SimpleNamespace(
            candidates=[
                CandidateEvaluation("rm", 1.0, risk=0.0, score=1.0),
                CandidateEvaluation("rm", 1.0, risk=0.0, score=1.0),
                CandidateEvaluation("rm", 1.0, risk=0.0, score=1.0),
            ],
            opinions=[
                AgentOpinion("a1", "rm", 1.0),
                AgentOpinion("a2", "rm", 1.0),
                AgentOpinion("a3", "rm", 1.0),
                AgentOpinion("a4", "rm", 1.0),
            ],
            args=["x"],
            context={},
            analytical_metadata={"risk": 0.0},
        )

        result = self.run_async(core.process(message))

        self.assertEqual(result.transition, "deny")
        self.assertEqual(result.rule_id, "RULE_HARD_RESTRICTED")
        self.assertEqual(executor.calls, 0)

    def test_m7_4_allow_path_preserves_authorized_request_identity(self):
        executor = AsyncMock()
        core = TUUCore(
            PolicyEngine(),
            executor,
            collapse_engine=CollapseEngine(entropy_threshold=0.5),
            swarm_engine=SwarmEngine(),
        )

        from tuu_executor import ExecutionResult
        from tuu_policy import AuthorizedRequest

        async def execute(decision):
            return ExecutionResult(
                transition="completed",
                intent=decision.intent,
                executed_request=decision.authorized_request,
                return_code=0,
                stdout="TUU\\n",
                stderr="",
                duration_ms=0.0,
            )

        executor.execute.side_effect = execute

        message = SimpleNamespace(
            candidates=[
                CandidateEvaluation("echo", 1.0, score=0.999),
                CandidateEvaluation("pwd", 1.0, score=0.001),
            ],
            args=["TUU"],
            context={},
            analytical_metadata={"risk": 0.0},
        )

        result = self.run_async(core.process(message))

        self.assertEqual(result.transition, "completed")
        self.assertIsInstance(result.executed_request, AuthorizedRequest)
        self.assertEqual(result.executed_request.intent, "echo")
        self.assertEqual(result.executed_request.args, ("TUU",))
        executor.execute.assert_awaited_once()

    def test_m7_5_core_remains_backward_compatible_without_epistemic_layers(self):
        executor = AsyncMock()
        from tuu_executor import ExecutionResult

        async def execute(decision):
            return ExecutionResult(
                transition="completed",
                intent=decision.intent,
                executed_request=decision.authorized_request,
                return_code=0,
                stdout="TUU\\n",
                stderr="",
                duration_ms=0.0,
            )

        executor.execute.side_effect = execute
        core = TUUCore(PolicyEngine(), executor)

        message = SimpleNamespace(
            intent="echo",
            args=["TUU"],
            context={},
            analytical_metadata={"risk": 0.0},
        )

        result = self.run_async(core.process(message))

        self.assertEqual(result.transition, "completed")
        self.assertEqual(result.stdout, "TUU\\n")
        executor.execute.assert_awaited_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
