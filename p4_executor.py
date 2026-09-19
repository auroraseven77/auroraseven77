import json
import math
from b1_motor.circuit import evaluate_ansatz
from b1_motor.hamiltonian import measure_energy
from b1_motor.nelder_mead import minimize

def objective(params):
    # O circuito gera o estado quântico e o hamiltoniano mede a energia esperada
    state = evaluate_ansatz(params)
    energy = measure_energy(state)
    return energy

def run_p4():
    print("=== INICIALIZANDO ORQUESTRADOR P4 (VQE B1.1) ===")
    
    # Parâmetros iniciais zerados (48 dimensões)
    x0 = [0.0] * 48
    
    print("Executando otimização Nelder-Mead (Orçamento máximo: 128 avaliações)...")
    x_opt, val_opt, evals, status, _ = minimize(objective, x0, initial_step=0.05, max_evals=128, tol=1e-6)
    
    print(f"\n--- RESULTADOS DO EXPERIMENTO P4 ---")
    print(f"Status de Parada: {status}")
    print(f"Avaliações Realizadas: {evals}")
    print(f"Energia Ótimizada (Valor Mínimo): {val_opt:.12f}")
    
    # Validação do envelope contratual
    assert evals <= 128, "Violação de orçamento de avaliações!"
    
    # Gravando o selo de resultado do P4
    output_data = {
        "status": status,
        "evaluations": evals,
        "optimal_energy": val_opt,
        "parameters_shape": len(x_opt)
    }
    
    with open("B1.1_EXPERIMENT_RESULT.json", "w") as f:
        json.dump(output_data, f, indent=2)
        
    print("Selo P4 gravado com sucesso em B1.1_EXPERIMENT_RESULT.json")

if __name__ == "__main__":
    run_p4()
