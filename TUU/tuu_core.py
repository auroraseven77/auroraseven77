"""TUU/tuu_core.py - Orquestrador principal e ciclo epistemico -> autorizacao -> execucao."""

import asyncio
import hashlib
import math
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from TUU.authorization import (
    AuthorizationContext,
    AuthorizationDecision,
    JsonValue,
    evaluate_authorization,
    freeze_value,
)
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
    if raw_score < 0.0:
        raise ValueError(
            f"Score negativo rejeitado pelo contrato TUU "
            f"(S_i={raw_score:.6f}, intent='{intent}')"
        )
    # Preserve numeric precision for downstream consensus and lifecycle decisions.
    # Negative raw scores are rejected immediately above; only the upper bound applies.
    score = min(1.0, raw_score)
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


def _calculate_swarm_consensus_raw(
    candidates: tuple[CandidateEvaluation, ...],
) -> tuple[float, float, tuple[float, ...], float, int]:
    """Return unrounded H_N, K_N, probabilities, selected score, and winner index."""
    if not candidates:
        return 0.0, 0.0, (), 0.0, -1

    scores = tuple(max(0.0, candidate.score) for candidate in candidates)
    n = len(scores)

    if n == 1:
        h_n_raw = 0.0
        probabilities_raw = (1.0,)
    else:
        total = math.fsum(scores)
        if total <= 0.0:
            probabilities_raw = tuple(1.0 / n for _ in scores)
            h_n_raw = 1.0
        else:
            probabilities_raw = tuple(score / total for score in scores)
            entropy = -math.fsum(
                probability * math.log2(probability)
                for probability in probabilities_raw
                if probability > 0.0
            )
            h_n_raw = entropy / math.log2(n)

    k_n_raw = 1.0 - h_n_raw
    max_score = max(scores)
    # Keep the current main contract: SHA-256 breaks exact ties only.
    tied_indices = [
        index for index, score in enumerate(scores)
        if score == max_score
    ]
    winner_index = min(
        tied_indices,
        key=lambda index: hashlib.sha256(
            candidates[index].intent.encode("utf-8")
        ).hexdigest(),
    )
    selected_score_raw = scores[winner_index]
    return h_n_raw, k_n_raw, probabilities_raw, selected_score_raw, winner_index


def calculate_swarm_consensus(
    candidates: tuple[CandidateEvaluation, ...],
    *,
    tau_k: float = 0.25,
    s_min: float = 0.50,
) -> tuple[float, float, float, int]:
    """Return rounded presentation values, preserving the public tuple API.

    Lifecycle gates use _calculate_swarm_consensus_raw directly; these rounded
    values are intended for display and existing callers that consume the
    four-value presentation tuple.
    """
    h_n_raw, k_n_raw, _, selected_score_raw, winner_index = (
        _calculate_swarm_consensus_raw(candidates)
    )
    return (
        round(h_n_raw, 6),
        round(k_n_raw, 6),
        round(selected_score_raw, 4),
        winner_index,
    )

TUULifecycleState = Literal[
    "evaluating", "resolving", "consensus", "collapsed",
    "executing", "completed", "blocked",
]


class LifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    state: TUULifecycleState
    message: str
    metadata: Mapping[str, JsonValue] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def enforce_recursive_immutability(cls, v: Any) -> Mapping[str, JsonValue]:
        return freeze_value(v)


class LifecycleResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    final_state: TUULifecycleState
    candidates: tuple[CandidateEvaluation, ...]
    entropy_normalized: float
    probabilities_raw: tuple[float, ...] = Field(default_factory=tuple)
    h_n_raw: float = 0.0
    k_n_raw: float = 0.0
    collapsed_candidate: CandidateEvaluation | None = None
    authorization: AuthorizationDecision | None = None
    execution: ExecutionResult | None = None
    events: tuple[LifecycleEvent, ...] = Field(default_factory=tuple)

    @field_validator("candidates", "events", mode="before")
    @classmethod
    def enforce_immutable_sequences(cls, v: Any) -> tuple:
        if isinstance(v, list):
            return tuple(v)
        return v


async def process_intent_lifecycle(
    metrics: list[AgentMetricOutput],
    *,
    authorization_context: AuthorizationContext | None = None,
    entropy_consensus_threshold: float = 0.25,
    s_min: float = 0.50,
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
            probabilities_raw=(),
            h_n_raw=0.0,
            k_n_raw=0.0,
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

    h_n_raw, k_n_raw, probabilities_raw, selected_score_raw, winner_index = (
        _calculate_swarm_consensus_raw(candidates)
    )
    # Preserve rounded telemetry while using raw values for every gate.
    h_n = round(h_n_raw, 6)
    k_n = round(k_n_raw, 6)
    selected_score = round(selected_score_raw, 4)
    events.append(
        LifecycleEvent(
            state="consensus" if k_n_raw >= entropy_consensus_threshold and selected_score_raw >= s_min else "resolving",
            message="Normalized Shannon entropy and consensus circuit evaluated.",
            metadata={
                "entropy_normalized": h_n,
                "consensus_normalized": k_n,
                "selected_score": selected_score,
                "probabilities_raw": probabilities_raw,
                "h_n_raw": h_n_raw,
                "k_n_raw": k_n_raw,
                "selected_score_raw": selected_score_raw,
                "tau_k": entropy_consensus_threshold,
                "s_min": s_min,
            },
        )
    )

    if (
        k_n_raw < entropy_consensus_threshold
        or selected_score_raw < s_min
    ):
        events.append(
            LifecycleEvent(
                state="resolving",
                message="Consensus circuit retained lifecycle in resolving.",
            )
        )
        return LifecycleResult(
            final_state="resolving",
            candidates=candidates,
            entropy_normalized=h_n,
            probabilities_raw=probabilities_raw,
            h_n_raw=h_n_raw,
            k_n_raw=k_n_raw,
            events=tuple(events),
        )

    if winner_index < 0:
        return LifecycleResult(
            final_state="blocked",
            candidates=candidates,
            entropy_normalized=h_n,
            probabilities_raw=probabilities_raw,
            h_n_raw=h_n_raw,
            k_n_raw=k_n_raw,
            events=tuple(events),
        )

    collapsed = candidates[winner_index]
    events.append(
        LifecycleEvent(
            state="collapsed",
            message="Deterministic collapse selected the consensus candidate.",
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
            entropy_normalized=h_n,
            probabilities_raw=probabilities_raw,
            h_n_raw=h_n_raw,
            k_n_raw=k_n_raw,
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
        entropy_normalized=h_n,
        probabilities_raw=probabilities_raw,
        h_n_raw=h_n_raw,
        k_n_raw=k_n_raw,
        collapsed_candidate=collapsed,
        authorization=authorization,
        execution=execution,
        events=tuple(events),
    )
