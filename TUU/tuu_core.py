from typing import Any, Optional


class TUUCore:
    def __init__(
        self,
        policy_engine: Any,
        executor: Any,
        observability_hook: Optional[Any] = None,
        collapse_engine: Optional[Any] = None,
        swarm_engine: Optional[Any] = None,
    ):
        self.policy = policy_engine
        self.executor = executor
        self.observability = observability_hook
        self.collapse = collapse_engine
        self.swarm = swarm_engine

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

        if self.collapse is not None:
            candidates = getattr(message, "candidates", payload.get("candidates"))
            if candidates is not None:
                collapse_decision = self.collapse.evaluate(list(candidates))
                await self._record("collapse_decision", collapse_decision)

                if collapse_decision.transition == "consensus":
                    if self.swarm is None:
                        return collapse_decision

                    opinions = getattr(
                        message, "opinions", payload.get("opinions", [])
                    )
                    consensus_state = self.swarm.resolve(list(opinions))
                    await self._record("consensus_state", consensus_state)

                    if consensus_state.selected_intent is None:
                        return consensus_state

                    intent = consensus_state.selected_intent
                elif collapse_decision.selected_intent is not None:
                    intent = collapse_decision.selected_intent.intent

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
