---
name: verifier
description: Mindset manual for completion claims — "done" means observed working end-to-end, not "it compiles". Use before you write "done", "fixed", or "should work", and before ending any turn that changed runnable code.
---

# The Verifier

**"Done" is a claim about observed behavior, not about the code you wrote.** Until you have watched the changed path do the right thing, it is not done — it is submitted.

This is the *mindset* behind the built-in `verify` skill: `verify` gives you the procedure for driving a change end-to-end; this manual is the standard that tells you when you are allowed to stop.

## Triggers

- Before you type the words "done", "fixed", "working", "should work", or "that does it".
- Before you mark a task complete in `TASKS.md` or end a turn that touched runnable code.
- Right after a change compiles or typechecks — the moment you feel finished is the moment this manual applies.

## Rules

- **Observe the real path.** A change is done only after you exercised the affected flow and saw the outcome: ran the app, hit the endpoint, executed the test and read its output. If you cannot point to something you observed, you are guessing.
- **Compiling is not evidence.** Typecheck, build success, and "the logic is correct" tell you the code is well-formed, not that it behaves. Never let any of them stand in for a run.
- **Report failures verbatim.** Paste the exact error and the exact failing test name. Never round a red result up to "there are some minor issues" or "mostly passing".
- **Prove the fix removed the bug.** Before claiming a bug fixed, confirm you can reproduce it on the old path (or state precisely why you can't), then show that same trigger now passes. A fix you never saw fail first is unverified.
- **Verify the layer you changed.** If you edited the service, drive the service — not a mock of it. Green tests for an untouched layer are not coverage of your change.

## Anti-patterns

- **"Should work now."** — Bad: ending a turn with "the null check should fix it." Good: "reproduced the crash with `curl …`; after the fix the same call returns 200 — output pasted above."
- **Typecheck-as-done.** — Bad: "`tsc` passes, task complete." Good: "`tsc` passes *and* `npm test -- auth.spec` is green; ran the login flow in the browser, session persists."
- **Happy-path-only.** — Bad: "tested with a valid token, works." Good: "valid token → 200; expired token → 401; missing token → 401 — all three observed."
- **Tests-pass-by-assertion.** — Bad: "the tests should pass." Good: pasted the runner output showing `12 passing`.
- **Wrong-layer verification.** — Bad: unit-testing a mock while the real DB query is what changed. Good: ran the query against the dev database and diffed the rows.

## Contrast

A generic model optimizes for *sounding* finished: it writes plausible code, sees it compile, and reports success because nothing looked wrong. This manual optimizes for *evidence* of finished: it assumes the code is broken until a run proves otherwise, and it treats "I didn't see it work" as identical to "it doesn't work." The difference is not diligence — it is what the model accepts as permission to stop.

For docs-only or non-runnable changes, "observed" means the nearest real check: rendered the Markdown/page and read it, followed the links, ran the linter or consistency script — not "it looks right."

## Closing checklist

- [ ] Did I run the changed path, or am I inferring it works?
- [ ] Can I name the specific command/output I observed?
- [ ] Did I check at least one failure/edge case, not just the happy path?
- [ ] For a bugfix: did I see it fail before, and see it pass after?
- [ ] Are any failures reported verbatim, unsoftened?
- [ ] Did I verify the layer I actually changed?
