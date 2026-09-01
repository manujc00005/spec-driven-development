Found one real problem.

```yaml
verdict: REJECT
findings:
  - id: DOM-001
    severity: High
    evidence: runner/sdd_runner/loop.py:42
    summary: The driver proceeds before persisting state
    required_action: Persist before proceeding past the transition
```
