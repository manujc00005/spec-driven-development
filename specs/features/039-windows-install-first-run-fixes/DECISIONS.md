# Decisions: windows-install-first-run-fixes

## D001 — Retry the `CLAUDE.md` link instead of moving the personal-import block

**Status:** Accepted · **Context:** BUG-1

The request preferred moving the personal import above the link step, and allowed the retry
alternative "only if moving the block is dangerous, and document why". It is dangerous, and this is
the why.

The personal payload restores `home/agents` alongside `central/CLAUDE.md`
(`scripts/personal-config.ps1:25-27`, `scripts/lib/personal-config.sh`). The link block copies the
framework's shipped agents into `~/.claude/agents` with `Copy-FileSafely` / `copy_file_safely`,
which is **additive and skips a file that already exists and differs** (without `--force`). The two
blocks therefore contend for the same files, and order decides the winner:

- today — framework agents land first, personal import skips them (**framework wins**);
- after the move — personal agents land first, framework copy skips them (**personal wins**).

That is a real, silent behaviour change in agent precedence, on a code path the reported bug never
touched, for a fix that is supposed to be minimal. Rejected.

Relocating only the `CLAUDE.md` link step reaches the same end state for BUG-1 and touches nothing
else: no other step depends on the personal layer, and no other step depends on `CLAUDE.md` being
linked.

## D002 — Defer the "does not exist yet" message rather than printing it twice

**Status:** Accepted · **Context:** BUG-1

The first link attempt now stays silent when the central `CLAUDE.md` is missing, and the message
prints only if the retry also finds it missing. The alternative — print at the original site, retry
later — puts `CLAUDE.md link skipped` and `CLAUDE.md linked ->` in the same transcript, which reads
as a bug even when it is correct.

**Accepted cost:** if the run dies at the `MissingShipped` guard (`exit 1`, profiles.json out of
sync), it exits between the two attempts and the skip message is never printed. That path is already
failing loudly about a broken repo checkout, and the personal import is skipped there too for the
same reason. Recorded rather than defended.

## D003 — `-CentralDir` fallback only when the parameter was not passed

**Status:** Accepted · **Context:** BUG-2b

An explicitly passed `-CentralDir` is an instruction. If it does not exist, the right answer is to
say so and stop — not to quietly use a different directory that happens to exist. The fallback is
therefore gated on `$PSBoundParameters.ContainsKey('CentralDir')`, so it applies to the *default*
only. This also keeps the fix from mutating any documented behaviour: with the default present, not
one code path changes.

## D004 — No hardlink/copy ladder in bash

**Status:** Accepted · **Context:** BUG-3

BUG-3 is a Windows privilege problem: `New-Item -ItemType SymbolicLink` requires elevation or
Developer Mode. `ln -s` on macOS/Linux requires neither, so there is no failure to fall back from.
Adding a ladder to `install.sh` would be untriggerable code guarding against a condition that does
not arise on the platform, and the request explicitly scoped bash changes to "safe and necessary".

## D005 — `$DefaultCentralDir` as a literal, guarded by a test

**Status:** Accepted · **Context:** BUG-2a

PowerShell cannot reference a `param()` default from inside the same `param()` block, so the value
exists twice: once as the parameter default, once as `$DefaultCentralDir`. Rather than reach for
reflection over `$PSCommandPath`, the duplication is made safe by a regression test that extracts
both literals from the file and asserts they match. Cheap, obvious, and it fails loudly if someone
changes one and forgets the other.

## D006 — Recognise a hardlinked `CLAUDE.md` on re-run

**Status:** Accepted · **Context:** BUG-3

Introducing the fallback changes what the *next* run sees: a hardlinked `~/.claude/CLAUDE.md` is not
a `SymbolicLink`, so the existing branch would tell the user to "resolve manually" a file the
installer had just created for them. Teaching that branch about `LinkType -eq 'HardLink'` is
adjacent-necessary — the fix does not work correctly across runs without it — not a drive-by
improvement.

## D007 — Spec numbered 039, not 032

**Status:** Accepted · **Context:** spec placement

`specs/features/032-autonomous-loop-residual-calibration/` already exists on `main` and is closed.
Reusing `032-` would put two unrelated features under one number in a trail whose only index is the
number. 039 is the next free slot. No other aspect of the request was reinterpreted.
