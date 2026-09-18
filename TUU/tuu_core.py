"""TUU/tuu_core.py - Orquestrador principal e ciclo epistemico -> autorizacao -> execucao."""

from __future__ import annotations

import asyncio
import math
from typing import Any, Literal, Mapping, TypeAlias

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
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    state: TUULifecycleState
    message: str
    metadata: Mapping[str, JsonValue] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def enforce_recursive_immutability(cls, v: Any) -> Mapping[str, JsonValue]:
        return freeze_value(v)


class LifecycleResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    final_state: TUULifecycleState
    candidates: tuple[CandidateEvaluation, ...]
    entropy_normalized: float
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
