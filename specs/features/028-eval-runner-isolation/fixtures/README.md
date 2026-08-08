# Prompt golden fixtures (T000)

Captured **before** any edit to `scripts/skill-eval.sh`, so T011's byte-identity assertion
(AC-005) compares against pre-change output rather than against the script it is testing.

| Field | Value |
|---|---|
| captured at commit | `8764577` |
| capture date | 2026-08-06 |
| scenario | `evals/scenarios/verifier.md` |
| `scripts/skill-eval.sh` vs `HEAD` | identical (`git diff` empty at capture time) |

## Files

| File | sha256 |
|---|---|
| `verifier-control.prompt.golden` | `c54fc745d2f59281b59155a7f37b4c8a4f7bfa122eaf0053cef0047efcdd1ad1` |
| `verifier-treatment.prompt.golden` | `645aa225351e780bfbcaaca9105b967ad4ce1b6fda71d968d67d2e75f9f4451d` |

## How they were produced

```bash
env -u SKILL_EVAL_RUNNER -u SKILL_EVAL_MODEL bash scripts/skill-eval.sh verifier > raw.txt
sed -n '16,20p' raw.txt > verifier-control.prompt.golden     # between the CONTROL and TREATMENT banners
sed -n '22,92p' raw.txt > verifier-treatment.prompt.golden   # between the TREATMENT and closing banners
```

The line numbers are specific to this capture and are recorded for provenance only. **T011 must
locate the banners rather than hardcoding line numbers** — the pre-run summary gains an
`isolation:` line in T006, which shifts every offset.

## What T011 asserts, and what it deliberately does not

**Asserts:** the text between the arm banners, for an isolated runner, is byte-identical to these
files. That is the FR-010 guarantee — the gates change what is *allowed to run*, never what is
*sent to the model*.

**Does not assert:** the surrounding stdout. The pre-run summary is expected to change (T006 adds
the `isolation:` line) and a whole-stdout golden would fail by design.

## Why a superseded scenario is fine here

Every file in `evals/scenarios/` is superseded (spec 022, D010) because the corpus describes
repository state a model cannot see. That defect makes a scenario unusable as *behavioural
evidence*; it does not affect its use here. These fixtures are a determinism check on string
assembly — no model is called, and the scenario's content is never judged. Spec 023 may replace
`verifier.md`, at which point these goldens are regenerated from the same commit-then-capture
procedure.
