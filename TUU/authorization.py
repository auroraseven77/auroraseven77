"""TUU/authorization.py - Fronteira normativa de autorização."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Mapping, TypeAlias
from typing_extensions import TypeAliasType

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from TUU.tuu_core import CandidateEvaluation


JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue = TypeAliasType(
    "JsonValue",
    "JsonPrimitive | Mapping[str, JsonValue] | tuple[JsonValue, ...]",
)


def freeze_value(val: Any) -> Any:
    """Congela recursivamente estruturas JSON-like."""
    if isinstance(val, dict):
        return MappingProxyType(
            {str(k): freeze_value(v) for k, v in val.items()}
        )
    if isinstance(val, (list, set, tuple)):
        return tuple(freeze_value(v) for v in val)
    return val


class AuthorizationContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = "system"
    environment: Literal["development", "staging", "production"] = "production"
    max_allowed_risk: float = Field(default=0.50, ge=0.0, le=1.0)
    allowed_commands: frozenset[str] = Field(
        default=frozenset({"ls", "pwd", "uname", "whoami", "date", "ping", "echo"})
    )


class AuthorizationDecision(BaseModel):
    """Decisão normativa com metadata recursivamente imutável."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    intent: str
    status: Literal["pending", "approved", "rejected"]
    policy_evaluated: str
    reason: str
    metadata: Mapping[str, JsonValue] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def enforce_recursive_immutability(cls, v: Any) -> Mapping[str, JsonValue]:
        return freeze_value(v)


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
