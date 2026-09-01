"""Concurrent start — spec 040 AC-011/AC-017, AUDIT-6.

The contested window is the claim itself, and it is far too narrow to hit from
outside: releasing two CLIs from a barrier makes them run the entry gate first,
and several `git` invocations of variable duration separate them by orders of
magnitude more than the window. An earlier version of this file did exactly that
and drew the wrong conclusion from it — see D044.

So the barrier is placed where the race actually is. Each contender wraps
`Loop._load_or_create_state` **in the child process only** — production carries
no test hook — and the two phases are:

1. both announce they have reached the point before the claim, and neither
   proceeds until both have;
2. both attempt the claim, and the winner does not continue until both have
   attempted — which is what stops the winner from finishing and leaving
   resumable state that the loser would then legitimately resume, producing two
   `plan` events with no overlap at all.

No sleeps order anything: every wait is a busy-wait on a file appearing.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from sdd_runner import exits, state
from tests.support import fixture, make_repo

RUNNER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROUNDS = 6

CONTENDER = '''
import os, sys
sys.path.insert(0, {runner_root!r})
BARRIER = {barrier!r}
ARRIVED = os.path.join(BARRIER, "arrived")
ATTEMPTED = os.path.join(BARRIER, "attempted")
RELEASE = os.path.join(BARRIER, "release")

from sdd_runner.loop import Loop
_original = Loop._load_or_create_state


def _announce(directory):
    open(os.path.join(directory, str(os.getpid())), "w").close()


def _wait_file(path):
    while not os.path.exists(path):
        pass


def _wait_count(directory, n):
    while len(os.listdir(directory)) < n:
        pass


def _synchronized(self, unchecked_count):
    _announce(ARRIVED)
    _wait_file(RELEASE)              # phase 1: both are at the claim
    try:
        result = _original(self, unchecked_count)
    except BaseException as exc:
        _announce(ATTEMPTED)
        _wait_count(ATTEMPTED, 2)
        raise
    _announce(ATTEMPTED)
    _wait_count(ATTEMPTED, 2)        # phase 2: the winner waits for the loser
    return result


Loop._load_or_create_state = _synchronized

from sdd_runner.__main__ import main
sys.exit(main({argv!r}))
'''


class SynchronizedClaim(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _round(self):
        root = tempfile.mkdtemp(dir=self.tmp.name)
        repo, feature_dir = make_repo(root)
        script = os.path.join(root, "script.json")
        with open(script, "w", encoding="utf-8") as fh:
            json.dump([fixture("worker_done.md")], fh)

        barrier = os.path.join(root, "barrier")
        for name in ("arrived", "attempted"):
            os.makedirs(os.path.join(barrier, name))

        argv = ["--repo", repo, "--feature", "specs/features/900-fixture",
                "--backend", "stub", "--stub-script", script, "--baseline", "true"]
        child = os.path.join(root, "contender.py")
        with open(child, "w", encoding="utf-8") as fh:
            fh.write(CONTENDER.format(runner_root=RUNNER_ROOT, barrier=barrier, argv=argv))

        env = dict(os.environ, PYTHONPATH=RUNNER_ROOT, PYTHONDONTWRITEBYTECODE="1")
        procs = []
        with open(os.devnull, "rb") as devnull:
            for _ in range(2):
                procs.append(subprocess.Popen(
                    [sys.executable, child], stdin=devnull, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, env=env))
            arrived = os.path.join(barrier, "arrived")
            while len(os.listdir(arrived)) < 2:      # both at the claim
                pass
            open(os.path.join(barrier, "release"), "w").close()
            outputs = [p.communicate(timeout=180) for p in procs]

        codes = [p.returncode for p in procs]
        events = []
        log = os.path.join(feature_dir, "run.jsonl")
        if os.path.isfile(log):
            with open(log, encoding="utf-8") as fh:
                events = [json.loads(line) for line in fh if line.strip()]
        return codes, events, outputs, feature_dir

    # -- AC-017 ----------------------------------------------------------
    def test_exactly_one_owner_while_both_are_inside_the_claim(self):
        for attempt in range(ROUNDS):
            with self.subTest(round=attempt):
                codes, events, outputs, _ = self._round()
                detail = "codes=%s\n%s" % (codes, "\n".join(e for _o, e in outputs))

                self.assertEqual(codes.count(exits.CONCURRENT_RUN), 1,
                                 "exactly one contender must be refused: " + detail)
                self.assertEqual(codes.count(exits.STATE_UNRESUMABLE), 0,
                                 "no contender may read a partial document: " + detail)

                plans = [e for e in events if e["event"] == "plan"]
                self.assertEqual(len(plans), 1, "exactly one owner: " + detail)
                self.assertFalse(plans[0]["resumed"],
                                 "the owner created the run; a resume here means the two never "
                                 "overlapped: " + detail)

                workers = [e for e in events if e["event"] == "dispatch"
                           and e.get("agent") == "worker"]
                self.assertEqual(len(workers), 1, "one worker dispatch in total: " + detail)

    def test_the_loser_dispatches_nothing_and_names_the_owner(self):
        codes, events, outputs, _ = self._round()
        self.assertIn(exits.CONCURRENT_RUN, codes)
        combined = "\n".join(out + err for out, err in outputs)
        self.assertIn("refusing to start a second runner", combined)
        # One `plan`, and the loser is not in it: it never got far enough to plan.
        self.assertEqual(len([e for e in events if e["event"] == "plan"]), 1)

    # -- dead-owner recovery still works ---------------------------------
    def test_a_dead_owner_is_still_recovered_after_the_claim_changed(self):
        codes, _events, _outputs, feature_dir = self._round()
        self.assertIn(exits.CONCURRENT_RUN, codes)

        path = os.path.join(feature_dir, "ORCHESTRATION.md")
        doc = state.Orchestration.load(path)
        fields = state.parse_fields(doc.body("State"))
        fields["runner pid"] = "999999"                  # nobody
        doc.set_body("State", state.render_fields(fields))
        doc.set_body("Run result", "\nACTIVE\n\nresumable: yes\n\n")
        doc.save(path)

        from sdd_runner import resume
        self.assertFalse(resume._pid_alive(999999), "the fixture pid must really be dead")
        resumed = resume.inspect(state.Orchestration.load(path), path, 3,
                                 fields["runner host"])
        self.assertTrue(resumed.recovered_from_interrupt,
                        "an owner whose process is gone must still be recoverable")


class PartialPublication(unittest.TestCase):
    """The document must never be visible before it is whole (AUDIT-6, D045)."""

    def test_a_published_state_file_is_always_a_complete_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ORCHESTRATION.md")
            doc = state.new_document("f", "runner", 0,
                                     {"max_iterations": 3, "max_delegations": 25,
                                      "pid": 1, "host": "h"})
            doc.create_exclusive(path)
            loaded = state.Orchestration.load(path)
            self.assertEqual(state.parse_fields(loaded.body("State"))["writer"], "sdd_runner")
            self.assertEqual(loaded.run_result(), "ACTIVE")

    def test_publishing_over_an_existing_path_is_refused_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ORCHESTRATION.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("someone else got here first\n")
            doc = state.new_document("f", "runner", 0,
                                     {"max_iterations": 3, "max_delegations": 25})
            with self.assertRaises(FileExistsError):
                doc.create_exclusive(path)
            with open(path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "someone else got here first\n")

    def test_the_claim_path_never_creates_an_empty_file(self):
        """The window cannot be caught by timing, so the mechanism is asserted.

        Making the path exist before the content is written is what produced the
        window at all: a contender that looked in between loaded a truncated
        document and exited 16. Racing for a sub-microsecond interleaving is not
        evidence; forbidding the call that opens it is.
        """
        import itertools

        from sdd_runner import loop as loop_mod
        from sdd_runner.backends.stub import StubBackend
        from sdd_runner.log import RunLog
        from tests.support import GREEN_BASELINE

        with tempfile.TemporaryDirectory() as tmp:
            repo, feature_dir = make_repo(tmp)
            state_path = os.path.join(feature_dir, "ORCHESTRATION.md")
            offenders = []
            real_open = os.open

            def watched_open(path, flags, *args, **kwargs):
                if os.fspath(path) == state_path and flags & os.O_CREAT:
                    offenders.append((path, flags))
                return real_open(path, flags, *args, **kwargs)

            counter = itertools.count()
            log = RunLog(os.path.join(feature_dir, "run.jsonl"),
                         clock=lambda: next(counter), environ={})
            loop = loop_mod.Loop(repo, feature_dir, StubBackend(script=["x"]), log,
                                 clock=lambda: 0, baseline_cmd=GREEN_BASELINE)
            os.open = watched_open
            try:
                loop._load_or_create_state(2)
            finally:
                os.open = real_open

        self.assertEqual(offenders, [],
                         "the claim opened the state path directly; publication must go "
                         "through create_exclusive, which never makes an empty file visible")

    def test_no_temporary_file_is_left_behind(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ORCHESTRATION.md")
            doc = state.new_document("f", "runner", 0,
                                     {"max_iterations": 3, "max_delegations": 25})
            doc.create_exclusive(path)
            self.assertEqual([n for n in os.listdir(tmp) if n.startswith(".orchestration")], [])


if __name__ == "__main__":
    unittest.main()
