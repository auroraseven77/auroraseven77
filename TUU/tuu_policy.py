from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class AuthorizedRequest:
    intent: str
    args: Tuple[str, ...]
    constraints: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        intent: str,
        args: List[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> "AuthorizedRequest":
        normalized_intent = intent.lower().strip()
        normalized_args = tuple(args)
        constraints = constraints or {}
        constraints_tuple = tuple(
            sorted(
                (
                    key,
                    tuple(value) if isinstance(value, (list, tuple)) else value,
                )
                for key, value in constraints.items()
            )
        )
        return cls(normalized_intent, normalized_args, constraints_tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "args": list(self.args),
            "constraints": {
                key: list(value) if isinstance(value, tuple) else value
                for key, value in self.constraints
            },
        }


@dataclass(frozen=True)
class PolicyDecision:
    transition: str
    intent: str
    rule_id: str
    reason: str
    authorized_request: Optional[AuthorizedRequest] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PolicyEngine:
    DEFAULT_ALLOWLIST = {
        "pkg_list", "pkg_search", "pkg_update",
        "ls", "pwd", "date", "whoami", "uname", "echo",
    }
    DEFAULT_RESTRICTED = {"rm", "dd", "mkfs", "chmod", "chown", "sudo", "su"}

    def __init__(
        self,
        allowlist: Optional[set] = None,
        restricted_intents: Optional[set] = None,
    ):
        self.allowlist = (
            set(allowlist) if allowlist is not None else set(self.DEFAULT_ALLOWLIST)
        )
        self.restricted_intents = (
            set(restricted_intents)
            if restricted_intents is not None
            else set(self.DEFAULT_RESTRICTED)
        )

    async def evaluate(
        self,
        intent: str,
        args: List[str],
        context: Any = None,
        analytical_metadata: Optional[Dict[str, Any]] = None,
    ) -> PolicyDecision:
        normalized_intent = intent.lower().strip()
        normalized_args = list(args)
        constraints = {
            "timeout": 2.0,
            "read_only": normalized_intent
            in {"ls", "pwd", "date", "whoami", "uname", "pkg_list"},
        }
        authorized_request = AuthorizedRequest.create(
            normalized_intent, normalized_args, constraints
        )

        if normalized_intent in self.restricted_intents:
            return PolicyDecision(
                "deny",
                normalized_intent,
                "RULE_HARD_RESTRICTED",
                f"Intent '{normalized_intent}' is explicitly restricted.",
                authorized_request,
            )

        if not self._validate_args_normatively(normalized_intent, normalized_args):
            return PolicyDecision(
                "deny",
                normalized_intent,
                "RULE_ARGUMENT_VIOLATION",
                f"Arguments for '{normalized_intent}' violated security constraints.",
                authorized_request,
            )

        if normalized_intent not in self.allowlist:
            return PolicyDecision(
                "deny",
                normalized_intent,
                "RULE_ALLOWLIST_VIOLATION",
                f"Intent '{normalized_intent}' is not present in the execution allowlist.",
                authorized_request,
            )

        risk = (analytical_metadata or {}).get("risk", 0.0)
        if risk > 0.8:
            return PolicyDecision(
                "deny",
                normalized_intent,
                "RULE_HIGH_ANALYTICAL_RISK",
                f"Execution denied by policy due to excessive analytical risk ({risk}).",
                authorized_request,
            )

        return PolicyDecision(
            "allow",
            normalized_intent,
            "RULE_ALLOW_PASSED",
            "Intent successfully cleared all policy gates.",
            authorized_request,
        )

    def _validate_args_normatively(self, intent: str, args: List[str]) -> bool:
        if intent == "echo":
            forbidden = {">", "<", "|", ";", "&", "$", "`"}
            return not any(any(char in arg for char in forbidden) for arg in args)

        if intent == "pkg_search":
            return len(args) == 1 and bool(args[0].strip())

        return True
