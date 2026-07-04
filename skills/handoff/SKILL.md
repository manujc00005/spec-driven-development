---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work.

## What to include

- **Active goal**: what the user is trying to accomplish, in one sentence.
- **Context**: key decisions made, constraints discovered, and approaches already tried and ruled out.
- **Current state**: what is done, what is in progress, what is blocked.
- **Next step**: the single most useful action for the next session to take first.
- **Suggested skills**: skills the next agent should invoke (e.g. `/spec-implement`, `/debugger`, `/spec-review`).
- **Key file paths**: the spec folder, relevant source files, config files — referenced by path, not content.

## What NOT to include

- Do not paste full file contents — reference paths instead.
- Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL.
- Do not include sensitive information: API keys, passwords, tokens, or personally identifiable information. Redact anything sensitive.
- Do not include conversation scaffolding (greetings, confirmations, status messages) — only the substance.

## Output

Save to the user's temporary directory:

```
%TEMP%\handoff-<timestamp>.md
```

Where `<timestamp>` is the current date-time in `YYYYMMDD-HHmmss` format.

Print the full resolved path to the file after saving so the user can find it.

## Usage

Use this skill when:

- **Context is near the limit**: the conversation is long and a fresh session would benefit from a clean summary.
- **Changing machine, user account, or agent**: the next session will not have access to this conversation history.
- **Handing off to another agent**: a parallel agent needs enough context to continue independently.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the document accordingly — emphasise the relevant context, suggested next steps, and skills.
