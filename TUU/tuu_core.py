"""TUU/tuu_core.py - Orquestrador principal e ciclo epistemico -> autorizacao -> execucao."""

import asyncio
import math
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from TUU.authorization import (\n    AuthorizationContext,\n    AuthorizationDecision,\n    JsonValue,\n    evaluate_authorization,\n    freeze_value,\n)
from TUU.execution import ExecutionResult, execute_command_securely


class AgentMetricOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    feasibility: float = Field(..., ge=0.0, le=1.0)
    historical_success: float = Field(..., ge=0.0, le=1.0)
    risk: float = Field(..., ge=0.0, le=1.0)


class CandidateEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str
    confidence: float
    feasibility: float
    historical_success: float
    risk: float
    score: float = Field(..., ge=0.0, le=1.0)


def compute_candidate_evaluation(
    intent: str,
    metrics: AgentMetricOutput,
    *,
    w_c: float = 0.4,
    w_h: float = 0.2,
    w_v: float = 0.3,
    w_r: float = 0.1,
) -> CandidateEvaluation:
    raw_score = (
        w_c * metrics.confidence
        + w_h * metrics.historical_success
        + w_v * metrics.feasibility
        - w_r * metrics.risk
    )
    score = round(max(0.0, min(1.0, raw_score)), 4)
    return CandidateEvaluation(
        intent=intent,
        confidence=metrics.confidence,
        feasibility=metrics.feasibility,
        historical_success=metrics.historical_success,
        risk=metrics.risk,
        score=score,
    )


def compute_normalized_entropy(scores: list[float]) -> float:
    n = len(scores)
    if n <= 1:
        return 0.0
    total = sum(max(0.0, s) for s in scores)
    if total <= 0.0:
        return 1.0
    probabilities = [max(0.0, s) / total for s in scores]
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0.0)
    return entropy / math.log2(n)


TUULifecycleState = Literal[
    "evaluating", "resolving", "consensus", "collapsed",
    "executing", "completed", "blocked",
]


class LifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: TUULifecycleState
    message: str
    metadata: Mapping[str, Any] = Field(default_factory=dict)


class LifecycleResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    final_state: TUULifecycleState
    candidates: tuple[CandidateEvaluation, ...]
    entropy_normalized: float
    collapsed_candidate: CandidateEvaluation | None = None
    authorization: AuthorizationDecision | None = None
    execution: ExecutionResult | None = None
    events: tuple[LifecycleEvent, ...] = Field(default_factory=tuple)\n\n    @field_validator("candidates", "events", mode="before")\n    @classmethod\n    def enforce_immutable_sequences(cls, v: Any) -> tuple:\n        if isinstance(v, list):\n            return tuple(v)\n        return v


async def process_intent_lifecycle(
    metrics: list[AgentMetricOutput],
    *,
    authorization_context: AuthorizationContext | None = None,
    entropy_consensus_threshold: float = 0.75,
    timeout: float = 5.0,
) -> LifecycleResult:
    events: list[LifecycleEvent] = [
        LifecycleEvent(state="evaluating", message="Epistemic evaluation started.")
    ]

    if not metrics:
        events.append(LifecycleEvent(state="blocked", message="No candidate metrics supplied."))
        return LifecycleResult(
            final_state="blocked",
            candidates=(),
            entropy_normalized=0.0,
            events=tuple(events),
        )

    candidates = tuple(
        compute_candidate_evaluation(item.intent, item)
        for item in metrics
    )
    events.append(
        LifecycleEvent(
            state="evaluating",
            message="Candidate scores computed deterministically.",
            metadata={"candidate_count": len(candidates)},
        )
    )

    entropy_normalized = compute_normalized_entropy([c.score for c in candidates])
    events.append(
        LifecycleEvent(
            state="consensus" if entropy_normalized >= entropy_consensus_threshold else "resolving",
            message="Normalized entropy circuit evaluated.",
            metadata={"entropy_normalized": entropy_normalized},
        )
    )

    if len(candidates) > 1 and entropy_normalized < entropy_consensus_threshold:
        events.append(
            LifecycleEvent(
                state="resolving",
                message="Circuit breaker retained lifecycle in resolving.",
            )
        )
        return LifecycleResult(
            final_state="resolving",
            candidates=candidates,
            entropy_normalized=entropy_normalized,
            events=tuple(events),
        )

    collapsed = max(candidates, key=lambda candidate: candidate.score)
    events.append(
        LifecycleEvent(
            state="collapsed",
            message="Deterministic collapse selected highest-scoring candidate.",
            metadata={"intent": collapsed.intent, "score": collapsed.score},
        )
    )

    context = authorization_context or AuthorizationContext()
    authorization = evaluate_authorization(collapsed, context)

    if authorization.status != "approved":
        events.append(
            LifecycleEvent(
                state="blocked",
                message="Authorization rejected the collapsed candidate.",
                metadata={"reason": authorization.reason},
            )
        )
        return LifecycleResult(
            final_state="blocked",
            candidates=candidates,
            entropy_normalized=entropy_normalized,
            collapsed_candidate=collapsed,
            authorization=authorization,
            events=tuple(events),
        )

    events.append(
        LifecycleEvent(
            state="executing",
            message="Authorization approved; secure execution started.",
            metadata={"intent": authorization.intent},
        )
    )

    execution = await asyncio.to_thread(
        execute_command_securely,
        authorization,
        timeout,
    )
    final_state: TUULifecycleState = "completed" if execution.executed else "blocked"
    events.append(
        LifecycleEvent(
            state=final_state,
            message="Secure execution completed." if execution.executed else "Secure execution failed or timed out.",
            metadata={"returncode": execution.returncode},
        )
    )

    return LifecycleResult(
        final_state=final_state,
        candidates=candidates,
        entropy_normalized=entropy_normalized,
        collapsed_candidate=collapsed,
        authorization=authorization,
        execution=execution,
        events=tuple(events),
    )
