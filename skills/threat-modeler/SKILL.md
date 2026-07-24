---
name: threat-modeler
description: Mindset manual for attacker thinking while writing code — ask "who can call this and what's the worst input?" before the first draft, not after. Use before writing any handler, endpoint, parser, query, or anything that touches external input.
---

## SDD Contract

```yaml
category: mindset
inputs: [handler/endpoint/parser-under-design]
outputs: [behavioral-constraint]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: security-reviewer
secondary_agents: [implementer]
profile_scope: all
provider_specific: true
```

# The Threat Modeler

**Security is a property of the first draft, not a review you pass later.** Ask "how would I attack this?" while you write the code, and most vulnerabilities never get typed.

This is the *mindset* that feeds `security-review`: the review audits a change after it exists; this manual makes the attack question part of writing it, so the review finds less. It teaches defensive thinking only — spotting and closing holes, never exploiting them.

## Triggers

- Before writing any handler, endpoint, route, parser, deserializer, or query.
- The moment code touches external input: request params, headers, cookies, uploaded files, env vars, or data crossing a trust boundary (including rows from a shared DB).
- When adding a capability or permission — before, not after, you wire it up.

## Rules

- **Name the caller and the worst input.** Before writing the body, answer in one line: who can reach this, with what worst-case input, and what do they gain if it's malicious? If you can't answer, you don't understand the surface yet.
- **Treat all external input as hostile until validated.** Params, headers, files, env, and cross-boundary DB content are attacker-controlled by default. Validate type, range, authorization, and shape at the boundary — not deep inside the logic.
- **Pair every use case with its abuse case.** When you add "user can upload an avatar," say in the same breath "…so an attacker can upload a 2GB polyglot file to path `../../etc`." The abuse case drives the guard you write.
- **Authorization is separate from authentication.** Knowing *who* the caller is doesn't mean they may do *this*. Check both — a valid token is not a permission.
- **Never build a query, command, or path by string concatenation from input.** Use parameterized queries, argument arrays, and path-join with validation. Concatenation is the vulnerability, regardless of how "trusted" the input feels.

## Anti-patterns

- **Format-checked, not authorized.** — Bad: validating that `accountId` is a UUID, then reading it without checking it belongs to the caller. Good: validate format *and* ownership.
- **Trusting the client.** — Bad: relying on the front-end's "admin-only" button to gate an action. Good: enforce the check server-side; the client is a suggestion.
- **"Internal, nobody will call it."** — Bad: an unauthenticated internal endpoint assumed unreachable. Good: authenticate it anyway; "internal" is a network accident, not a guarantee.
- **Concatenated query/command/path.** — Bad: `"SELECT * FROM u WHERE id=" + id`. Good: parameterized query with `id` bound.
- **Unbounded input.** — Bad: accepting an upload or a list with no size/length cap. Good: enforce limits at the boundary.

## Contrast

A generic model adds security when something makes it — a review comment, a checklist, an explicit "make this secure." Left alone, it writes the happy path and trusts its inputs, because the code works in the demo. This manual inverts the default: it assumes every input is an attack until proven safe and asks the abuse question before writing the use case. The vulnerability a generic model ships and a reviewer later catches is one this manual never wrote.

## Closing checklist

- [ ] Did I name who can call this and the worst-case input?
- [ ] Is every external input validated at the boundary?
- [ ] Did I check authorization, not just authentication?
- [ ] Did I state the abuse case for each new capability?
- [ ] Are all queries/commands/paths parameterized, never concatenated?
- [ ] Are sizes, lengths, and ranges bounded?
