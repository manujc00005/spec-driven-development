---
name: scout
description: Mindset manual for orienting before editing — read the structure and an exemplar before writing, search for an existing implementation, derive conventions from the code. Use before your first edit in an unfamiliar area of a codebase.
---

## SDD Contract

```yaml
category: mindset
inputs: [unfamiliar-code-area]
outputs: [behavioral-constraint]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: codebase-researcher
secondary_agents: [implementer]
profile_scope: all
provider_specific: true
```

# The Scout

**In an unfamiliar codebase, the first thing you write should be the last thing you do.** Look before you type: the repo has already decided how this kind of code is written, and your job is to find that decision, not make your own.

This is the *in-the-moment* counterpart to `sdd-onboard` and `context-manager`: those produce durable orientation artifacts (context docs, reading lists); this manual governs the small orientation you do in the seconds before an edit, every time you enter unfamiliar territory.

## Triggers

- Before your first edit in a directory, module, or layer you haven't worked in this session.
- Before writing a utility, helper, or component — the thing you're about to build may already exist.
- The moment you're about to apply a default from your own priors (a library, a file layout, a naming style) rather than the repo's.

## Rules

- **Read structure before writing.** List the directory and open one exemplar file that does the kind of thing you're about to do. Your first edit comes only after you can name the pattern you're following.
- **Search before building.** Grep for the function, endpoint, or component you're about to create. Build new only when the search comes back empty — a second implementation of something that exists is worse than none.
- **Derive conventions from the code.** Naming, test location, error handling, import style, and formatting come from the surrounding files, never from your defaults. When the repo and your instinct disagree, the repo wins.
- **Use the repo's tools, not your favorites.** If the project already solves a job with a library or helper, use it. Don't import a new dependency for something the codebase already does.
- **Locate, don't guess.** When you need a file, list or search for it. Guessing a path and being wrong wastes a round-trip and risks editing the wrong thing.

## Anti-patterns

- **Reinvented utility.** — Bad: writing `formatCurrency` when `utils/money.ts` already exports it. Good: grep `format.*urrency` first, find it, use it.
- **Foreign library.** — Bad: adding `axios` to a repo that uses `fetch` everywhere. Good: match the existing HTTP approach.
- **Guessed location.** — Bad: creating `tests/foo.test.js` when the repo colocates tests as `foo.spec.js` next to source. Good: look at where existing tests live, follow it.
- **Personal restyle.** — Bad: reformatting a file to your brace/quote preference while editing it. Good: match the file's existing style exactly.
- **Default-driven naming.** — Bad: naming a handler `handleSubmit` in a repo where they're all `onSubmitOrder`. Good: read two neighbors, match the pattern.

## Contrast

A generic model starts typing from its own priors — its favorite library, its default file layout, its house naming — because those are fast and familiar, and the code it produces looks reasonable in isolation. This manual starts by making the repo's priors its own: it treats every unfamiliar area as a place with existing answers to find, not a blank page to fill. The tell is that a generic model's code reads as an import from another project; this manual's code reads as if the repo's authors wrote it.

## Closing checklist

- [ ] Did I read the structure and an exemplar before editing?
- [ ] Did I search for an existing implementation before building new?
- [ ] Do my names, layout, and style match the neighbors?
- [ ] Did I use the repo's existing tools instead of importing my own?
- [ ] Did I locate files by listing/searching, not guessing?
- [ ] Could a reviewer tell I'm new to this area from the code? (Should be no.)
