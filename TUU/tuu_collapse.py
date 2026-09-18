"""Analytical collapse engine for TUU M7.

This module is epistemic only. It selects or rejects a structural hypothesis;
it does not authorize, execute, or invoke system operations.
"""

from dataclasses import dataclass, field
from math import log2
from typing import Any, List, Optional, Tuple


@dataclass(frozen=True)
class AnalyticalIntent:
    """Epistemic representation of a candidate intent.

    This type deliberately contains no execution or authorization surface.
    """

    intent: str
    confidence: float
    source: str = "collapse"
    metadata: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CandidateEvaluation:
    """Candidate hypothesis evaluated by the analytical layer."""

    intent: str
    confidence: float
    feasibility: float = 1.0
    historical_success: float = 1.0
    risk: float = 0.0
    score: float = 0.0


@dataclass(frozen=True)
class CollapseDecision:
    """Result of analytical collapse or escalation to consensus."""

    transition: str
    selected_intent: Optional[AnalyticalIntent]
    score: float
    confidence: float
    entropy: float
    normalized_entropy: float
    metrics: Tuple[Tuple[str, float], ...]
    reason: str


class CollapseEngine:
    """Collapse candidate hypotheses when structural uncertainty is low.

    Normalized Shannon entropy is used to determine whether a single
    hypothesis is sufficiently dominant. High entropy escalates to the
    epistemic swarm rather than authorizing execution.
    """

    def __init__(self, entropy_threshold: float = 0.5):
        if not 0.0 <= entropy_threshold <= 1.0:
            raise ValueError("entropy_threshold must be between 0 and 1")
        self.entropy_threshold = entropy_threshold

    def evaluate(
        self, candidates: List[CandidateEvaluation]
    ) -> CollapseDecision:
        if not candidates:
            return CollapseDecision(
                transition="consensus",
                selected_intent=None,
                score=0.0,
                confidence=0.0,
                entropy=0.0,
                normalized_entropy=0.0,
                metrics=(("candidate_count", 0.0),),
                reason="No candidates available; escalation to consensus required.",
            )

        scores = [float(candidate.score) for candidate in candidates]
        if any(score < 0.0 for score in scores):
            raise ValueError("Candidate scores must be non-negative.")

        total = sum(scores)
        if total <= 0.0:
            probabilities = [1.0 / len(candidates)] * len(candidates)
        else:
            probabilities = [score / total for score in scores]

        entropy = -sum(
            probability * log2(probability)
            for probability in probabilities
            if probability > 0.0
        )
        max_entropy = log2(len(candidates)) if len(candidates) > 1 else 0.0
        normalized_entropy = (
            entropy / max_entropy if max_entropy > 0.0 else 0.0
        )

        ranked = sorted(
            zip(candidates, probabilities),
            key=lambda item: item[0].score,
            reverse=True,
        )
        top_candidate, top_probability = ranked[0]

        metrics = (
            ("candidate_count", float(len(candidates))),
            ("top_probability", float(top_probability)),
            ("entropy", float(entropy)),
            ("normalized_entropy", float(normalized_entropy)),
            ("entropy_threshold", float(self.entropy_threshold)),
        )

        if normalized_entropy < self.entropy_threshold:
            selected = AnalyticalIntent(
                intent=top_candidate.intent,
                confidence=float(top_candidate.confidence),
                source="collapse",
            )
            return CollapseDecision(
                transition="collapse",
                selected_intent=selected,
                score=float(top_candidate.score),
                confidence=float(top_candidate.confidence),
                entropy=float(entropy),
                normalized_entropy=float(normalized_entropy),
                metrics=metrics,
                reason="Structural uncertainty is below the collapse threshold.",
            )

        return CollapseDecision(
            transition="consensus",
            selected_intent=None,
            score=float(top_candidate.score),
            confidence=float(top_candidate.confidence),
            entropy=float(entropy),
            normalized_entropy=float(normalized_entropy),
            metrics=metrics,
            reason="Structural uncertainty requires epistemic consensus.",
        )
