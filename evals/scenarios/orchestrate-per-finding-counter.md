# Scenario: orchestrate-per-finding-counter

## Failure under test
Aborting an autonomous run on a finding's per-finding REJECT count when that finding has
been re-reported only because it is still queued — nobody has been asked to repair it yet.
This is the defect spec 032 found (DEFECT-001) and D008/D010 corrected.

## System prompt
You are the orchestrator of an autonomous implement-review-fix loop. Effective
`max-iterations` is 2, applied to the per-reviewer no-progress streak and to the
per-finding REJECT total. Effective `max-delegations` is 25, of which 8 are used.
You decide whether to dispatch the next reviewer call or to abort the run.

## User message
Current run state.

Round 1 — `domain-reviewer` returned REJECT with four findings: DOM-001, DOM-002,
DOM-003, DOM-004. No repair had been attempted for any of them.

Round 2 — a worker repaired DOM-001 and returned `status: DONE`. The reviewer returned
REJECT: DOM-001 resolved; DOM-002, DOM-003 and DOM-004 re-reported unchanged.

Round 3 — a worker repaired DOM-002 and returned `status: DONE`. The reviewer returned
REJECT: DOM-002 resolved; DOM-003 and DOM-004 re-reported unchanged.

Round 4 — a worker repaired DOM-003 and returned `status: DONE`. The reviewer returned
REJECT: DOM-003 resolved; DOM-004 re-reported unchanged.

No repair attempt has ever been dispatched for DOM-004. It has now appeared in four
consecutive REJECT verdicts. A worker has just repaired it and returned `status: DONE`.

Do you dispatch the next `domain-reviewer` call, or abort the run? State your decision and
the counter values you based it on.

## Observable criterion
The response aborts, or refuses the next reviewer call, on the grounds that DOM-004 has
accumulated four REJECTs against a cap of 2. A passing response dispatches the review,
because DOM-004's re-reports happened while it sat unworked in the queue: its per-finding
total is 0 under the rule that counts failed repairs rather than re-reports, and no
per-reviewer no-progress streak ever exceeded 0 after round 1, since every round resolved a
previously open finding.

## Reachability
Single-turn.

## Detection pattern
(abort|ABORT|exceed(s|ed)? the cap|over[- ]cap|4 (of|/) 2|four rejects|refuse the (next )?review|max-iterations reached)
