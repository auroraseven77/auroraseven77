"""Input-contract and budget regressions for the B1 motor optimizer."""

import math

import pytest

from b1_motor.nelder_mead import minimize


@pytest.mark.parametrize("budget", [0, -1])
def test_nonpositive_evaluation_budget_is_rejected_before_objective(budget):
    calls = []

    def objective(point):
        calls.append(point)
        return sum(point)

    with pytest.raises(ValueError, match="max_evals must be >= 1"):
        minimize(objective, [0.0], max_evals=budget)

    assert calls == []


@pytest.mark.parametrize("budget", [1.5, True, "10"])
def test_noninteger_evaluation_budget_is_rejected(budget):
    with pytest.raises(TypeError, match="max_evals must be a positive integer"):
        minimize(lambda point: sum(point), [0.0], max_evals=budget)


@pytest.mark.parametrize("step", [0.0, -0.1, math.inf, -math.inf, math.nan])
def test_invalid_initial_step_is_rejected(step):
    with pytest.raises(ValueError, match="initial_step must be finite and > 0"):
        minimize(lambda point: sum(point), [0.0], initial_step=step)


def test_non_numeric_initial_step_is_rejected():
    with pytest.raises(TypeError, match="initial_step must be a real number"):
        minimize(lambda point: sum(point), [0.0], initial_step="0.05")


@pytest.mark.parametrize("tol", [-1.0, math.inf, -math.inf, math.nan])
def test_invalid_tolerance_is_rejected(tol):
    with pytest.raises(ValueError, match="tol must be finite and >= 0"):
        minimize(lambda point: sum(point), [0.0], tol=tol)


def test_empty_starting_point_is_rejected():
    with pytest.raises(ValueError, match="x0 must contain at least one parameter"):
        minimize(lambda point: sum(point), [])


@pytest.mark.parametrize("point", [[math.nan], [math.inf], [-math.inf]])
def test_nonfinite_starting_point_is_rejected(point):
    with pytest.raises(ValueError, match="x0 must contain only finite values"):
        minimize(lambda values: sum(values), point)


def test_non_sequence_starting_point_is_rejected():
    with pytest.raises(TypeError, match="x0 must be a one-dimensional sequence"):
        minimize(lambda point: sum(point), None)


def test_non_callable_objective_is_rejected():
    with pytest.raises(TypeError, match="objective_function must be callable"):
        minimize(None, [0.0])


def test_budget_smaller_than_initial_simplex_is_respected():
    calls = 0

    def objective(point):
        nonlocal calls
        calls += 1
        return sum(value * value for value in point)

    _, _, evals, status, simplex = minimize(
        objective,
        [0.0, 0.0, 0.0],
        max_evals=2,
    )

    assert calls == evals == 2
    assert status in {"CONVERGED", "MAX_FUNCTION_EVALUATIONS"}
    assert len(simplex) == 2
