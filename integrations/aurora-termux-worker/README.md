# Aurora Termux Bounded Test Worker

Status: **prototype in an isolated PR branch; not installed or executed on a device**.

## Purpose

This is the missing pull-based bridge between GitHub-hosted changes and the Termux environment. It is intentionally narrower than a remote shell:

1. A GitHub-side coordinator writes a task manifest to `automation/termux-task-queue`.
2. The Termux worker polls that branch over HTTPS using the existing local mirror.
3. Each task must name an open PR, its exact 40-character head commit, a built-in test suite, and a bounded timeout.
4. The worker verifies the current PR head matches the queued SHA before executing anything.
5. Tests run in a detached temporary Git worktree, sequentially, with a temporary HOME/TMPDIR and no GitHub token in the test process environment.
6. The worker publishes one JSON result to a unique branch under `automation/termux-results/`; it never pushes to `main` or to the source PR branch.
7. A coordinator can read the result branch and produce the final acceptance report.

## The queue is data, not a shell

The manifest path is fixed at `.aurora-termux-worker/queue.json` on the dedicated `automation/termux-task-queue` branch. The schema is:

```json
{
  "schema_version": 1,
  "tasks": [
    {
      "task_id": "motor-optimizer-pr52",
      "pr": 52,
      "sha": "b2b0fefa807f238dcefa4659ef4aa7d16cbf8d9d",
      "suite": "motor_optimizer",
      "timeout_seconds": 900
    }
  ]
}
```

The SHA above is an example of a previously observed PR head, not a promise that it remains current. A coordinator must populate the exact live PR head SHA before enqueueing a task. Queue tasks cannot contain command strings, paths, environment variables, or arbitrary test arguments.

Built-in suite identifiers are hard-coded in `aurora_termux_worker.py`: `motor_optimizer`, `mps_observables`, `motor_b12`, `tuu_invariants`, `phase1`, and `compile_core`. A queue containing any other suite is rejected. At most eight tasks are read per poll; each timeout is 30–1800 seconds. Tasks run sequentially to reduce pressure on low-memory Android devices.

## Result contract

Result JSON includes schema and worker versions, task/PR/commit identity, suite, start/finish times, duration, Python/platform versions, outcome, exit code, and bounded stdout/stderr tails. Common token patterns are redacted. Outcomes include `passed`, `failed`, `timeout`, `stale_commit`, and `runner_error`.

Result branch names are deterministic for the task ID and source SHA:
`automation/termux-results/<task-id>-<sha12>`.
The report path is
`integrations/aurora-termux-worker/reports/<task-id>--<sha12>.json`.
The branch is separate from `main`; the report is not merged automatically.

## Authentication model

Fetching public repository content requires no token. Publishing reports requires a fine-grained GitHub token restricted to this repository with **Contents: Read and write** and no administration, workflow, or other permissions. Store it in the configured token file with filesystem mode `0600`. The worker reads the token only after the test process exits and supplies it to the one Git push process via a process-local Git HTTP header. The token is not passed to the suite's environment or printed to stdout/stderr.

Because the repository is public, result reports are public. Do not put credentials, private paths, personal data, or sensitive test output in them. The report tail is bounded and common token shapes are redacted, but redaction is not a substitute for not producing sensitive output.

## Trust and safety limitations

This worker is **not a security sandbox**. Test code runs under the Termux user and can potentially read that user's files or access the network. The temporary HOME and stripped environment reduce accidental exposure; they do not create an OS security boundary. Only enqueue owner-controlled source commits and review any new suite before changing the allowlist. Do not execute untrusted contributor PR code on the phone.

The worker checks the exact PR head SHA to avoid running a stale task, but this alone does not prove that the PR is benign. A failed, timed-out, or stale test is reported as failure evidence, not silently retried as a pass. A timed-out suite is terminated as a process group so child processes do not intentionally outlive the test timeout.

## One-time activation, not performed by this PR

The isolated mirror currently syncs only `main`; this worker lives on its own branch until reviewed. To activate later, the owner must choose the reviewed deployment commit, configure a repository-scoped write token, initialize the queue branch, and schedule the separate Termux job. This PR does not install packages, start a service, modify the device, or change the existing mirror job.

After the PR is accepted and the six-hour mirror sync has pulled the worker into `main`, the one-time installer is `integrations/aurora-termux-worker/install_termux_worker_job.sh`. It checks the isolated mirror and dependencies, prompts for a token without echoing it only if no token file exists, writes the token as mode `0600`, installs the worker under `~/.local/lib`, and registers job `517704` on a 15-minute period. It does not run a task immediately and it does not install packages. The user must create the fine-grained token in GitHub settings; do not paste the token into a chat.

For Android reliability, a 15-minute periodic job is a target, subject to Android/Termux scheduling and battery/network constraints. Polls may be delayed by the operating system. The existing six-hour mirror-sync job remains separate and unchanged.

## Host-side acceptance tests

Run from this directory:

```sh
python -m py_compile aurora_termux_worker.py
python -m unittest -v test_aurora_termux_worker.py
```

These tests validate the queue schema, command allowlist, bounds, and log redaction. They do not claim that the worker has been installed or exercised on Android.
