import math

class MaxEvaluationsReached(Exception):
    pass

def minimize(objective_function, x0, initial_step=0.05, max_evals=128, tol=1e-6):
    N = len(x0)
    alpha, gamma, rho, sigma = 1.0, 2.0, 0.5, 0.5
    evals = 0
    
    def f(x):
        nonlocal evals
        if evals >= max_evals:
            raise MaxEvaluationsReached()
        val = objective_function(x)
        if math.isnan(val) or math.isinf(val):
            raise ValueError("Falha Contratual: Função objetivo retornou NaN ou Inf")
        evals += 1
        return val

    simplex = []
    try:
        val0 = f(x0)
        simplex.append((0, x0, val0))
        
        for i in range(N):
            xi = list(x0)
            xi[i] += initial_step
            vali = f(xi)
            simplex.append((i + 1, xi, vali))
            
        while evals < max_evals:
            simplex.sort(key=lambda item: (item[2], item[0]))
            
            # Critério de convergência estrito (B1.1)
            if simplex[-1][2] - simplex[0][2] <= tol:
                return simplex[0][1], simplex[0][2], evals, "CONVERGED", simplex
                
            centroid = [0.0] * N
            for i in range(N):
                for j in range(N):
                    centroid[j] += simplex[i][1][j]
            centroid = [c / N for c in centroid]
            
            worst_id, worst_x, worst_val = simplex[-1]
            second_worst_val = simplex[-2][2]
            best_val = simplex[0][2]
            
            # Reflexão
            xr = [centroid[i] + alpha * (centroid[i] - worst_x[i]) for i in range(N)]
            r_val = f(xr)
            
            if best_val <= r_val < second_worst_val:
                simplex[-1] = (worst_id, xr, r_val)
                continue
                
            # Expansão
            if r_val < best_val:
                xe = [centroid[i] + gamma * (xr[i] - centroid[i]) for i in range(N)]
                e_val = f(xe)
                if e_val < r_val:
                    simplex[-1] = (worst_id, xe, e_val)
                else:
                    simplex[-1] = (worst_id, xr, r_val)
                continue
                
            # Contração
            if r_val >= second_worst_val:
                if r_val < worst_val:
                    xc = [centroid[i] + rho * (xr[i] - centroid[i]) for i in range(N)]
                    c_val = f(xc)
                    if c_val <= r_val:
                        simplex[-1] = (worst_id, xc, c_val)
                        continue
                else:
                    xc = [centroid[i] - rho * (worst_x[i] - centroid[i]) for i in range(N)]
                    c_val = f(xc)
                    if c_val < worst_val:
                        simplex[-1] = (worst_id, xc, c_val)
                        continue
                        
                # Encolhimento (Shrink) in-place para suportar orçamento parcial
                best_id, best_x, best_val = simplex[0]
                for i in range(1, len(simplex)):
                    xi_id, xi_x, xi_val = simplex[i]
                    x_shrunk = [best_x[j] + sigma * (xi_x[j] - best_x[j]) for j in range(N)]
                    val_shrunk = f(x_shrunk)
                    simplex[i] = (xi_id, x_shrunk, val_shrunk)

    except MaxEvaluationsReached:
        pass
        
    simplex.sort(key=lambda item: (item[2], item[0]))
    status = "CONVERGED" if (simplex[-1][2] - simplex[0][2] <= tol) else "MAX_FUNCTION_EVALUATIONS"
    
    # Retornamos o simplex interno como 5º argumento para os testes de auditoria
    return simplex[0][1], simplex[0][2], evals, status, simplex
