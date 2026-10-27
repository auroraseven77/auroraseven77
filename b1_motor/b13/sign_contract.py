"""B1.3 explicit TFIM comparison convention."""

from b1_motor.hamiltonian_b12 import TFIMSignConvention

B13_SIGN_CONVENTION = TFIMSignConvention(
    interaction_sign=-1,
    field_sign=-1,
)

__all__ = ["B13_SIGN_CONVENTION"]
