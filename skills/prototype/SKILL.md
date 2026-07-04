---
name: prototype
description: Build a throwaway prototype to answer a design question — a runnable terminal app for logic/state questions (LOGIC branch), or several radically different UI variations on one route (UI branch).
disable-model-invocation: true
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Pick a branch

Identify which question is being answered:

- **"Does this logic / state model feel right?"** → **LOGIC branch**. Build a tiny interactive terminal app that pushes the state machine through cases that are hard to reason about on paper.
- **"What should this look like?"** → **UI branch**. Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

Getting this wrong wastes the whole prototype. If ambiguous and the user is unreachable, default to the branch that better matches the surrounding code (backend module → LOGIC; page or component → UI) and state the assumption at the top.

## Rules that apply to both branches

1. **Throwaway from day one.** Name it so a casual reader can see it is a prototype, not production.
2. **One command to run.** Use the project's existing task runner (`pnpm <name>`, `python <path>`, etc.).
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on.
4. **Skip the polish.** No tests, no error handling beyond what makes it runnable, no abstractions.
5. **Surface the state.** After every action (LOGIC) or on every variant switch (UI), render the full relevant state.
6. **Delete or absorb when done.** When the prototype has answered its question, delete it or fold the validated decision into the real code.

---

## LOGIC branch — interactive terminal app

Use when the question is about **business logic, state transitions, or data shape**.

### Process

#### 1. State the question

Before writing code, write what state model and question you are prototyping — one paragraph at the top of the prototype file or README. A logic prototype that answers the wrong question is pure waste.

#### 2. Pick the language

Use whatever the host project uses. Match existing tooling conventions — do not add a new package manager or runtime just for the prototype.

#### 3. Isolate the logic in a portable module

Put the actual logic behind a small, pure interface that could be lifted into the real codebase later. Choose the right shape:

- **Pure reducer** — `(state, action) => state`. Best for discrete events with a single state value.
- **State machine** — explicit states and transitions. Best when "which actions are even legal now" is part of the question.
- **Set of pure functions** over a plain data type. Best when there is no implicit current state.
- **Class or module with a clear method surface** when the logic genuinely owns ongoing internal state.

Keep it pure: no I/O, no terminal code, no `console.log` for control flow. The TUI imports it and calls into it.

#### 4. Build the smallest TUI that exposes the state

Clear the screen on every tick (`console.clear()` / `print("\033[2J\033[H")` / equivalent) and re-render the whole frame. Each frame:

1. **Current state** — pretty-printed, one field per line or formatted JSON. Bold field names (`\x1b[1m`), dim less-important context (`\x1b[2m`), reset with `\x1b[0m`.
2. **Keyboard shortcuts** at the bottom — `[a] add user  [d] delete user  [q] quit`. Bold the key.

Behaviour: initialise state → read one keystroke → dispatch to handler → re-render → loop until quit.

#### 5. Make it runnable in one command

Add a script to the project's existing task runner. The user must be able to run `pnpm run <prototype-name>` or equivalent — never need to remember a path.

#### 6. Hand it over

Give the user the run command. Let them drive it. Add new actions if they ask. Prototypes evolve.

#### 7. Capture the answer

Ask what the prototype taught them (or leave a `NOTES.md` if they are AFK). The validated reducer / machine / function set can be lifted into the real module — the TUI shell gets deleted.

### LOGIC anti-patterns

- **Don't add tests.** A prototype that needs tests is no longer a prototype.
- **Don't wire it to the real database.** Use an in-memory store unless the question is specifically about persistence.
- **Don't generalise.** The prototype answers one question.
- **Don't blur the logic and the TUI together.** If the reducer references `console.log` or terminal codes, it is no longer portable.

---

## UI branch — variant switcher on a route

Use when the question is **"What should this look like?"**

### Two sub-shapes — strongly prefer A

**Sub-shape A (preferred)** — variants rendered on an existing route, gated by `?variant=` URL param. All existing data fetching, params, and auth stay — only the rendering swaps. Even for things that don't yet have a page but would naturally live inside one, use sub-shape A.

**Sub-shape B (last resort)** — only when there is genuinely no existing page to embed the prototype in. Create a throwaway route following the project's existing routing convention. Name it so it is obviously a prototype.

### Process

#### 1. State the question and pick N

Default to **3 variants**. Cap at 5. Write down the plan in one line:

> "Three variants of the settings page, switchable via `?variant=`, on the existing `/settings` route."

#### 2. Generate radically different variants

Each variant must be **structurally different** — different layout, different information hierarchy, different primary affordance, not just different colours. Use the project's component library / styling system. Export clear component names: `VariantA`, `VariantB`, `VariantC`.

#### 3. Wire them together

```tsx
// pseudo-code — adapt to the project's framework
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <VariantA {...data} />}
    {variant === 'B' && <VariantB {...data} />}
    {variant === 'C' && <VariantC {...data} />}
    <PrototypeSwitcher variants={['A','B','C']} current={variant} />
  </>
);
```

#### 4. Build the floating switcher

A small fixed-position bar at bottom-centre with: left arrow → variant label → right arrow.

- Clicking an arrow updates the URL search param (use the framework's router).
- Keyboard: `←` / `→` also cycle. Do not intercept when an input is focused.
- Visually distinct from the page (high-contrast pill, subtle shadow).
- Hidden in production: gate on `process.env.NODE_ENV !== 'production'` or equivalent.

Put the switcher in a single shared component.

#### 5. Hand it over

Surface the URL and `?variant=` keys. The interesting feedback is usually "I want the header from B with the sidebar from C."

#### 6. Capture the answer and clean up

Once a variant wins, write down which and why. Then:

- **Sub-shape A**: delete losing variants and the switcher; fold the winner into the existing page.
- **Sub-shape B**: promote winning variant to a real route; delete the throwaway route and switcher.

### UI anti-patterns

- **Variants that differ only in colour or copy.** Real variants disagree about structure.
- **Sharing too much code between variants.** A shared `<Header>` is fine; a shared `<Layout>` defeats the point.
- **Wiring variants to real mutations.** Point at a stub — the question is "what should this look like", not "does the backend work".
- **Promoting the prototype directly to production.** Rewrite it properly when folding it in.

---

## SDD integration

- **Never commit prototype code to main.** Prototypes live on a short-lived scratch branch or stay local.
- **Before deleting the prototype**, record the answer in `DECISIONS.md` in the relevant feature folder. The code is throwaway; the decision is permanent.
- The prototype's output feeds the next planning step — it does not replace a spec.

## Recommended next command

- If the prototype answered its question → `/spec-create <feature>` to start the formal spec.
- If the question is still open → adjust the prototype or run `/decision-mapping` to map remaining unknowns.
