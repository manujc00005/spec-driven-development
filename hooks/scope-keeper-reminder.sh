#!/usr/bin/env bash
# scope-keeper-reminder.sh — PreToolUse nudge on Edit/Write/NotebookEdit.
#
# The mindset skills are declared "always in effect", but a skill is
# model-invoked: its rules only reach context if the assistant chooses to load
# it. That gap is the point of this hook (spec 036) — scope-keeper's own
# description names a deterministic trigger, "before your first edit", and this
# is the harness observing it.
#
# Fires ONCE per session (keyed on session_id, falling back to a time throttle
# when that field is absent). Set SDD_SCOPE_REMINDER=0 to disable.
#
# Exit 0 ALWAYS — reinforcement, not enforcement (spec 036 D002). Scope is a
# judgement, not a predicate; a hook that blocked edits on a judgement call
# would fire on correct work and be switched off within a day, taking the
# reminder with it. Nothing below may fail an edit.

set -uo pipefail   # deliberately NOT -e: no internal failure may block an edit

FALLBACK_TTL_SECONDS=3600

# Always drain stdin, even when disabled: leaving the payload unread can hand
# the caller a broken pipe.
INPUT="$(cat 2>/dev/null || true)"

[ "${SDD_SCOPE_REMINDER:-1}" != "0" ] || exit 0

LIB="$(dirname "${BASH_SOURCE[0]}")/lib/claude-json.sh"
SESSION_ID=""
if [ -f "$LIB" ]; then
  # shellcheck source=lib/claude-json.sh
  . "$LIB" 2>/dev/null || true
  if command -v claude_json_get_field >/dev/null 2>&1; then
    SESSION_ID="$(claude_json_get_field "$INPUT" "session_id" 2>/dev/null || true)"
  fi
fi

# The session id becomes a filename, so it is sanitised to a closed character
# set rather than escaped: a value like "../../etc/passwd" must not be able to
# name a path at all. Anything that sanitises away falls through to the time
# throttle (spec 036 AC-006).
SAFE_ID="$(printf '%s' "$SESSION_ID" | tr -cd 'A-Za-z0-9_-' | cut -c1-64)"

TMPDIR_SAFE="${TMPDIR:-/tmp}"
if [ -n "$SAFE_ID" ]; then
  MARKER="$TMPDIR_SAFE/.sdd-scope-reminder-$SAFE_ID"
else
  MARKER="$TMPDIR_SAFE/.sdd-scope-reminder-notsid"
fi

mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null; }

if [ -f "$MARKER" ]; then
  if [ -n "$SAFE_ID" ]; then
    exit 0   # this session has already been reminded
  fi
  # No session id: fall back to a time throttle so a missing harness field
  # degrades to "quieter", never to "nags on every edit".
  marker_mtime="$(mtime "$MARKER" || true)"
  if [ -n "$marker_mtime" ]; then
    age=$(( $(date +%s) - marker_mtime ))
    [ "$age" -le "$FALLBACK_TTL_SECONDS" ] && exit 0
  fi
fi

# A marker we cannot write means "remind again next time" — never a reason to
# stay silent, and never a reason to fail.
touch "$MARKER" 2>/dev/null || true

# Excerpt only. skills/scope-keeper/SKILL.md is the source of truth; scripts/
# mindset-hook.test.sh asserts these claims still exist there, so the two
# cannot drift silently (spec 036 D004).
printf '%s\n' '{"systemMessage": "[scope-keeper] Before this edit — do exactly what was asked: the requested scope IS the deliverable. No drive-by refactors, no \"while I am at it\", no speculative generality. A real improvement you spot mid-task gets reported, not applied. Necessary-adjacent is in scope (say why); \"would be nicer\" is not. Dead code your change created is yours to remove; dead code you found is not. Match the surrounding code. Full manual: /scope-keeper. This is a reminder, not a gate — use your judgement. Silence it with SDD_SCOPE_REMINDER=0."}'
exit 0
