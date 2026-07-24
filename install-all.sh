#!/usr/bin/env bash
# install-all.sh — thin convenience wrapper that installs BOTH adapters in order:
#   1) Claude Code adapter  ->  ./install.sh
#   2) Codex adapter        ->  ./adapters/codex/install-codex.sh
#
# It does NOT modify or reimplement either installer — it only calls them. Each installer stays the
# single source of truth for its own behavior, flags, and safety guarantees. Both are idempotent, so
# re-running this wrapper is safe: whatever is already installed is reported as a no-op.
#
# The two adapters install to DIFFERENT locations and never overlap:
#   Claude -> central config dir (+ optional ~/.claude linking)
#   Codex  -> AGENTS.md in the target project root + prompts under ~/.codex/prompts
#
# Codex is prompt-based and UNVERIFIED against a live Codex CLI — see adapters/codex/PARITY.md.
#
# Usage:
#   install-all.sh [--profile P] [--link-user-claude]
#                  [--codex-target DIR] [--codex-home DIR]
#                  [--skip-claude] [--skip-codex]
#                  [--dry-run] [--force]
#                  [--claude-args "…"] [--codex-args "…"] [-h|--help]
#
#   --dry-run / --force     forwarded to BOTH installers.
#   --profile / --link-user-claude   go to the Claude installer.
#   --codex-target (-> codex --target) / --codex-home   go to the Codex installer.
#   --claude-args / --codex-args     append extra raw args to the respective installer.
#
# Exit: if the Claude step fails, the Codex step is skipped and its exit code is returned.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SKIP_CLAUDE=false
SKIP_CODEX=false
DRY_RUN=false
FORCE=false
PROFILE=""
LINK_USER_CLAUDE=false
CODEX_TARGET=""
CODEX_HOME_ARG=""
EXTRA_CLAUDE=""
EXTRA_CODEX=""

usage() { sed -n '2,29p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --profile) PROFILE="${2:?--profile needs a value}"; shift 2 ;;
    --link-user-claude) LINK_USER_CLAUDE=true; shift ;;
    --codex-target) CODEX_TARGET="${2:?--codex-target needs a directory}"; shift 2 ;;
    --codex-home) CODEX_HOME_ARG="${2:?--codex-home needs a directory}"; shift 2 ;;
    --skip-claude) SKIP_CLAUDE=true; shift ;;
    --skip-codex) SKIP_CODEX=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --force) FORCE=true; shift ;;
    --claude-args) EXTRA_CLAUDE="${2:-}"; shift 2 ;;
    --codex-args) EXTRA_CODEX="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERROR] unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

CLAUDE_INSTALLER="$REPO_ROOT/install.sh"
CODEX_INSTALLER="$REPO_ROOT/adapters/codex/install-codex.sh"

rc=0

# ---------------------------------------------------------------------------
# 1) Claude Code adapter
# ---------------------------------------------------------------------------
if [ "$SKIP_CLAUDE" = true ]; then
  echo "== [1/2] Claude Code adapter — SKIPPED (--skip-claude) =="
else
  echo "== [1/2] Claude Code adapter -> install.sh =="
  if [ ! -x "$CLAUDE_INSTALLER" ] && [ ! -f "$CLAUDE_INSTALLER" ]; then
    echo "[ERROR] not found: $CLAUDE_INSTALLER" >&2; exit 1
  fi
  CLAUDE_ARGS=()
  [ -n "$PROFILE" ] && CLAUDE_ARGS+=(--profile "$PROFILE")
  [ "$LINK_USER_CLAUDE" = true ] && CLAUDE_ARGS+=(--link-user-claude)
  [ "$DRY_RUN" = true ] && CLAUDE_ARGS+=(--dry-run)
  [ "$FORCE" = true ] && CLAUDE_ARGS+=(--force)
  if [ -n "$EXTRA_CLAUDE" ]; then
    # shellcheck disable=SC2206
    read -ra _extra <<< "$EXTRA_CLAUDE"; CLAUDE_ARGS+=("${_extra[@]}")
  fi
  bash "$CLAUDE_INSTALLER" ${CLAUDE_ARGS[@]+"${CLAUDE_ARGS[@]}"}
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "[ERROR] Claude installer exited $rc — skipping Codex. Fix the above and re-run." >&2
    exit $rc
  fi
fi

echo ""

# ---------------------------------------------------------------------------
# 2) Codex adapter
# ---------------------------------------------------------------------------
if [ "$SKIP_CODEX" = true ]; then
  echo "== [2/2] Codex adapter — SKIPPED (--skip-codex) =="
else
  echo "== [2/2] Codex adapter -> adapters/codex/install-codex.sh =="
  if [ ! -f "$CODEX_INSTALLER" ]; then
    echo "[ERROR] not found: $CODEX_INSTALLER" >&2; exit 1
  fi
  if [ -n "$CODEX_TARGET" ]; then
    echo "   Codex AGENTS.md -> $CODEX_TARGET   (+ prompts -> ${CODEX_HOME_ARG:-~/.codex}/prompts)"
  else
    echo "   Codex AGENTS.md: SKIPPED (no --codex-target given — AGENTS.md is per-project)."
    echo "                    prompts still install to ${CODEX_HOME_ARG:-~/.codex}/prompts."
    echo "                    pass --codex-target <your-project> to install AGENTS.md too."
  fi
  CODEX_ARGS=()
  [ -n "$CODEX_TARGET" ] && CODEX_ARGS+=(--target "$CODEX_TARGET")
  [ -n "$CODEX_HOME_ARG" ] && CODEX_ARGS+=(--codex-home "$CODEX_HOME_ARG")
  [ "$DRY_RUN" = true ] && CODEX_ARGS+=(--dry-run)
  [ "$FORCE" = true ] && CODEX_ARGS+=(--force)
  if [ -n "$EXTRA_CODEX" ]; then
    # shellcheck disable=SC2206
    read -ra _extrac <<< "$EXTRA_CODEX"; CODEX_ARGS+=("${_extrac[@]}")
  fi
  bash "$CODEX_INSTALLER" ${CODEX_ARGS[@]+"${CODEX_ARGS[@]}"}
  rc=$?
fi

echo ""
if [ "$DRY_RUN" = true ]; then
  echo "Dry-run complete for all selected adapters. Nothing was written."
else
  echo "All selected adapters processed. Reminder: the Codex adapter's guardrails are conventions,"
  echo "not enforced hooks, and it is unverified against a live Codex CLI — see adapters/codex/PARITY.md."
fi
exit $rc
