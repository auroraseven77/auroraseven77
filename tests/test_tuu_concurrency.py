"""
tests/test_tuu_concurrency.py
==============================
Suíte de testes de concorrência e carga assíncrona do TUU Core.
Ajustada para respeitar o campo `execution` de LifecycleResult e a autorização
por string exata da intenção.
"""

import asyncio

import pytest

from TUU.authorization import AuthorizationContext
from TUU.tuu_core import AgentMetricOutput, LifecycleEvent, process_intent_lifecycle


@pytest.mark.asyncio
async def test_concurrent_lifecycles_execution_isolation():
    """
    Valida se N execuções simultâneas mantêm isolamento absoluto de dados.
    Verifica se o stdout de cada task refere-se exclusivamente à sua própria intenção.
    """
    num_tasks = 20

    async def run_single_lifecycle(task_id: int):
        intent_str = f"echo task_{task_id}"
        metrics = [
            AgentMetricOutput(
                intent=intent_str,
                confidence=0.9,
                feasibility=0.9,
                historical_success=0.9,
                risk=0.1,
            ),
        ]
        # Autorização exige correspondência exata da string da intenção
        auth_context = AuthorizationContext(
            allowed_commands=frozenset({intent_str}),
            max_allowed_risk=0.5,
        )
        result = await process_intent_lifecycle(
            metrics=metrics,
            auth_context=auth_context,
            entropy_threshold=0.5,
        )
        return task_id, intent_str, result

    tasks = [run_single_lifecycle(i) for i in range(num_tasks)]
    results = await asyncio.gather(*tasks)

    for task_id, expected_intent, result in results:
        assert result.final_state == "completed"
        assert result.collapsed_candidate is not None
        assert result.collapsed_candidate.intent == expected_intent
        assert result.execution is not None
        assert result.execution.executed is True
        assert f"task_{task_id}" in result.execution.stdout


@pytest.mark.asyncio
async def test_concurrent_lifecycles_mixed_outcomes():
    """
    Garante que falhas ou bloqueios em uma execução não afetam tasks paralelas.
    """
    metrics_valid = [
        AgentMetricOutput(
            intent="echo Valid",
            confidence=0.9,
            feasibility=0.9,
            historical_success=0.9,
            risk=0.1,
        ),
    ]
    metrics_blocked = [
        AgentMetricOutput(
            intent="rm -rf /",
            confidence=0.9,
            feasibility=0.9,
            historical_success=0.9,
            risk=0.05,
        ),
    ]
    metrics_resolving = [
        AgentMetricOutput(
            intent="echo A",
            confidence=0.8,
            feasibility=0.8,
            historical_success=0.8,
            risk=0.1,
        ),
        AgentMetricOutput(
            intent="echo B",
            confidence=0.1,
            feasibility=0.1,
            historical_success=0.1,
            risk=0.9,
        ),
    ]

    auth_context = AuthorizationContext(
        allowed_commands=frozenset({"echo Valid"}),
        max_allowed_risk=0.5,
    )

    task_valid = process_intent_lifecycle(
        metrics=metrics_valid,
        auth_context=auth_context,
        entropy_threshold=0.5,
    )
    task_blocked = process_intent_lifecycle(
        metrics=metrics_blocked,
        auth_context=auth_context,
        entropy_threshold=0.5,
    )
    task_resolving = process_intent_lifecycle(
        metrics=metrics_resolving,
        auth_context=auth_context,
        entropy_threshold=0.99,
    )

    res_valid, res_blocked, res_resolving = await asyncio.gather(
        task_valid, task_blocked, task_resolving
    )

    assert res_valid.final_state == "completed"
    assert res_blocked.final_state == "blocked"
    assert res_resolving.final_state == "resolving"


@pytest.mark.asyncio
async def test_event_listener_concurrency_isolation():
    """
    Comprova ausência de vazamento de estado de callbacks: listener_task1
    jamais captura eventos disparados por task2 e vice-versa.
    """
    captured_events_task1: list[LifecycleEvent] = []
    captured_events_task2: list[LifecycleEvent] = []

    async def listener_task1(event: LifecycleEvent):
        captured_events_task1.append(event)

    async def listener_task2(event: LifecycleEvent):
        captured_events_task2.append(event)

    m1 = [
        AgentMetricOutput(
            intent="echo Listener1",
            confidence=0.9,
            feasibility=0.9,
            historical_success=0.9,
            risk=0.1,
        )
    ]
    m2 = [
        AgentMetricOutput(
            intent="echo Listener2",
            confidence=0.9,
            feasibility=0.9,
            historical_success=0.9,
            risk=0.1,
        )
    ]

    ctx1 = AuthorizationContext(
        allowed_commands=frozenset({"echo Listener1"}),
        max_allowed_risk=0.5,
    )
    ctx2 = AuthorizationContext(
        allowed_commands=frozenset({"echo Listener2"}),
        max_allowed_risk=0.5,
    )

    await asyncio.gather(
        process_intent_lifecycle(
            m1,
            auth_context=ctx1,
            entropy_threshold=0.5,
            event_listener=listener_task1,
        ),
        process_intent_lifecycle(
            m2,
            auth_context=ctx2,
            entropy_threshold=0.5,
            event_listener=listener_task2,
        ),
    )

    assert len(captured_events_task1) > 0
    assert len(captured_events_task2) > 0

    assert all("Listener2" not in e.message for e in captured_events_task1)
    assert all("Listener1" not in e.message for e in captured_events_task2)


@pytest.mark.asyncio
async def test_high_volume_concurrency_stress():
    """
    Submete o orquestrador a 50 execuções paralelas simultâneas para validar escalabilidade.
    """
    num_parallel = 50

    async def run_stress(i: int):
        intent_str = f"echo stress_{i}"
        metrics = [
            AgentMetricOutput(
                intent=intent_str,
                confidence=0.9,
                feasibility=0.9,
                historical_success=0.9,
                risk=0.1,
            )
        ]
        ctx = AuthorizationContext(
            allowed_commands=frozenset({intent_str}),
            max_allowed_risk=0.5,
        )
        return await process_intent_lifecycle(
            metrics,
            auth_context=ctx,
            entropy_threshold=0.5,
        )

    results = await asyncio.gather(*(run_stress(i) for i in range(num_parallel)))

    assert len(results) == num_parallel
    assert all(r.final_state == "completed" for r in results)
    assert all(r.execution is not None and r.execution.executed is True for r in results)
