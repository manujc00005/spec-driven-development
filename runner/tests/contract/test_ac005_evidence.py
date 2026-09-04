"""The AC-005 evidence artifact must exist, be complete, and still be true.

Spec 042 `domain:DOM-019`, raised three times. Twice it was a stale count. The
third time the file was **empty** — a truncate-before-read bug wiped it — and the
suite could not tell, because nothing read it. A criterion whose evidence lives in
a file no test opens is a criterion nobody is checking.

The count is **derived**, never compared against a number typed into this file:
the artifact states what the suite reports, and this asserts the artifact's figure
equals what the loader discovers now. A hardcoded expectation here would age
exactly the way the artifact did.
"""

import io
import os
import re
import unittest

from tests.support import REPO_ROOT

ARTIFACT = os.path.join(REPO_ROOT, "specs", "features", "042-canonical-autonomous-core",
                        "evidence", "SUITE_AND_TEST_DIFF.md")

REQUIRED_SECTIONS = ("## Count", "## No assertion was weakened",
                     "## What changed in the test tree, counted correctly")


def read():
    with io.open(ARTIFACT, encoding="utf-8") as fh:
        return fh.read()


def file_table_section():
    """The `## What changed in the test tree` section only.

    Scoped for the same reason `count_section` is: the artifact narrates its own
    corrected history, so anything read from the whole file reads the description
    of a past mistake as a present claim.
    """
    text = read()
    start = text.index("## What changed in the test tree")
    return text[start:]


def table_rows():
    """The section's file table, as {row label: (declared count, [entries])}.

    Parsed from the markdown row structure — cells split on `|`, entries taken as
    the backtick-quoted spans of the Files cell. Not a search over the section's
    text: the prose beside the table names files too, and counting those would be
    the mention-read-as-use failure this artifact exists to record.
    """
    rows = {}
    for line in file_table_section().splitlines():
        if not line.startswith("| **"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not cells[1].isdigit():
            continue
        label = cells[0].strip("* ")
        entries = re.findall(r"`([^`]+)`", cells[2])
        rows[label] = (int(cells[1]), entries)
    return rows


def count_section():
    """The `## Count` section only.

    Scoped rather than whole-file, and for the reason this feature keeps
    relearning: the artifact's header **quotes** its own superseded figures
    (`Ran 362`, `Ran 395`, `Ran 441`) so the history stays readable, and a search
    over the whole file reads those quotations as live claims. The first version
    of this guard did exactly that and failed against its own file's history —
    the fifth time in this feature that a text search mistook a mention for a use,
    this time inside the guard written to end the class.
    """
    text = read()
    start = text.index("## Count")
    end = text.index("##", start + len("## Count"))
    return text[start:end]


def discovered_test_count():
    """What the tree actually holds, counted the same way the suite runs it."""
    import unittest as _unittest
    suite = _unittest.TestLoader().discover(
        os.path.join(REPO_ROOT, "runner", "tests"),
        top_level_dir=os.path.join(REPO_ROOT, "runner"))

    def count(node):
        return sum(count(child) for child in node) if hasattr(node, "__iter__") else 1

    return count(suite)


class TheArtifactExists(unittest.TestCase):
    def test_it_is_present(self):
        self.assertTrue(os.path.isfile(ARTIFACT), "AC-005's evidence artifact is missing")

    def test_it_is_not_empty(self):
        """The failure that produced this guard: 0 bytes, and a green suite."""
        self.assertGreater(os.path.getsize(ARTIFACT), 0,
                           "AC-005's evidence artifact is empty")
        self.assertGreater(len(read().split()), 100,
                           "AC-005's evidence artifact has been gutted")


class TheArtifactIsComplete(unittest.TestCase):
    def test_every_required_section_is_present(self):
        text = read()
        for heading in REQUIRED_SECTIONS:
            with self.subTest(section=heading):
                self.assertIn(heading, text,
                              "AC-005's evidence lost a section it is required to carry")

    def test_it_carries_the_baseline_and_the_floor(self):
        text = read()
        self.assertIn("276", text, "the AC-005 floor is unstated")
        self.assertIn("at least 276", text)


class TheArtifactIsStillTrue(unittest.TestCase):
    def test_the_stated_count_matches_the_tree(self):
        """Derived on both sides — no number is typed into this test."""
        stated = re.findall(r"Ran (\d+) tests", count_section())
        self.assertTrue(stated, "the artifact states no test count")
        self.assertEqual({int(n) for n in stated}, {discovered_test_count()},
                         "the recorded count and the tree have drifted apart")

    def test_the_stated_count_is_at_or_above_the_ac005_floor(self):
        self.assertGreaterEqual(discovered_test_count(), 276,
                                "the suite fell below the count AC-005 protects")

    def test_the_assertion_diff_evidence_still_reports_nothing_removed(self):
        """The claim AC-005 actually rests on."""
        text = read()
        self.assertIn("(no output)", text,
                      "the artifact no longer shows the assertion-level diff as empty")
        self.assertIn("import-only", text)

    def test_each_table_row_counts_what_it_lists(self):
        """The defect this check was added for — `domain:DOM-019`, continued.

        The untracked row read `6` while naming five files, because a regeneration
        updated the number and not the list. A count and a list that disagree are
        two claims about the same fact, and only one of them can be right.
        """
        rows = table_rows()
        self.assertTrue(rows, "the file table is gone from the AC-005 evidence")
        for label, (declared, entries) in sorted(rows.items()):
            with self.subTest(row=label):
                self.assertEqual(declared, len(entries),
                                 "%s declares %d and lists %d"
                                 % (label, declared, len(entries)))

    def test_no_entry_is_counted_twice(self):
        for label, (_declared, entries) in sorted(table_rows().items()):
            with self.subTest(row=label):
                duplicated = sorted({e for e in entries if entries.count(e) > 1})
                self.assertEqual(duplicated, [], "%s lists a file twice: %s"
                                 % (label, duplicated))

    def test_the_prose_does_not_contradict_the_table(self):
        """The prose restates the untracked count in words; it must be the same number."""
        rows = table_rows()
        self.assertIn("New, untracked", rows)
        declared = rows["New, untracked"][0]
        stated = re.search(r"this feature added (\d+) of\s*\n?\s*them",
                           file_table_section())
        self.assertIsNotNone(stated,
                             "the section no longer states the untracked count in prose")
        self.assertEqual(int(stated.group(1)), declared,
                         "the prose and the table disagree about how many files are new")

    def test_the_two_rows_together_account_for_the_whole_union(self):
        """Neither row may quietly drop a file the union command reports."""
        rows = table_rows()
        total = sum(len(entries) for _declared, entries in rows.values())
        self.assertGreaterEqual(total, 15,
                                "the file table has shrunk below what the union reports")

    def test_the_superseded_figures_stay_visible(self):
        """The file's own rule, and the reason its history is readable."""
        text = read()
        for old in ("362", "395", "441"):
            with self.subTest(superseded=old):
                self.assertIn(old, text, "a superseded figure was erased rather than labelled")


if __name__ == "__main__":
    unittest.main()
