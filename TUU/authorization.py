"""TUU/authorization.py - Fronteira normativa de autorização.

Mantém o contexto de segurança e a decisão de autorização imutáveis,
separando risco epistemológico da permissão operacional.
"""

from types import MappingProxyType
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from TUU.tuu_core import CandidateEvaluation


class AuthorizationContext(BaseModel):
    """Contexto de segurança imutável injetado pelo ambiente de runtime."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = "system"
    environment: Literal["development", "staging", "production"] = "production"
    max_allowed_risk: float = Field(default=0.50, ge=0.0, le=1.0)
    allowed_commands: frozenset[str] = Field(
        default=frozenset({"ls", "pwd", "uname", "whoami", "date", "ping", "echo"})
    )


class AuthorizationDecision(BaseModel):
    """Resultado com imutabilidade rasa e profunda (deep frozen)."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    intent: str
    status: Literal["pending", "approved", "rejected"]
    policy_evaluated: str
    reason: str
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="after")
    @classmethod
    def enforce_immutable_metadata(cls, v: Any) -> Mapping[str, Any]:
        """Converte dicionários mutáveis em MappingProxyType imutável."""
        if isinstance(v, dict):
            return MappingProxyType(dict(v))
        return v


def evaluate_authorization(
    candidate: CandidateEvaluation,
    context: AuthorizationContext,
) -> AuthorizationDecision:
    """Avaliação operacional isolada e imutável."""

    if candidate.intent not in context.allowed_commands:
        return AuthorizationDecision(
            intent=candidate.intent,
            status="rejected",
            policy_evaluated="allowlist_policy",
            reason=f"Comando '{candidate.intent}' fora da allowlist permitida.",
        )

    if candidate.risk > context.max_allowed_risk:
        return AuthorizationDecision(
            intent=candidate.intent,
            status="rejected",
            policy_evaluated="risk_threshold_policy",
            reason=(
                f"Risco da hipótese ({candidate.risk:.2f}) excede o limite tolerado "
                f"({context.max_allowed_risk:.2f})."
            ),
        )

    return AuthorizationDecision(
        intent=candidate.intent,
        status="approved",
        policy_evaluated="strict_local_policy",
        reason="Hipótese colapsada atende à allowlist e ao limite de risco.",
    )
