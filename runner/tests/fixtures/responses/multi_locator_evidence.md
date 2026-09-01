Multi-location finding, which must be ACCEPTED.

```yaml
verdict: REJECT
findings:
  - id: DOM-006
    severity: Medium
    evidence: runner/sdd_runner/counters.py:20-44
    summary: definition and use site disagree
    required_action: Align them
```
