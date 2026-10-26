from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "scripts" / "aurora_mcp_source_inventory.sh"


def _json_output(stdout: str) -> dict:
    match = re.search(r"(?m)^\{\n", stdout)
    assert match is not None, stdout
    return json.loads(stdout[match.start():])


def _file_entry(document: dict, root_name: str, filename: str) -> dict:
    root = next(item for item in document["roots"] if item["root"] == root_name)
    return next(item for item in root["files"] if item["name"] == filename)


def _run(home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        ["/bin/bash", str(SCRIPT), *args],
        cwd=REPOSITORY,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )


def test_hashes_selected_source_but_never_discloses_contents_or_script_commands(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    root = home / "mcp-aurora-server"
    root.mkdir()
    source = b"SOURCE_SENTINEL_do_not_print\nconsole.log('demo');\n"
    (root / "index.js").write_bytes(source)
    (root / "bridge.cjs").write_text(
        "const child = require('child_process');\n"
        "const server = http.createServer(app);\n"
        "server.listen(8787);\n"
        "fs.writeFileSync('demo', 'payload');\n"
        "const token = process.env.AURORA_TOKEN;\n"
        "const value = eval('1 + 1');\n"
        "const response = await fetch('https://example.invalid');\n"
        "registerTool('read');\n"
        "authorize('read');\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps({
            "name": "safe-demo",
            "version": "1.2.3",
            "main": "index.js",
            "scripts": {"start": "COMMAND_SENTINEL_should_never_print"},
        }),
        encoding="utf-8",
    )
    (root / "package-lock.json").write_text("LOCK_SENTINEL", encoding="utf-8")
    (root / "audit-denials.jsonl").write_text("LEDGER_SENTINEL", encoding="utf-8")
    (root / "aurora.log").write_text("LOG_SENTINEL", encoding="utf-8")
    (root / ".env").write_text("ENV_SENTINEL=never_print", encoding="utf-8")
    (root / "index.js.bak").write_text("BACKUP_SENTINEL", encoding="utf-8")
    (root / "private-helper.js").write_text("PRIVATE_SENTINEL", encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    (nested / "nested.js").write_text("NESTED_SENTINEL", encoding="utf-8")

    before = {p.relative_to(home).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    result = _run(home)
    assert result.returncode == 0, result.stderr
    document = _json_output(result.stdout)
    source_entry = _file_entry(document, "~/mcp-aurora-server", "index.js")
    assert source_entry["sha256"] == hashlib.sha256(source).hexdigest()
    assert source_entry["state"] == "HASHED_SOURCE_ONLY"
    triage_entry = _file_entry(document, "~/mcp-aurora-server", "bridge.cjs")
    assert triage_entry["state"] == "HASHED_SOURCE_ONLY"
    marker_lines = triage_entry["static_marker_lines"]
    assert marker_lines["process_execution"] >= 1
    assert marker_lines["network_client"] >= 1
    assert marker_lines["network_listener"] >= 1
    assert marker_lines["filesystem_mutation"] >= 1
    assert marker_lines["environment_or_credential_access"] >= 1
    assert marker_lines["dynamic_code"] >= 1
    assert marker_lines["mcp_tool_or_protocol"] >= 1
    assert marker_lines["authorization_or_approval"] >= 1
    marker_numbers = triage_entry["static_marker_line_numbers"]
    assert marker_numbers["process_execution"] == [1]
    assert marker_numbers["network_listener"] == [2, 3]
    assert marker_numbers["filesystem_mutation"] == [4]
    assert marker_numbers["environment_or_credential_access"] == [5]
    assert marker_numbers["dynamic_code"] == [6]
    assert marker_numbers["network_client"] == [7]
    assert marker_numbers["mcp_tool_or_protocol"] == [8]
    assert marker_numbers["authorization_or_approval"] == [9]
    assert triage_entry["manual_review_suggested"] is True
    assert triage_entry["manual_review_marker_categories"] == [
        "dynamic_code",
        "environment_or_credential_access",
        "filesystem_mutation",
        "network_listener",
        "process_execution",
    ]
    assert triage_entry["static_marker_lines_truncated"] == {}
    package_entry = _file_entry(document, "~/mcp-aurora-server", "package.json")
    assert package_entry["state"] == "HASHED_MANIFEST_ONLY"
    root_entry = next(x for x in document["roots"] if x["root"] == "~/mcp-aurora-server")
    assert root_entry["package_metadata"]["name"] == "safe-demo"
    assert root_entry["package_metadata"]["script_names"] == ["start"]
    for sentinel in (
        "COMMAND_SENTINEL_should_never_print",
        "SOURCE_SENTINEL",
        "require('child_process')",
        "AURORA_TOKEN",
        "LOCK_SENTINEL",
        "LEDGER_SENTINEL",
        "LOG_SENTINEL",
        "ENV_SENTINEL",
        "BACKUP_SENTINEL",
        "PRIVATE_SENTINEL",
        "NESTED_SENTINEL",
    ):
        assert sentinel not in result.stdout
    after = {p.relative_to(home).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert after == before
    assert document["side_effects"].startswith("read-only local filesystem inspection")
    assert "package.json" in document["side_effects"]
    assert "never emits or executes package script command values" in document["side_effects"]



def test_summary_mode_reports_only_review_candidates_and_preserves_files(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    root = home / "mcp-aurora-server"
    root.mkdir()
    source = (
        "const child = require('child_process');\\n"
        "const server = http.createServer(app);\\n"
        "server.listen(8787);\\n"
        "fs.writeFileSync('demo', 'payload');\\n"
        "const value = eval('TRIAGE_SECRET_SENTINEL');\\n"
    )
    (root / "bridge.cjs").write_text(source, encoding="utf-8")
    (root / "quiet.js").write_text("const x = 1;\\n", encoding="utf-8")
    (root / "package.json").write_text(
        json.dumps({"name": "summary-demo", "scripts": {"start": "PRIVATE_COMMAND_SENTINEL"}}),
        encoding="utf-8",
    )
    before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}

    result = _run(home, "--summary")
    assert result.returncode == 0, result.stderr
    document = _json_output(result.stdout)
    assert document["view"] == "SUMMARY"
    summary = next(item for item in document["roots"] if item["root"] == "~/mcp-aurora-server")
    assert summary["source_files_hashed"] == 2
    assert summary["manifests_hashed"] == 1
    assert summary["manual_review_candidate_count"] == 1
    assert "files" not in summary
    candidate = summary["manual_review_candidates"][0]
    assert candidate["name"] == "bridge.cjs"
    assert candidate["static_marker_line_numbers"]["network_listener"] == [2, 3]
    assert candidate["static_marker_line_numbers"]["filesystem_mutation"] == [4]
    assert candidate["static_marker_line_numbers"]["dynamic_code"] == [5]
    assert summary["marker_file_counts"]["process_execution"] == 1
    assert "quiet.js" not in result.stdout
    assert "TRIAGE_SECRET_SENTINEL" not in result.stdout
    assert "PRIVATE_COMMAND_SENTINEL" not in result.stdout
    after = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    assert after == before

def test_static_marker_line_numbers_are_bounded(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    root = home / "mcp-aurora"
    root.mkdir()
    (root / "eval-helper.js").write_text(
        "".join("eval('candidate');\n" for _ in range(15)),
        encoding="utf-8",
    )

    result = _run(home)
    assert result.returncode == 0, result.stderr
    document = _json_output(result.stdout)
    entry = _file_entry(document, "~/mcp-aurora", "eval-helper.js")
    assert entry["static_marker_lines"]["dynamic_code"] == 15
    assert entry["static_marker_line_numbers"]["dynamic_code"] == list(range(1, 9))
    assert entry["static_marker_lines_truncated"]["dynamic_code"] is True
    assert entry["manual_review_suggested"] is True


def test_absent_roots_and_symlink_roots_are_reported_without_following_them(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    result = _run(home)
    assert result.returncode == 0, result.stderr
    document = _json_output(result.stdout)
    assert all(root["state"] == "ABSENT" for root in document["roots"])

    target = tmp_path / "real-source"
    target.mkdir()
    (target / "leak.js").write_text("SYMLINK_TARGET_SENTINEL", encoding="utf-8")
    (home / "mcp-aurora").symlink_to(target, target_is_directory=True)
    result = _run(home)
    assert result.returncode == 0, result.stderr
    document = _json_output(result.stdout)
    root = next(item for item in document["roots"] if item["root"] == "~/mcp-aurora")
    assert root["state"] == "SYMLINK_ROOT_SKIPPED"
    assert "SYMLINK_TARGET_SENTINEL" not in result.stdout


def test_source_symlink_is_not_followed(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    root = home / "mcp-aurora"
    root.mkdir()
    target = home / "target.js"
    target.write_text("SYMLINK_SOURCE_SENTINEL", encoding="utf-8")
    (root / "linked.js").symlink_to(target)
    result = _run(home)
    assert result.returncode == 0, result.stderr
    document = _json_output(result.stdout)
    assert _file_entry(document, "~/mcp-aurora", "linked.js")["state"] == "SYMLINK_SKIPPED"
    assert "SYMLINK_SOURCE_SENTINEL" not in result.stdout
