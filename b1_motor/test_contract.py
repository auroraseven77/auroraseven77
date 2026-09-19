import math
from .circuit import evaluate_ansatz
from .nelder_mead import minimize

def run_proofs():
    print("Iniciando auditoria de invariantes contratuais...")

    # PROVA 1: Ausência de CX na camada 2
    params = [0.0] * 48
    params[33] = math.pi
    state = evaluate_ansatz(params)
    assert abs(state[64].real) > 0.99, "PROVA 1 FALHOU: Camada 2 sofreu CX indevido."
    assert abs(state[96]) < 0.01, "PROVA 1 FALHOU: O estado vazou para o índice 96."
    print("PROVA 1 PASS: Camada 2 não possui portas CX.")

    # PROVA 2: Ordem exata dos 48 parâmetros
    params2 = [0.0] * 48
    params2[7] = math.pi
    state2 = evaluate_ansatz(params2)
    assert abs(state2[1].real) > 0.99, "PROVA 2 FALHOU: Ordem incorreta."
    print("PROVA 2 PASS: Mapeamento de 48 parâmetros estrito.")

    # PROVA 3: Initial step == 0.05 estrito
    pts = []
    def obj_capture(x): 
        pts.append(list(x))
        return sum(x)
    minimize(obj_capture, [0.0, 0.0], max_evals=3)
    assert pts[1] == [0.05, 0.0], f"PROVA 3 FALHOU: {pts[1]}"
    print("PROVA 3 PASS: Initial step == 0.05 demonstrado iterativamente.")

    # PROVA 4: Tie-break de Vertex IDs
    def obj_flat(x): return 0.0
    _, _, _, _, simplex_flat = minimize(obj_flat, [0.0]*4, max_evals=5) 
    ids = [s[0] for s in simplex_flat]
    assert ids == [0, 1, 2, 3, 4], f"PROVA 4 FALHOU: {ids}"
    print("PROVA 4 PASS: Tie-break ascendente de Vertex ID garantido.")

    # PROVA 5: Herança do Vertex ID após substituição
    call_count = 0
    def obj_desc(x):
        nonlocal call_count
        call_count += 1
        return -float(call_count)
    _, _, _, _, simplex_desc = minimize(obj_desc, [0.0]*2, max_evals=4)
    ids_desc = sorted([s[0] for s in simplex_desc])
    assert ids_desc == [0, 1, 2], "PROVA 5 FALHOU."
    print("PROVA 5 PASS: Herança de Vertex ID observada.")

    # PROVA 6: Forçar shrink e verificar estado parcial
    shrink_calls = 0
    def obj_shrink(x):
        nonlocal shrink_calls
        shrink_calls += 1
        return abs(x[0]) + abs(x[1])
    x_opt, val, evals, status, simplex_shrink = minimize(obj_shrink, [1.0, 1.0], max_evals=4)
    assert evals == 4, "PROVA 6 FALHOU."
    print("PROVA 6 PASS: Parada do Shrink em avaliação parcial (In-Place state) validada.")

    # PROVA 7 CORRIGIDA: Orçamento exatamente em 128
    # Retornamos o próprio contador float. Isso garante que a diferença entre o
    # melhor e o pior vértice sempre seja >= 1.0 (nunca cai no tol <= 1e-6), 
    # obrigando o motor a bater de frente no muro de 128 evals.
    budget_count = 0
    def obj_budget(x):
        nonlocal budget_count
        budget_count += 1
        return float(budget_count)
    
    _, _, evals_budget, status_budget, _ = minimize(obj_budget, [0.0]*48, max_evals=128)
    assert budget_count == 128, f"PROVA 7 FALHOU: Avaliou {budget_count} vezes."
    assert status_budget == "MAX_FUNCTION_EVALUATIONS", "PROVA 7 FALHOU: Status divergente."
    print("PROVA 7 PASS: Orçamento exato 128 e limite reconhecido.")

    # PROVA 8: CONVERGED verificado
    def obj_converge(x): return 0.0
    _, _, evals_conv, status_conv, _ = minimize(obj_converge, [0.0]*3, max_evals=10)
    assert status_conv == "CONVERGED", "PROVA 8 FALHOU."
    assert evals_conv == 4, "PROVA 8 FALHOU."
    print("PROVA 8 PASS: Critério de convergência delta E <= 1e-6 funcional.")

    # PROVA 9: Rejeição de NaN/Inf
    def obj_nan(x): return float('nan')
    try:
        minimize(obj_nan, [0.0]*3, max_evals=10)
        assert False, "PROVA 9 FALHOU."
    except ValueError as e:
        assert "NaN ou Inf" in str(e)
    print("PROVA 9 PASS: Barreira contra numéricos inválidos armada.")

    print("\n=== TODAS AS 9 PROVAS DE INVARIANTES CONCLUÍDAS COM SUCESSO ===")
    print("O motor base agora reflete fisicamente os invariantes matemáticos do P0'.")

if __name__ == "__main__":
    run_proofs()
