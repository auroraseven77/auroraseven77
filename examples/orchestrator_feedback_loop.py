import asyncio
import logging
from typing import List, Protocol
from TUU.tuu_core import process_intent_lifecycle, AgentMetricOutput, LifecycleResult
from TUU.authorization import AuthorizationContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TUUFeedbackLoop")


class InterfaceEnxame(Protocol):
    async def solicitar_votacao(self, contexto: str, rodada: int) -> List[AgentMetricOutput]:
        ...


class EnxameSimulado:
    """Simula a reavaliação de métricas pelo enxame após retenção por entropia."""
    
    async def solicitar_votacao(self, contexto: str, rodada: int) -> List[AgentMetricOutput]:
        logger.info(f"[ENXAME] Gerando propostas | Rodada {rodada}")
        if rodada == 1:
            # S1 = 0.82, S2 = 0.80 -> H_N ~= 1.000, K_N ~= 0.000 (resolving)
            return [
                AgentMetricOutput(intent="echo Task Completed", confidence=0.9, feasibility=0.9, historical_success=0.9, risk=0.1),
                AgentMetricOutput(intent="ls -l", confidence=0.89, feasibility=0.9, historical_success=0.9, risk=0.1)
            ]
        else:
            # S1 = 0.86, S2 = 0.10 -> H_N ~= 0.482, K_N ~= 0.518 (consensus)
            return [
                AgentMetricOutput(intent="echo Task Completed", confidence=1.0, feasibility=0.9, historical_success=1.0, risk=0.1),
                AgentMetricOutput(intent="ls -l", confidence=0.2, feasibility=0.2, historical_success=0.2, risk=0.8)
            ]


class AgenteSentinela:
    """Audita a tupla congelada result.events e classifica o estado final."""
    
    async def avaliar_resultado(self, result: LifecycleResult) -> str:
        for event in result.events:
            logger.info(f"[SENTINELA - HISTÓRICO] State='{event.state}' | Msg='{event.message}'")

        logger.info(f"[SENTINELA - BALANÇO] Estado Final: {result.final_state}")

        if result.final_state == "completed":
            stdout = result.execution.stdout if result.execution else ""
            logger.info(f"[SENTINELA] Sucesso. Output: '{stdout.strip()}'")
            return "RESOLVED"
            
        elif result.final_state == "resolving":
            logger.warning(
                f"[SENTINELA] Retenção por incerteza (H_N = {result.entropy_normalized:.3f}). "
                "Solicitando nova rodada."
            )
            return "RETRY"
            
        elif result.final_state == "blocked":
            motivo = result.authorization.reason if result.authorization else "Rejeição normativa"
            logger.error(f"[SENTINELA] Bloqueio preventivo: '{motivo}'. Abortando.")
            return "ABORT"
            
        return "ABORT"


class AgenteGuardiao:
    """Configura a fronteira normativa e invoca o TUU Core com os contratos corretos."""
    
    def __init__(self, allowed_commands: set[str], default_tau: float = 0.25):
        self.auth_context = AuthorizationContext(
            allowed_commands=frozenset(allowed_commands),
            max_allowed_risk=0.5
        )
        self.default_tau = default_tau
        self.sentinela = AgenteSentinela()

    async def executar_ciclo(
        self,
        metrics: List[AgentMetricOutput],
        tau: float | None = None
    ) -> tuple[LifecycleResult, str]:
        threshold = tau if tau is not None else self.default_tau
        
        result = await process_intent_lifecycle(
            metrics=metrics,
            authorization_context=self.auth_context,
            entropy_consensus_threshold=threshold
        )
        
        diagnostico = await self.sentinela.avaliar_resultado(result)
        return result, diagnostico


class FeedbackLoop:
    """Coordenador de malha fechada entre Enxame, Guardião e Sentinela."""
    
    def __init__(self, guardiao: AgenteGuardiao, enxame: InterfaceEnxame, max_retries: int = 3):
        self.guardiao = guardiao
        self.enxame = enxame
        self.max_retries = max_retries

    async def executar_com_convergencia(self, contexto_tarefa: str, tau: float = 0.25) -> LifecycleResult:
        rodada = 1
        while rodada <= self.max_retries:
            logger.info(f"\n=== MALHA FECHADA: Rodada {rodada}/{self.max_retries} ===")
            metricas = await self.enxame.solicitar_votacao(contexto_tarefa, rodada)
            resultado, diagnostico = await self.guardiao.executar_ciclo(metricas, tau=tau)
            
            if diagnostico == "RESOLVED":
                logger.info(f"[FEEDBACK LOOP] Resolvido na rodada {rodada}.")
                return resultado
            elif diagnostico == "ABORT":
                logger.error("[FEEDBACK LOOP] Bloqueado definitivamente. Encerrando.")
                return resultado
            elif diagnostico == "RETRY":
                rodada += 1
                if rodada <= self.max_retries:
                    await asyncio.sleep(0.1)
                else:
                    logger.error("[FEEDBACK LOOP] Limite de tentativas atingido.")
                    return resultado

        return resultado


async def main():
    enxame = EnxameSimulado()
    guardiao = AgenteGuardiao(allowed_commands={"echo Task Completed", "ls -l"})
    feedback_loop = FeedbackLoop(guardiao=guardiao, enxame=enxame, max_retries=3)

    await feedback_loop.executar_com_convergencia("Execução de tarefa autorizada")

if __name__ == "__main__":
    asyncio.run(main())
