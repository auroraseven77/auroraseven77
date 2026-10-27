"""Host-side validation tests for the bounded Termux worker."""

import json
import unittest

from aurora_termux_worker import (
    MAX_TASKS_PER_POLL,
    SUITES,
    WorkerError,
    sanitize_log,
    suite_command,
    validate_queue,
)


def valid_task(task_id="motor-optimizer-pr52"):
    return {
        "task_id": task_id,
        "pr": 52,
        "sha": "b2b0fefa807f238dcefa4659ef4aa7d16cbf8d9d",
        "suite": "motor_optimizer",
        "timeout_seconds": 900,
    }


def queue_bytes(tasks):
    return json.dumps({"schema_version": 1, "tasks": tasks}).encode("utf-8")


class QueueValidationTests(unittest.TestCase):
    def test_empty_queue_is_valid(self):
        self.assertEqual(validate_queue(queue_bytes([])), [])

    def test_valid_task_is_normalized(self):
        task = valid_task()
        task["sha"] = task["sha"].upper()
        result = validate_queue(queue_bytes([task]))
        self.assertEqual(result[0]["sha"], task["sha"].lower())
        self.assertEqual(result[0]["suite"], "motor_optimizer")

    def test_unknown_fields_are_rejected(self):
        task = valid_task()
        task["command"] = "echo unsafe"
        with self.assertRaisesRegex(WorkerError, "invalid field set"):
            validate_queue(queue_bytes([task]))

    def test_shell_command_cannot_be_smuggled_as_suite(self):
        task = valid_task()
        task["suite"] = "motor_optimizer && touch /tmp/pwned"
        with self.assertRaisesRegex(WorkerError, "non-allowlisted suite"):
            validate_queue(queue_bytes([task]))

    def test_invalid_commit_sha_is_rejected(self):
        task = valid_task()
        task["sha"] = "main"
        with self.assertRaisesRegex(WorkerError, "full 40-character commit SHA"):
            validate_queue(queue_bytes([task]))

    def test_duplicate_task_id_is_rejected(self):
        task = valid_task()
        with self.assertRaisesRegex(WorkerError, "duplicate task_id"):
            validate_queue(queue_bytes([task, task]))

    def test_boolean_pr_is_rejected(self):
        task = valid_task()
        task["pr"] = True
        with self.assertRaisesRegex(WorkerError, "invalid PR number"):
            validate_queue(queue_bytes([task]))

    def test_timeout_bounds_are_enforced(self):
        for timeout in (29, 1801, True, 1.5):
            task = valid_task()
            task["timeout_seconds"] = timeout
            with self.subTest(timeout=timeout):
                with self.assertRaisesRegex(WorkerError, "timeout_seconds"):
                    validate_queue(queue_bytes([task]))

    def test_task_count_is_bounded(self):
        tasks = [
            valid_task(f"task-{index}")
            for index in range(MAX_TASKS_PER_POLL + 1)
        ]
        with self.assertRaisesRegex(WorkerError, "at most"):
            validate_queue(queue_bytes(tasks))

    def test_queue_size_is_bounded(self):
        with self.assertRaisesRegex(WorkerError, "maximum byte size"):
            validate_queue(b"x" * (32 * 1024 + 1))

    def test_invalid_json_and_schema_are_rejected(self):
        with self.assertRaisesRegex(WorkerError, "valid UTF-8 JSON"):
            validate_queue(b"\xff")
        with self.assertRaisesRegex(WorkerError, "only schema_version and tasks"):
            validate_queue(b'{"schema_version":1,"tasks":[],"exec":"no"}')
        with self.assertRaisesRegex(WorkerError, "unsupported queue schema_version"):
            validate_queue(b'{"schema_version":2,"tasks":[]}')

    def test_task_id_path_traversal_is_rejected(self):
        task = valid_task("../escape")
        with self.assertRaisesRegex(WorkerError, "invalid task_id"):
            validate_queue(queue_bytes([task]))


class ExecutionBoundaryTests(unittest.TestCase):
    def test_every_suite_is_a_fixed_argument_vector(self):
        for suite, arguments in SUITES.items():
            with self.subTest(suite=suite):
                self.assertIsInstance(arguments, tuple)
                self.assertTrue(arguments)
                self.assertNotIn("shell", arguments)
                self.assertFalse(any(";" in arg for arg in arguments))

    def test_suite_command_requires_absolute_python_executable(self):
        with self.assertRaisesRegex(WorkerError, "absolute path"):
            suite_command("motor_optimizer", "python")
        command = suite_command("motor_optimizer", "/usr/bin/python3")
        self.assertEqual(command[0], "/usr/bin/python3")
        self.assertEqual(command[1:3], ["-m", "pytest"])

    def test_unknown_suite_cannot_build_command(self):
        with self.assertRaisesRegex(WorkerError, "non-allowlisted suite"):
            suite_command("rm_everything", "/usr/bin/python3")

    def test_log_tail_is_bounded_and_secrets_redacted(self):
        log = (
            "line\n" * 1000
            + "token=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n"
        ).encode()
        sanitized = sanitize_log(log)
        self.assertLessEqual(len(sanitized.encode()), 8192)
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz1234567890", sanitized)
        self.assertIn("[REDACTED]", sanitized)


if __name__ == "__main__":
    unittest.main(verbosity=2)
