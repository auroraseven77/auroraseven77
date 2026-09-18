"""
TUU/tuu_core.py - Orquestrador Principal (Marcos T1-T6, M7, M8)

Orquestra a transição estrita:
Collapse -> Swarm -> Policy -> Executor -> Attestation -> Telemetry
Preserva a retrocompatibilidade e a barreira de imunidade normativa.
"""

import inspect
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentMetricOutput(BaseModel):
    """
    Hard boundary for Agent Swarm output.

    Agents may emit only the four epistemic metrics. Score, ranking,
    authorization, and execution fields are intentionally forbidden.
    """
    model_config = ConfigDict(extra="forbid")

    confidence: float = Field(..., ge=0.0, le=1.0)
    feasibility: float = Field(..., ge=0.0, le=1.0)
    historical_success: float = Field(..., ge=0.0, le=1.0)
    risk: float = Field(..., ge=0.0, le=1.0)


class CandidateEvaluation(BaseModel):
    """Internal TUU representation after deterministic score computation."""
    model_config = ConfigDict(extra="forbid")

    intent: str
    confidence: float
    feasibility: float
    historical_success: float
    risk: float
    score: float


def compute_candidate_evaluation(
    intent: str,
    metrics: AgentMetricOutput,
    *,
    w_c: float = 0.4,
    w_h: float = 0.2,
    w_v: float = 0.3,
    w_r: float = 0.1,
) -> CandidateEvaluation:
    """Sole deterministic TUU boundary that produces S_i."""
    s_i = (
        w_c * metrics.confidence
        + w_h * metrics.historical_success
        + w_v * metrics.feasibility
        - w_r * metrics.risk
    )
    if s_i < 0.0:
        raise ValueError(
            f"Score negativo rejeitado pelo contrato TUU "
            f"(S_i={s_i:.6f}, intent='{intent}')"
        )
    return CandidateEvaluation(
        intent=intent,
        confidence=metrics.confidence,
        feasibility=metrics.feasibility,
        historical_success=metrics.historical_success,
        risk=metrics.risk,
        score=s_i,
    )


class TUUCore:
    def __init__(
        self,
        policy_engine,
        executor,
        observability_hook=None,
        collapse_engine=None,
        swarm_engine=None,
        attestation_engine=None,
        telemetry_engine=None,
    ):
        self.policy_engine = policy_engine
        self.executor = executor
        self.observability_hook = observability_hook
        self.collapse_engine = collapse_engine
        self.swarm_engine = swarm_engine
        self.attestation_engine = attestation_engine
        self.telemetry_engine = telemetry_engine

        # Backward-compatible aliases used by the original M7 core.
        self.policy = policy_engine
        self.observability = observability_hook
        self.collapse = collapse_engine
        self.swarm = swarm_engine

    def _get_field(self, obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    async def _record(self, event_type: str, data: Any) -> None:
        if self.observability:
            result = self.observability(event_type, data)
            if inspect.isawaitable(result):
                await result

    def _evaluate_policy(self, request: Any):
        intent = self._get_field(request, "intent", "ls")
        args = list(self._get_field(request, "args", []) or [])
        context = self._get_field(request, "context", {})
        analytical_metadata = self._get_field(
            request, "analytical_metadata", {"risk": 0.0}
        )

        return self.policy_engine.evaluate(
            intent=intent,
            args=args,
            context=context,
            analytical_metadata=analytical_metadata,
        )

    async def process(self, request: Any) -> Any:
        """Interface assíncrona principal usada nas suítes de integração."""
        return await self._process_internal(request)

    def process_request(self, request: Any) -> Any:
        """Interface síncrona mantida para chamadas diretas."""
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._process_internal(request))

        # A synchronous API cannot safely block the already-running event loop.
        return self._process_sync(request)

    def _process_sync(self, request: Any) -> Any:
        # Keep the synchronous compatibility path structurally equivalent.
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._process_internal(request))

        raise RuntimeError(
            "process_request() cannot synchronously block a running event loop; "
            "use await process() instead."
        )

    async def _process_internal(self, request: Any) -> Any:
        start_time = time.time()
        request_id = self._get_field(request, "request_id", "req_unknown")

        entropy = 0.0
        quorum = agreement = margin = 1.0
        consensus_state = "consensus"

        # M7: collapse receives the candidate list, never the request envelope.
        if self.collapse_engine is not None:
            candidates = self._get_field(request, "candidates", None)
            if candidates is not None:
                collapse_result = self.collapse_engine.evaluate(list(candidates))
                if inspect.isawaitable(collapse_result):
                    collapse_result = await collapse_result

                entropy = getattr(collapse_result, "entropy", 0.0)
                await self._record("collapse_decision", collapse_result)

                transition = getattr(collapse_result, "transition", None)
                selected = getattr(collapse_result, "selected_intent", None)

                if transition == "consensus":
                    # M7: consensus is analytical only; it never authorizes execution.
                    if self.swarm_engine is None:
                        return await self._finalize(
                            request_id,
                            start_time,
                            entropy,
                            quorum,
                            agreement,
                            margin,
                            "unresolved",
                            "deny",
                            False,
                            None,
                            None,
                        )

                    opinions = self._get_field(request, "opinions", []) or []
                    consensus = self.swarm_engine.resolve(list(opinions))
                    if inspect.isawaitable(consensus):
                        consensus = await consensus

                    quorum = getattr(consensus, "quorum", 1.0)
                    agreement = getattr(consensus, "agreement", 1.0)
                    margin = getattr(consensus, "margin", 1.0)
                    consensus_state = getattr(
                        consensus, "transition", "unresolved"
                    )
                    await self._record("consensus_state", consensus)

                    selected_intent = getattr(consensus, "selected_intent", None)
                    if selected_intent is None:
                        return await self._finalize(
                            request_id,
                            start_time,
                            entropy,
                            quorum,
                            agreement,
                            margin,
                            consensus_state,
                            "deny",
                            False,
                            None,
                            None,
                        )

                    request_intent = selected_intent
                elif selected is not None:
                    request_intent = getattr(selected, "intent", selected)
                else:
                    request_intent = self._get_field(request, "intent", "ls")
            else:
                request_intent = self._get_field(request, "intent", "ls")
        else:
            request_intent = self._get_field(request, "intent", "ls")

        # Policy is the normative barrier and receives explicit arguments.
        policy_request = request
        if request_intent != self._get_field(request, "intent", "ls"):
            # Preserve the original request object where possible while applying
            # the intent selected by the analytical layer.
            from types import SimpleNamespace

            policy_request = SimpleNamespace(
                intent=request_intent,
                args=list(self._get_field(request, "args", []) or []),
                context=self._get_field(request, "context", {}),
                analytical_metadata=self._get_field(
                    request, "analytical_metadata", {"risk": 0.0}
                ),
            )

        policy_result = self._evaluate_policy(policy_request)
        if inspect.isawaitable(policy_result):
            policy_result = await policy_result

        await self._record("policy_evaluation", policy_result)

        policy_decision = getattr(policy_result, "transition", None)
        if policy_decision is None:
            policy_decision = (
                policy_result.get("decision", "DENY")
                if isinstance(policy_result, dict)
                else "DENY"
            )

        allowed = str(policy_decision).lower() in {"allow", "allowed"}

        if not allowed:
            return await self._finalize(
                request_id,
                start_time,
                entropy,
                quorum,
                agreement,
                margin,
                consensus_state,
                policy_decision,
                False,
                None,
                policy_result,
            )

        # PolicyDecision is the executor's authorization surface. Do not call
        # PolicyEngine.authorize() here: doing so would bypass the established
        # PolicyDecision -> Executor contract.
        execution_output = self.executor.execute(policy_result)
        if inspect.isawaitable(execution_output):
            execution_output = await execution_output

        await self._record("execution_result", execution_output)

        return await self._finalize(
            request_id,
            start_time,
            entropy,
            quorum,
            agreement,
            margin,
            consensus_state,
            policy_decision,
            True,
            execution_output,
            execution_output,
        )

    async def _finalize(
        self,
        request_id: str,
        start_time: float,
        entropy: float,
        quorum: float,
        agreement: float,
        margin: float,
        consensus_state: str,
        policy_decision: Any,
        executed: bool,
        execution_output: Any,
        return_value: Any,
    ) -> Any:
        attestation_hash = "0" * 64

        if self.attestation_engine:
            try:
                attestation = self.attestation_engine.create_attestation(
                    request_id=request_id,
                    entropy=entropy,
                    quorum=quorum,
                    agreement=agreement,
                    margin=margin,
                    consensus_state=consensus_state,
                    policy_decision=policy_decision,
                    executed=executed,
                )
                if inspect.isawaitable(attestation):
                    attestation = await attestation
                attestation_hash = getattr(
                    attestation, "attestation_hash", attestation_hash
                )
            except Exception:
                pass

        latency_ms = (time.time() - start_time) * 1000.0

        if self.telemetry_engine:
            try:
                telemetry = self.telemetry_engine.record(
                    request_id=request_id,
                    latency_ms=latency_ms,
                    entropy=entropy,
                    quorum=quorum,
                    agreement=agreement,
                    margin=margin,
                    consensus_state=consensus_state,
                    policy_decision=policy_decision,
                    executed=executed,
                    attestation_hash=attestation_hash,
                )
                if inspect.isawaitable(telemetry):
                    await telemetry
            except Exception:
                pass

        if self.observability_hook:
            try:
                hook_result = self.observability_hook(
                    {
                        "request_id": request_id,
                        "policy_decision": policy_decision,
                        "executed": executed,
                        "attestation_hash": attestation_hash,
                        "latency_ms": latency_ms,
                    }
                )
                if inspect.isawaitable(hook_result):
                    await hook_result
            except Exception:
                pass

        return return_value
