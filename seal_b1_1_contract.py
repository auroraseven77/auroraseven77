import yaml
import json
import hashlib
import sys

P0_PRIME_YAML = """
schema_version: "B1.1-Execution-Instance"
manifest_id: "PSI-B1.1-N8"
reference_theoretical_manifest: "84410bac94daa5739144f649a4a886c1244729765c9d146385cb3bd0099f6124"

execution_instance:
  qubit_count: 8
  parameter_count: 48
  physical_qpu_claim: false

vqe_specification:
  ansatz:
    family: "hardware_efficient_linear_entanglement"
    depth: 2
    rotation_gates: ["RY", "RZ"]
    entangler: "CX"

  parameter_order:
    qubit_order: "0_to_N_minus_1"
    layer_order: "ascending"
    rotation_order: ["RY", "RZ"]

  cost_function:
    type: "1D_transverse_field_ising"
    boundary_condition: "open"
    coupling_J: 1.0
    transverse_field_h: 1.0

optimizer:
  algorithm: "Nelder-Mead_Pure_Python"
  max_function_evaluations: 128
  evaluation_budget_includes_initial_simplex: true
  energy_tolerance: 1.0e-6
  stochastic: false

  implementation:
    language: "Python"
    external_optimizer_dependency: false
    external_numeric_optimizer: false

  hyperparameters:
    reflection_alpha: 1.0
    expansion_gamma: 2.0
    contraction_rho: 0.5
    shrink_sigma: 0.5

  simplex_initialization:
    method: "basis_vector_offset"
    offset_delta: 0.05
    vertex_count: 49
    base_vertex_included: true
    coordinate_indexing: "0_to_47"

  operational_rules:
    vertex_identity:
      initial_ids: "0_to_48"
      replacement_policy: "replacement_point_inherits_replaced_vertex_id"
      tie_break: "ascending_vertex_id"

    centroid_computation:
      excluded_vertex: "worst"
      summation_order: "ascending_vertex_id"
      accumulation: "left_to_right_binary64"
      division: "after_complete_vector_sum"

    shrink_flow:
      evaluation_order: "ascending_vertex_id"
      partial_shrink_allowed: true
      partial_shrink_termination: "MAX_FUNCTION_EVALUATIONS"

  convergence:
    criterion: "simplex_energy_spread"
    condition: "max_energy_minus_min_energy <= tolerance"

  termination_statuses:
    - "CONVERGED"
    - "MAX_FUNCTION_EVALUATIONS"

initialization:
  method: "explicit_parameter_vector"
  parameter_count: 48
  parameters: [
    0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, -0.8,
    0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, -0.8,
    0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, -0.8,
    0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, -0.8,
    0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, -0.8,
    0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, -0.8
  ]

execution:
  backend:
    identifier: "pure-python-statevector-b1"
    external_quantum_sdk: false
  shots: null

numeric_contract:
  scalar_type: "IEEE-754 binary64"
  complex_type: "complex128"
  nan_policy: "reject"
  infinity_policy: "reject"

reproducibility:
  scope: "deterministic_under_specified_execution_environment"
  cross_architecture_bitwise_guarantee: false
"""

def seal_b1_1_contract():
    try:
        manifest = yaml.safe_load(P0_PRIME_YAML)
    except Exception as e:
        print(f"Erro ao ler YAML: {e}")
        sys.exit(1)

    with open("MANIFEST_B1.1.yaml", "w") as f:
        f.write(P0_PRIME_YAML.strip() + "\n")

    p1_prime_canonical = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    p2_prime_hash = hashlib.sha256(
        p1_prime_canonical.encode("utf-8")
    ).hexdigest()

    print("=== P0': MANIFESTO B1.1 CANÔNICO SALVO ===")
    print("Arquivo: MANIFEST_B1.1.yaml")
    print()
    print(
        "Referência teórica ancorada: "
        f"{manifest['reference_theoretical_manifest']}"
    )
    print()
    print("=== P2': EXPERIMENT_HASH (H_pre') ===")
    print(p2_prime_hash)

    with open("B1.1_EXPERIMENT_HASH.seal", "w") as f:
        f.write(p2_prime_hash + "\n")

if __name__ == "__main__":
    seal_b1_1_contract()
