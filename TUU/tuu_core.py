from typing import Any, Optional


class TUUCore:
    def __init__(
        self,
        policy_engine: Any,
        executor: Any,
        observability_hook: Optional[Any] = None,
    ):
        self.policy = policy_engine
        self.executor = executor
        self.observability = observability_hook

    async def _record(self, event_type: str, data: Any) -> None:
        if self.observability:
            await self.observability(event_type, data)

    async def process(self, message: Any) -> Any:
        payload = getattr(message, "payload", {})
        if not isinstance(payload, dict):
            payload = {}

        intent = getattr(message, "intent", payload.get("intent", "ls"))
        args = getattr(message, "args", payload.get("args", []))
        context = getattr(message, "context", {})
        analytical_metadata = getattr(
            message, "analytical_metadata", {"risk": 0.0}
        )

        policy_decision = await self.policy.evaluate(
            intent=intent,
            args=list(args),
            context=context,
            analytical_metadata=analytical_metadata,
        )
        await self._record("policy_evaluation", policy_decision)

        if policy_decision.transition != "allow":
            return policy_decision

        result = await self.executor.execute(policy_decision)
        await self._record("execution_result", result)
        return result
