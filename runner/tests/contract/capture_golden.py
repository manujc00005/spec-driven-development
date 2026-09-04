"""Record the golden CLI transcripts — spec 042 T001.

Run from the repository root:

    PYTHONPATH=runner python3 runner/tests/contract/capture_golden.py

It rewrites every file under the feature's `evidence/golden/`. Re-running it on
an unmodified tree must produce no diff; that reproducibility IS T001's
verification criterion, so the script prints a per-scenario verdict rather than
writing silently.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tests.contract import golden  # noqa: E402


def main():
    os.makedirs(golden.GOLDEN_DIR, exist_ok=True)
    changed, stable = [], []
    for name in sorted(golden.SCENARIOS):
        text = golden.capture(name)
        path = os.path.join(golden.GOLDEN_DIR, name + ".txt")
        previous = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                previous = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        if previous is None:
            print("  recorded  %s" % name)
        elif previous == text:
            stable.append(name)
            print("  stable    %s" % name)
        else:
            changed.append(name)
            print("  CHANGED   %s" % name)
    print("\n%d scenario(s); %d stable, %d changed" % (len(golden.SCENARIOS), len(stable),
                                                       len(changed)))
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
