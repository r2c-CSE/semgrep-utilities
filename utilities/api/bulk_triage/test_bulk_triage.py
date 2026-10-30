#!/usr/bin/env python3
"""Tests for bulk_triage.py. Run from this directory with:

    python3 -m unittest test_bulk_triage
"""

import argparse
import contextlib
import csv
import io
import os
import tempfile
import unittest
from unittest import mock

import bulk_triage


class FakeTriageApi:
    """Stands in for bulk_triage.bulk_triage.

    `siblings` maps a submitted issue ID to extra IDs the API reports as
    triaged alongside it (same fingerprint, other branches). IDs in
    `not_triaged` are never reported as triaged. IDs in `fail_on` raise.
    """

    def __init__(self, siblings=None, not_triaged=(), fail_on=()):
        self.siblings = siblings or {}
        self.not_triaged = set(not_triaged)
        self.fail_on = set(fail_on)
        self.payloads = []

    def __call__(self, session, deployment_slug, payload):
        self.payloads.append(payload)
        if self.fail_on & set(payload["issue_ids"]):
            raise RuntimeError("HTTP 500: boom")
        triaged = []
        for issue_id in payload["issue_ids"]:
            if issue_id not in self.not_triaged:
                triaged.append(issue_id)
            triaged.extend(self.siblings.get(issue_id, []))
        return {"num_triaged": len(triaged), "triaged_issues": triaged}

    @property
    def submitted(self):
        return [payload["issue_ids"] for payload in self.payloads]


class BulkTriageTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def path(self, name):
        return os.path.join(self.tmpdir.name, name)

    def write_csv(self, rows, header=("issue_id", "issue_type")):
        path = self.path("input.csv")
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        return path

    def read_csv(self, name):
        with open(self.path(name), newline="") as f:
            return [(row["issue_type"], int(row["issue_id"])) for row in csv.DictReader(f)]

    def run_main(self, args, api=None, token="test-token"):
        argv = [
            "bulk_triage.py",
            "--remaining-csv", self.path("remaining.csv"),
            "--not-triaged-csv", self.path("not_triaged.csv"),
            "--delay", "0",
            *args,
        ]
        env = {"SEMGREP_APP_TOKEN": token} if token else {}
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("sys.argv", argv), \
                mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(bulk_triage, "bulk_triage", api or FakeTriageApi()), \
                mock.patch.object(bulk_triage, "create_session", return_value=None), \
                contextlib.redirect_stdout(stdout), \
                contextlib.redirect_stderr(stderr):
            rc = bulk_triage.main()
        return rc, stdout.getvalue(), stderr.getvalue()


class ReadIssuesTest(BulkTriageTestCase):
    def test_groups_by_type_dedupes_and_keeps_order(self):
        path = self.write_csv([(3, ""), (1, "sca"), (2, ""), (3, ""), (1, "")])
        issues = bulk_triage.read_issues(path, "sast")
        self.assertEqual({k: list(v) for k, v in issues.items()}, {"sast": [3, 2, 1], "sca": [1]})

    def test_issue_id_only_csv_uses_default_type(self):
        path = self.write_csv([(5,), (6,)], header=("issue_id",))
        issues = bulk_triage.read_issues(path, "secrets")
        self.assertEqual({k: list(v) for k, v in issues.items()}, {"secrets": [5, 6]})

    def test_missing_issue_id_column(self):
        path = self.write_csv([(1,)], header=("id",))
        with self.assertRaisesRegex(ValueError, "issue_id"):
            bulk_triage.read_issues(path, "sast")

    def test_invalid_issue_id(self):
        path = self.write_csv([("abc", "")])
        with self.assertRaisesRegex(ValueError, "input.csv:2"):
            bulk_triage.read_issues(path, "sast")

    def test_invalid_issue_type(self):
        path = self.write_csv([(1, "dast")])
        with self.assertRaisesRegex(ValueError, "issue_type"):
            bulk_triage.read_issues(path, "sast")


class LimitArgTest(unittest.TestCase):
    def test_bounds(self):
        self.assertEqual(bulk_triage.limit_arg("1"), 1)
        self.assertEqual(bulk_triage.limit_arg("3000"), 3000)
        for bad in ("0", "3001", "-5"):
            with self.assertRaises(argparse.ArgumentTypeError):
                bulk_triage.limit_arg(bad)


class MainTest(BulkTriageTestCase):
    def test_batches_respect_limit_and_payload(self):
        path = self.write_csv([(i, "") for i in range(1, 6)])
        api = FakeTriageApi()
        rc, _, _ = self.run_main(
            ["--deployment-slug", "d", "--csv", path, "--state", "ignored",
             "--reason", "false_positive", "--note", "n", "--limit", "2"],
            api,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(api.submitted, [[1, 2], [3, 4], [5]])
        self.assertEqual(
            api.payloads[0],
            {
                "issue_type": "sast",
                "issue_ids": [1, 2],
                "limit": 2,
                "new_triage_state": "ignored",
                "new_triage_reason": "false_positive",
                "new_note": "n",
            },
        )

    def test_queued_siblings_are_not_resubmitted(self):
        # 1 drags in 4 (queued later) and 99 (not in the CSV).
        path = self.write_csv([(i, "") for i in range(1, 7)])
        api = FakeTriageApi(siblings={1: [4, 99]})
        rc, out, _ = self.run_main(
            ["--deployment-slug", "d", "--csv", path, "--state", "reopened", "--limit", "2"], api
        )
        self.assertEqual(rc, 0)
        # Without sibling removal this would be [[1, 2], [3, 4], [5, 6]].
        self.assertEqual(api.submitted, [[1, 2], [3, 5], [6]])
        self.assertIn("2 additional sibling(s) triaged (1 removed from queue)", out)
        self.assertIn("including 2 additional sibling(s) not submitted (1 of them removed from queue)", out)

    def test_siblings_only_removed_within_same_issue_type(self):
        path = self.write_csv([(1, "sast"), (2, "sca")])
        api = FakeTriageApi(siblings={1: [2]})
        rc, _, _ = self.run_main(["--deployment-slug", "d", "--csv", path, "--state", "fixing"], api)
        self.assertEqual(rc, 0)
        self.assertEqual(
            [(p["issue_type"], p["issue_ids"]) for p in api.payloads],
            [("sast", [1]), ("sca", [2])],
        )

    def test_unreported_issues_written_and_not_retried(self):
        path = self.write_csv([(1, ""), (2, ""), (3, "")])
        api = FakeTriageApi(not_triaged={2})
        rc, _, _ = self.run_main(
            ["--deployment-slug", "d", "--csv", path, "--state", "fixing", "--limit", "2"], api
        )
        self.assertEqual(rc, 0)
        self.assertEqual(api.submitted, [[1, 2], [3]])
        self.assertEqual(self.read_csv("not_triaged.csv"), [("sast", 2)])

    def test_failure_writes_remaining_queue_minus_siblings(self):
        path = self.write_csv([(1, ""), (2, ""), (3, ""), (4, ""), (5, "sca")])
        api = FakeTriageApi(siblings={1: [4]}, fail_on={2})
        rc, _, err = self.run_main(
            ["--deployment-slug", "d", "--csv", path, "--state", "fixing", "--limit", "1"], api
        )
        self.assertEqual(rc, 1)
        self.assertIn("FAILED", err)
        self.assertEqual(self.read_csv("remaining.csv"), [("sast", 2), ("sast", 3), ("sca", 5)])

    def test_dry_run_sends_nothing_and_needs_no_token(self):
        path = self.write_csv([(i, "") for i in range(1, 6)])
        api = FakeTriageApi()
        rc, out, _ = self.run_main(
            ["--deployment-slug", "d", "--csv", path, "--state", "fixing", "--limit", "2", "--dry-run"],
            api,
            token=None,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(api.payloads, [])
        self.assertIn("up to 3 request(s)", out)

    def test_missing_token(self):
        path = self.write_csv([(1, "")])
        rc, _, err = self.run_main(
            ["--deployment-slug", "d", "--csv", path, "--state", "fixing"], token=None
        )
        self.assertEqual(rc, 1)
        self.assertIn("SEMGREP_APP_TOKEN", err)

    def test_argument_validation(self):
        path = self.write_csv([(1, "")])
        cases = [
            ["--deployment-slug", "d", "--csv", path],
            ["--deployment-slug", "d", "--csv", path, "--state", "fixing", "--reason", "no_time"],
            ["--deployment-slug", "d", "--csv", path, "--note", "x" * 3001],
            ["--deployment-slug", "d", "--csv", path, "--state", "fixing", "--limit", "3001"],
        ]
        for args in cases:
            with self.subTest(args=args[4:]), self.assertRaises(SystemExit):
                self.run_main(args)


if __name__ == "__main__":
    unittest.main()
