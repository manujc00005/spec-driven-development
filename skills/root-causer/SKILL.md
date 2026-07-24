---
name: root-causer
description: Mindset manual for debugging stance — reproduce before hypothesizing, name why the bug happened not just that it's gone, and never patch a symptom when the cause is one layer down. Use when something is broken and you're tempted to fix the first thing you see.
---

## SDD Contract

```yaml
category: mindset
inputs: [current-bug]
outputs: [behavioral-constraint]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: implementer
secondary_agents: []
profile_scope: all
provider_specific: true
```

# The Root Causer

**A bug you can't reproduce, you can't fix — you can only disturb.** And a fix you can't explain isn't a fix; it's a symptom you happened to silence.

This is the *stance* inside `debugger`: that skill gives you the 6-phase procedure and the feedback-loop construction; this manual is the discipline you hold while running it — reproduce first, distrust the easy answer, fix the cause not the surface.

## Triggers

- The moment something is broken, throwing, failing, or slow — before forming any theory.
- When you spot a plausible cause and feel the urge to fix it immediately.
- When a fix "works" and you're about to move on — before you do, check whether you can explain *why*.

## Rules

- **No hypothesis before reproduction.** First make the bug happen on demand — a failing test, a curl, a script. Only once it's red on command do you get to theorize. If you truly can't reproduce it, say precisely why, and treat every fix as unconfirmed.
- **Name why it happened, not just that it's gone.** When a fix works, state the causal story: what condition produced the bug and how the fix removes that condition. "It works now" with no story means you patched a symptom and the cause is still there.
- **Distrust the first plausible explanation.** Before acting on your leading theory, actively look for one piece of evidence that would *contradict* it. The first explanation that fits is often the one that's easiest to think of, not the one that's true.
- **Fix the cause's layer, not the symptom's.** If the null appears in the view but originates in the service, fix the service. Then check the symptom's layer for siblings — other places the same root cause leaks.
- **A masked race is not fixed.** Retries, sleeps, and defensive null-checks that hide a bug without explaining it are symptom patches. If you add one, say what real fix it's standing in for.

## Anti-patterns

- **Guess-first.** — Bad: "probably a caching issue," changing cache config without reproducing. Good: reproduce the stale read on demand, *then* confirm it's the cache.
- **Defensive null-check.** — Bad: adding `if (x == null) return` where `x` was never supposed to be null. Good: find why `x` is null — the missing init two layers up — and fix that.
- **Sleep-the-race-away.** — Bad: `sleep(100)` until the flake stops. Good: find the unsynchronized access and order it correctly.
- **Fix the test, not the code.** — Bad: loosening an assertion so the suite goes green. Good: the assertion was right; the code is wrong — fix the code.
- **"It works now."** — Bad: closing a bug with no causal explanation. Good: "The bug happened because X; the fix removes X; here's it failing before and passing after."

## Contrast

A generic model stops when the symptom disappears: it finds a plausible cause, applies a change, sees the error go away, and reports success — often having moved the bug rather than removed it. This manual stops only when the cause is *named* and the fix *provably* eliminates it: reproduced first, explained in a causal sentence, verified by watching the original trigger now pass. The difference shows up a week later, when the generic model's "fix" resurfaces under a slightly different input and this manual's doesn't.

## Closing checklist

- [ ] Did I reproduce the bug on demand before theorizing?
- [ ] Can I state, in one sentence, why the bug happened?
- [ ] Did I look for evidence against my first explanation?
- [ ] Did I fix the cause's layer, not just where the symptom showed?
- [ ] Did I check for siblings of the same root cause?
- [ ] Did I avoid masking the bug with a retry/sleep/null-check?
