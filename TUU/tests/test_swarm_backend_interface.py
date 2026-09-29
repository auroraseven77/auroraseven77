import pytest
from pydantic import ValidationError

from TUU.swarm_backend_interface import (
    CodecType,
    ContractionInput,
    OperationType,
    PayloadPointer,
    StateVersion,
    TensorContractionRequest,
    TensorMetadata,
)


@pytest.fixture
def valid_pointer():
    return PayloadPointer(
        payload_hash="a" * 64,
        byte_length=1024,
        codec=CodecType.SAFETENSORS,
    )


@pytest.fixture
def valid_metadata():
    return TensorMetadata(
        shape=(2, 4, 4),
        dtype="complex128",
        bond_dimension=4,
    )


@pytest.fixture
def valid_request(valid_pointer, valid_metadata):
    return TensorContractionRequest(
        task_id="task_001",
        state_version=StateVersion(
            version_id=1,
            qubits_affected=(0, 1),
        ),
        operation_type=OperationType.GATE_CONTRACTION_SVD,
        chi_max=256,
        inputs=(
            ContractionInput(
                name="q0",
                pointer=valid_pointer,
                metadata=valid_metadata,
            ),
        ),
    )


def test_request_instantiation_and_validation(valid_request):
    assert valid_request.task_id == "task_001"
    assert valid_request.chi_max == 256
    assert valid_request.operation_type == OperationType.GATE_CONTRACTION_SVD
    assert len(valid_request.inputs) == 1


def test_deep_immutability(valid_request):
    with pytest.raises(ValidationError):
        valid_request.task_id = "hacked_task"

    with pytest.raises(ValidationError):
        valid_request.inputs[0].name = "hacked_name"

    with pytest.raises(TypeError):
        valid_request.inputs[0] = valid_request.inputs[0]


def test_nested_pointer_and_metadata_are_frozen(valid_request):
    with pytest.raises(ValidationError):
        valid_request.inputs[0].pointer.byte_length = 2048

    with pytest.raises(ValidationError):
        valid_request.inputs[0].metadata.dtype = "float64"

    with pytest.raises(ValidationError):
        valid_request.state_version.version_id = 2


def test_structural_validation_fails_on_invalid_data():
    with pytest.raises(ValidationError):
        PayloadPointer(
            payload_hash="abcd",
            byte_length=-500,
            codec=CodecType.SAFETENSORS,
        )

    with pytest.raises(ValidationError):
        TensorContractionRequest(
            task_id="task_002",
            state_version=StateVersion(
                version_id=1,
                qubits_affected=(0, 1),
            ),
            operation_type=OperationType.GATE_CONTRACTION_SVD,
            chi_max=-10,
            inputs=(),
        )


@pytest.mark.parametrize(
    "qubits",
    [
        (1, 1),
        (2, 0),
    ],
)
def test_state_version_rejects_noncanonical_qubit_order(qubits):
    with pytest.raises(ValidationError):
        StateVersion(version_id=1, qubits_affected=qubits)


def test_payload_hash_is_structurally_constrained():
    with pytest.raises(ValidationError):
        PayloadPointer(
            payload_hash="g" * 64,
            byte_length=1,
            codec=CodecType.RAW_BYTES,
        )

    with pytest.raises(ValidationError):
        PayloadPointer(
            payload_hash="a" * 63,
            byte_length=1,
            codec=CodecType.RAW_BYTES,
        )


def test_tensor_metadata_rejects_nonpositive_dimensions():
    with pytest.raises(ValidationError):
        TensorMetadata(
            shape=(2, 0, 4),
            dtype="complex128",
        )


def test_contract_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        PayloadPointer(
            payload_hash="a" * 64,
            byte_length=1,
            codec=CodecType.RAW_BYTES,
            unexpected="mutation",
        )


def test_floating_contract_values_must_be_finite():
    with pytest.raises(ValidationError):
        TensorContractionRequest(
            task_id="task_nan",
            state_version=StateVersion(
                version_id=1,
                qubits_affected=(0, 1),
            ),
            operation_type=OperationType.GATE_CONTRACTION_SVD,
            chi_max=1,
            truncation_threshold=float("nan"),
            inputs=(),
        )
