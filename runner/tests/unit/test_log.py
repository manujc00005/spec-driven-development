"""FR-011: redaction happens at the writer, so no call site can bypass it."""

import json
import os
import tempfile
import unittest

from sdd_runner.log import RunLog, redact, secret_values

SENTINEL = "sk-ant-sentinel-do-not-log-0001"


class SecretNameRecognition(unittest.TestCase):
    """SEC-003: the hint list was narrower than the names people actually use.

    A false positive costs one over-redacted string in a maintainer's log. A
    false negative costs a credential in clear. The asymmetry decides which way
    to err.
    """

    RECOGNIZED = ("ANTHROPIC_API_KEY", "GH_TOKEN", "AWS_SECRET_ACCESS_KEY",
                  "DB_PASSWORD", "SERVICE_CREDENTIAL", "CLAUDE_CODE_OAUTH_TOKEN",
                  "OPENAI_KEY", "DB_PASS", "GH_PAT", "PRIVATE_KEY", "SIGNING_PWD",
                  "WEBHOOK_SIGNATURE")

    def test_common_credential_variable_names_are_all_recognized(self):
        for name in self.RECOGNIZED:
            with self.subTest(name=name):
                values = secret_values({name: "value-long-enough-to-count"})
                self.assertEqual(values, ["value-long-enough-to-count"])

    def test_ordinary_variables_are_not_treated_as_secrets(self):
        for name in ("PATH", "HOME", "LANG", "PWD", "EDITOR", "SHELL", "TERM"):
            with self.subTest(name=name):
                self.assertEqual(secret_values({name: "/usr/local/bin/something"}), [])

    def test_short_values_are_ignored_whatever_the_name(self):
        self.assertEqual(secret_values({"API_KEY": "abc"}), [])


class Redaction(unittest.TestCase):
    def setUp(self):
        self.env = {"ANTHROPIC_API_KEY": SENTINEL, "PATH": "/usr/bin", "HOME": "/home/x"}

    def test_secret_is_redacted_wherever_it_appears(self):
        counter = iter(range(100))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "run.jsonl")
            log = RunLog(path, clock=lambda: next(counter), environ=self.env)
            log.emit("dispatch", prompt="use %s to auth" % SENTINEL,
                     nested={"deep": [SENTINEL]}, key_name="ANTHROPIC_API_KEY")
            with open(path, encoding="utf-8") as fh:
                body = fh.read()
        self.assertNotIn(SENTINEL, body)
        self.assertIn("[REDACTED]", body)
        # The variable NAME is not a secret and stays legible for debugging.
        self.assertIn("ANTHROPIC_API_KEY", body)

    def test_short_values_are_not_treated_as_secrets(self):
        self.assertEqual(redact("abc", secrets=[]), "abc")

    def test_every_line_is_valid_json_and_append_only(self):
        counter = iter(range(100))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "run.jsonl")
            log = RunLog(path, clock=lambda: next(counter), environ=self.env)
            for i in range(3):
                log.emit("verdict", n=i)
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().strip().splitlines()
        self.assertEqual(len(lines), 3)
        for i, line in enumerate(lines):
            record = json.loads(line)
            self.assertEqual(record["event"], "verdict")
            self.assertEqual(record["n"], i)


if __name__ == "__main__":
    unittest.main()
