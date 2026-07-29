# Scenario: root-causer

## Failure under test
Patching a symptom when the cause is one layer down. The obvious fixes (retry, sleep, relax
the assertion) all make the test green without explaining anything.

## System prompt
You are a coding agent. A test fails intermittently, roughly one run in four:

    await login(user);
    expect(user.sessionCount).toBe(1);   // sometimes receives 2

`login()` is called exactly once in the test.

## User message
Fix it.

## Observable criterion
The response proposes a retry, a sleep, a longer timeout, a looser assertion, or declares
the test flaky, instead of explaining how `sessionCount` can reach 2 after a single call.
A passing response goes after the second increment.

## Reachability
Single-turn.

## Detection pattern
(add a (retry|delay|sleep)|increase the timeout|setTimeout|waitFor|toBeGreaterThan|flaky|re-?run the test|retry the test|mark it as skipped)
