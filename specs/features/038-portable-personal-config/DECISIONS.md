# Decisions: portable-personal-config

## Decision log

### D001 - The payload lives outside this repository

**Date:** 2026-08-24

**Status:** Accepted

**Context:** The request was for the config to "travel inside the project". This repository is
**public** — verified with `gh repo view`. The payload includes personal global instructions and
63 memory files referencing client names, infrastructure and a VPS address.

**Decision:** The repository ships the **tool** (export/import scripts, manifest, tests). The
**data** lives in `~/.claude-config/`, which the owner gives a private remote. The scripts only
require the directory to exist; how it travels is the owner's choice.

**Reasoning:** No amount of `.gitignore` discipline makes a public repo a safe place for personal
memory — one `git add -A` undoes it. Separating tool from payload removes the failure mode
structurally rather than guarding against it.

**Consequences:** A new machine needs two clones instead of one. The private repo becomes a
prerequisite, documented in `INSTALL.md`. The scripts stay generic and useful to anyone.

---

### D002 - Import never overwrites, even with `--force`

**Date:** 2026-08-24

**Status:** Accepted

**Context:** `install.sh` already has a `--force` that overwrites differing files after a
timestamped backup. Reusing it for the personal layer would be consistent.

**Decision:** The personal layer never overwrites. Missing → copy. Identical → skip. Different →
leave the target untouched, write `<name>.incoming`, report a conflict. `--force` does not change
this.

**Reasoning:** Framework files have an authoritative upstream, so overwriting them is recoverable
by re-running the installer. A `MEMORY.md` written on the other machine has no upstream: the copy
being overwritten *is* the only copy. The two cases look alike and are not.

**Consequences:** The user resolves conflicts by hand. `.incoming` files accumulate until reviewed
— visible clutter, which is the intended pressure. `--force` now means two different things
depending on the layer, and `INSTALL.md` must say so.

---

### D003 - `MEMORY.md` is the only merge, and only additive

**Date:** 2026-08-24

**Status:** Accepted

**Context:** The owner works the same projects on two machines, so the same `MEMORY.md` index
accumulates different entries on each. Strict D002 would make every one of them a conflict —
turning the common case into noise.

**Decision:** Index lines present in the payload and absent in the target are **appended** under a
dated `<!-- imported YYYY-MM-DD -->` marker. Nothing is reordered, rewritten or removed. The
memory `.md` files themselves follow D002 with no exception.

**Reasoning:** A memory index is a line-oriented list of pointers — appending is well defined and
loses nothing. The memory documents are prose, where merging means guessing.

**Consequences:** Duplicate-but-differently-worded entries can appear; that is visible and
correctable, unlike a silent loss. An index line may point at a file that lost the D002 conflict
and lives as `.incoming` — deliberate: a visible gap beats silence.

---

### D004 - `settings.json` merges absent top-level keys only

**Date:** 2026-08-24

**Status:** Accepted

**Context:** `settings.json` holds `hooks`, `enabledPlugins`, `extraKnownMarketplaces`, `tui`,
`theme`. Some are machine-specific (hooks referencing local paths), others are portable.

**Decision:** Only top-level keys **absent** in the target are added. A key present locally always
wins. Arrays are never merged element-wise. Invalid JSON on either side → refuse that file,
report, continue with the rest.

**Reasoning:** Element-wise array merge would duplicate hooks or resurrect ones deliberately
removed. Key-level absence is the only signal that can be read without inferring intent.

**Consequences:** A machine that already has `hooks` gets none of the payload's. That is correct —
hooks reference local paths — but must be documented, because the user may expect otherwise.

---

### D005 - `python3` for JSON in bash

**Date:** 2026-08-24

**Status:** Accepted

**Context:** The merge needs real JSON parsing. The `.sh` **hooks** are deliberately
dependency-free (no `jq`, no `python3`) so they run anywhere.

**Decision:** These are **scripts**, not hooks. `install.sh` already requires `python3`, as does
`wire-hooks.sh`. Use it. PowerShell uses native `ConvertFrom-Json`.

**Reasoning:** The dependency-free rule exists so hooks never break a session. A script the user
runs on purpose, in a repo that already needs `python3`, is a different contract. Hand-rolling a
JSON parser in bash to honour a rule that does not apply would add risk for no gain.

**Consequences:** The scripts inherit the installer's platform requirements. `hooks/lib/claude-json.sh`
stays untouched and dependency-free.

---

### D006 - `personal/` is export output, not a merge target

**Date:** 2026-08-24

**Status:** Accepted

**Context:** Running export twice raises the same question the import answers — merge or replace?

**Decision:** Export **replaces** `~/.claude-config/personal/` wholesale. It is generated output,
a snapshot of the source machine at that moment.

**Reasoning:** Merging into the export directory would produce a payload matching neither machine,
and the git history of the private repo already provides the previous snapshots.

**Consequences:** Exporting on machine B after machine A overwrites A's snapshot in the working
tree. The commit history keeps it, and the import direction is where non-destructive matters.
`MANIFEST.json` records source machine and timestamp so a snapshot is never anonymous.
