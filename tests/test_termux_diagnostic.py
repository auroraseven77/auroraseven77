from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
DIAGNOSTIC = REPOSITORY / "scripts" / "aurora_mcp_termux_diagnostic.sh"


def _fake_command(directory: Path, name: str, body: str) -> None:
    path = directory / name
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(0o755)


def _run_diagnostic(tmp_path: Path, *, ss_body: str, ps_body: str) -> subprocess.CompletedProcess[str]:
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    _fake_command(fakebin, "ss", ss_body)
    _fake_command(fakebin, "ps", ps_body)
    # Replace only the final HTTP probe so this test never needs a real service.
    _fake_command(
        fakebin,
        "python3",
        'cat >/dev/null\nprintf \'{"state":"NOT_CONNECTED","stdio_mcp":"NOT_TESTED_BY_HTTP_PROBE"}\\n\'\nexit 1',
    )

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    Path(env["HOME"]).mkdir()
    env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        ["/bin/bash", str(DIAGNOSTIC)],
        cwd=REPOSITORY,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )


def test_permission_denied_listener_and_header_only_process_output_are_inconclusive(tmp_path: Path):
    result = _run_diagnostic(
        tmp_path,
        ss_body='printf "Cannot open netlink socket: Permission denied\\nState Recv-Q Send-Q Local Address:Port Peer Address:Port\\n"\nexit 0',
        ps_body='printf "PID TTY TIME CMD\\n"\nexit 0',
    )

    assert "listener_state=INCONCLUSIVE" in result.stdout
    assert "process_state=INCONCLUSIVE" in result.stdout
    assert "visible_process_rows=0 candidate_name_matches=0" in result.stdout
    assert "NOT_CONNECTED" in result.stdout
    assert "NO SERVICE STARTED" in result.stdout
    assert "NO PACKAGE INSTALLED" in result.stdout


def test_empty_listener_table_and_unmatched_process_names_are_not_overclaimed(tmp_path: Path):
    result = _run_diagnostic(
        tmp_path,
        ss_body='printf "State Recv-Q Send-Q Local Address:Port Peer Address:Port\\n"\nexit 0',
        ps_body='printf "PID TTY TIME CMD\\n123 pts/0 00:00:00 shell\\n"\nexit 0',
    )

    assert "listener_state=NO_ROWS_REPORTED" in result.stdout
    assert "process_state=NO_RELEVANT_NAME_MATCH" in result.stdout
    assert "visible_process_rows=1 candidate_name_matches=0" in result.stdout
    assert "not proof of absence" in result.stdout
    assert "NOT_CONNECTED" in result.stdout
