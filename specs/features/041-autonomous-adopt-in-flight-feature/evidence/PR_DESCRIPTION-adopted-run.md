# feat(pricing): member discount with zero clamp (spec 901-adopted)

## Summary

Adds `src/pricing.discount(total, member=False)`: subtracts a flat `MEMBER_DISCOUNT` (1000) only
when `member` is truthy and clamps the result at zero. Non-members get the input total unchanged.
Implements AC-001 (members get the discount, non-members do not) and AC-002 (totals never go
negative); the flat, members-only rule is D001.

The branch was started by hand (T001, T002) and adopted by the autonomous loop (spec 041). The
inherited-diff review found the discount applied regardless of `member` (DOM-001, Critical); T005
repairs it, T003 adds the clamp, T004 adds the tests.

## Test plan

- `./verify.sh` (PLAN-mandated, hermetic): green at baseline and after every task.
- `python3 -m unittest src.test_pricing`: 7 tests OK — member flat discount; explicit non-member
  unchanged; omitted flag means non-member; non-member below the discount untouched; member clamp
  at zero; boundary equal to the discount; zero input.

## Evidence

- Reviews: domain-reviewer APPROVE at fingerprint `18bf67a80fc8@2ed6adc`; final-conformance
  APPROVE at the same fingerprint, with T001/T002 labeled *inherited, verification not observed*.
- Working tree is uncommitted on `feat/adopted` at `2ed6adc`; the loop made no commits.
