"""Epistemic swarm consensus engine for TUU M7.

This module aggregates independent agent opinions into a consensus state.
It is analytical only: consensus never authorizes or executes an action.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class AgentOpinion:
    """Independent epistemic opinion supplied by an analytical agent."""

    agent_id: str
    intent: str
    confidence: float
    feasibility: float = 1.0
    risk: float = 0.0
    rationale: str = ""


@dataclass(frozen=True)
class ConsensusState:
    """Aggregated epistemic state.

    This type deliberately contains no AuthorizedRequest or execution surface.
    """

    transition: str
    selected_intent: Optional[str]
    quorum: float
    agreement: float
    margin: float
    opinions: Tuple[AgentOpinion, ...] = field(default_factory=tuple)
    reason: str = ""


class SwarmEngine:
    """Resolve agent opinions using quorum, agreement, and margin thresholds."""

    def __init__(
        self,
        quorum_threshold: float = 0.75,
        agreement_threshold: float = 0.75,
        margin_threshold: float = 0.20,
    ):
        for name, value in (
            ("quorum_threshold", quorum_threshold),
            ("agreement_threshold", agreement_threshold),
            ("margin_threshold", margin_threshold),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        self.quorum_threshold = quorum_threshold
        self.agreement_threshold = agreement_threshold
        self.margin_threshold = margin_threshold

    def resolve(self, opinions: List[AgentOpinion]) -> ConsensusState:
        if not opinions:
            return ConsensusState(
                transition="unresolved",
                selected_intent=None,
                quorum=0.0,
                agreement=0.0,
                margin=0.0,
                opinions=tuple(),
                reason="No agent opinions available.",
            )

        intent_counts = {}
        for opinion in opinions:
            intent_counts[opinion.intent] = intent_counts.get(opinion.intent, 0) + 1

        ranked = sorted(
            intent_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
        top_intent, top_count = ranked[0]
        second_count = ranked[1][1] if len(ranked) > 1 else 0
        total = len(opinions)

        quorum = top_count / total
        top_opinions = [
            opinion for opinion in opinions if opinion.intent == top_intent
        ]
        agreement = sum(
            opinion.confidence for opinion in top_opinions
        ) / len(top_opinions)
        margin = (top_count - second_count) / total

        resolved = (
            quorum >= self.quorum_threshold
            and agreement >= self.agreement_threshold
            and margin >= self.margin_threshold
        )

        if resolved:
            return ConsensusState(
                transition="consensus",
                selected_intent=top_intent,
                quorum=float(quorum),
                agreement=float(agreement),
                margin=float(margin),
                opinions=tuple(opinions),
                reason="Consensus thresholds satisfied.",
            )

        return ConsensusState(
            transition="unresolved",
            selected_intent=None,
            quorum=float(quorum),
            agreement=float(agreement),
            margin=float(margin),
            opinions=tuple(opinions),
            reason="Consensus thresholds not satisfied.",
        )
