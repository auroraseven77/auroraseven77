"""M7 integration tests for collapse -> swarm -> policy isolation."""

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tuu_collapse import CandidateEvaluation, CollapseEngine
from TUU.authorization import AuthorizationContext
from tuu_core import (
    AgentMetricOutput,
    TUUCore,
    process_intent_lifecycle,
)
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

    def test_m7_3_consensus_does_not_bypass_authorization(self):
        metrics = [
            AgentMetricOutput(
                intent="rm",
                confidence=1.0,
                feasibility=1.0,
                historical_success=1.0,
                risk=0.0,
            ),
        ]

        result = self.run_async(
            process_intent_lifecycle(
                metrics=metrics,
                authorization_context=AuthorizationContext(
                    user_id="operator_01",
                ),
                entropy_consensus_threshold=0.25,
                s_min=0.50,
                timeout=5.0,
            )
        )

        self.assertEqual(result.final_state, "blocked")
        self.assertIsNotNone(result.collapsed_candidate)
        self.assertEqual(result.collapsed_candidate.intent, "rm")
        self.assertIsNotNone(result.authorization)
        self.assertEqual(result.authorization.status, "rejected")
        self.assertEqual(
            result.authorization.policy_evaluated,
            "allowlist_policy",
        )
        self.assertIsNone(result.execution)

    def test_m7_4_allow_path_preserves_intent_continuity(self):
        metrics = [
            AgentMetricOutput(
                intent="echo",
                confidence=1.0,
                feasibility=1.0,
                historical_success=1.0,
                risk=0.0,
            ),
        ]

        result = self.run_async(
            process_intent_lifecycle(
                metrics=metrics,
                authorization_context=AuthorizationContext(
                    user_id="operator_01",
                ),
                entropy_consensus_threshold=0.25,
                s_min=0.50,
                timeout=5.0,
            )
        )

        self.assertEqual(result.final_state, "completed")
        self.assertIsNotNone(result.collapsed_candidate)
        self.assertEqual(result.collapsed_candidate.intent, "echo")

        self.assertIsNotNone(result.authorization)
        self.assertEqual(result.authorization.status, "approved")
        self.assertEqual(
            result.authorization.intent,
            result.collapsed_candidate.intent,
        )

        self.assertIsNotNone(result.execution)
        self.assertTrue(result.execution.executed)
        self.assertEqual(
            result.execution.intent,
            result.authorization.intent,
        )

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
