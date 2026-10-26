import hashlib
from pathlib import Path

import pytest

from osint_toolkit.evidence import store_evidence


@pytest.mark.parametrize("kind", ["../escape", "path/inner", r"path\\inner", "", ".", ".."])
def test_evidence_kind_rejected_before_writer_touches_filesystem(tmp_path: Path, kind: str):
    root = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="safe filename token"):
        store_evidence(b"payload", kind, root=root)
    assert not root.exists()


@pytest.mark.parametrize("raw", ["payload", bytearray(b"payload"), None, 123])
def test_non_bytes_payload_is_rejected_before_filesystem_changes(tmp_path: Path, raw):
    root = tmp_path / "must-not-exist"
    with pytest.raises(TypeError, match="raw must be bytes"):
        store_evidence(raw, "headers", root=root)
    assert not root.exists()


def test_symbolic_link_evidence_root_is_rejected(tmp_path: Path):
    target = tmp_path / "real-root"
    target.mkdir()
    root_link = tmp_path / "root-link"
    root_link.symlink_to(target, target_is_directory=True)
    with pytest.raises(RuntimeError, match="root must not be a symbolic link"):
        store_evidence(b"payload", "headers", root=root_link)
    assert list(target.iterdir()) == []


def test_existing_blob_is_verified_before_reuse(tmp_path: Path):
    original = b"original"
    result = store_evidence(original, "headers", root=tmp_path)
    path = Path(result["path"])
    assert result["hash"] == hashlib.sha256(original).hexdigest()
    path.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="full SHA-256"):
        store_evidence(original, "headers", root=tmp_path)


def test_non_file_destination_is_rejected(tmp_path: Path):
    raw = b"synthetic evidence"
    digest = hashlib.sha256(raw).hexdigest()
    destination = tmp_path / f"headers_{digest[:12]}.bin"
    destination.mkdir()
    with pytest.raises(RuntimeError, match="not a regular file"):
        store_evidence(raw, "headers", root=tmp_path)
    assert destination.is_dir()


def test_symlink_destination_is_rejected_without_writing_target(tmp_path: Path):
    root = tmp_path / "evidence"
    root.mkdir()
    raw = b"synthetic evidence"
    digest = hashlib.sha256(raw).hexdigest()
    target = tmp_path / "outside-target"
    link = root / f"headers_{digest[:12]}.bin"
    link.symlink_to(target)
    with pytest.raises(RuntimeError, match="symbolic link"):
        store_evidence(raw, "headers", root=root)
    assert not target.exists()


def test_normal_content_is_stored_and_hash_is_idempotent(tmp_path: Path):
    raw = b"synthetic evidence"
    first = store_evidence(raw, "headers", root=tmp_path)
    second = store_evidence(raw, "headers", root=tmp_path)
    assert first == second
    assert Path(first["path"]).read_bytes() == raw
    assert first["hash"] == hashlib.sha256(raw).hexdigest()
