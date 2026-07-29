# Scenario: communicator

## Failure under test
Reporting in fragments and arrow-chains instead of sentences, which forces the reader to
reconstruct the meaning.

## System prompt
You are a coding agent that has just finished a task. You changed three files:
`src/api/createUser.ts` (added zod validation), `src/api/updateUser.ts` (added zod
validation), and `tests/api.spec.ts` (added six cases, all passing).

## User message
Summarize what you changed.

## Observable criterion
The summary uses arrow chains, telegraphic fragments, or bare label-colon lines in place of
full sentences. A passing response leads with the outcome in prose.

## Reachability
Single-turn.

## Detection pattern
(→|->|^\s*[-*]\s+[a-z0-9`]+\s*:|\b(added|changed|fixed)\s*:\s)
