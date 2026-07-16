#!/usr/bin/env bash
#
# Consistency checker: verifies that profiles.json, the on-disk artifacts
# (skills/, hooks/, specs/_templates/, docs/_templates/, agents/), the hook
# wiring in settings.template.json / settings.template.sh.json, and the
# count claims in README.md all agree with each other.
#
# Exit codes: 0 = consistent, 1 = drift found (or profiles.json invalid),
# 2 = internal error (python3 missing).
#
# Usage: scripts/check-consistency.sh [--fix] [repo_root]
#   repo_root defaults to the repo containing this script. An explicit
#   argument lets the test harness (check-consistency.test.sh) point the
#   checker at a mutated temp copy of the repo.
#   With --fix, auto-corrects safe violations (README count markers) and
#   reports them with [FIXED] prefix. Non-auto-fixable violations block changes
#   and cause exit 1.
#
# See specs/features/007-ci-consistency-check/SPEC.md for the full list of
# drift classes this script enforces (FR-001..FR-011) and FR-012 for --fix.

set -uo pipefail

DEFAULT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIX_MODE=false
REPO_ROOT="$DEFAULT_ROOT"

# Parse --fix flag and optional repo_root argument
if [[ ${1:-} == "--fix" ]]; then
  FIX_MODE=true
  REPO_ROOT="${2:-$DEFAULT_ROOT}"
else
  REPO_ROOT="${1:-$DEFAULT_ROOT}"
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 is required to run this checker (see install.sh for the same dependency)."
  exit 2
fi

python3 - "$REPO_ROOT" "$FIX_MODE" <<'PYEOF'
import json
import os
import re
import sys

repo_root = sys.argv[1]
fix_mode = sys.argv[2].lower() == "true"
errors = []
fixed_markers = []


def err(category, item, message):
    errors.append(f"[{category}] {item} — {message}")


# ---------------------------------------------------------------------------
# Load profiles.json (FR-011: invalid JSON is a clean exit 1, not a traceback)
# ---------------------------------------------------------------------------
profiles_path = os.path.join(repo_root, "profiles.json")
try:
    with open(profiles_path, encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"[ERROR] profiles.json not found at {profiles_path}")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"[ERROR] profiles.json is not valid JSON: {e}")
    sys.exit(1)

profiles = data.get("profiles", {})

CATEGORIES = ("skills", "hooks", "templates", "agents")
PLANNED_KEYS = {
    "skills": "plannedSkills",
    "hooks": "plannedHooks",
    "templates": "plannedTemplates",
    "agents": "plannedAgents",
}

shipped = {cat: set() for cat in CATEGORIES}
planned = {cat: set() for cat in CATEGORIES}
shipped_by_profile = {}
owning_profile = {cat: {} for cat in CATEGORIES}

for pname, pdef in profiles.items():
    disabled = pdef.get("disabled") is True
    per = {cat: set(pdef.get(cat, [])) for cat in CATEGORIES}
    shipped_by_profile[pname] = per

    if disabled:
        for cat, items in per.items():
            if items:
                err("sanity", f"profile '{pname}'", f"disabled profile must ship no {cat}, found {sorted(items)}")
        continue

    for cat in CATEGORIES:
        shipped[cat].update(per[cat])
        for item in per[cat]:
            owning_profile[cat].setdefault(item, pname)
        planned[cat].update(pdef.get(PLANNED_KEYS[cat], []))

# Shipped/planned overlap within the same category is a manifest error.
for cat in CATEGORIES:
    for item in sorted(shipped[cat] & planned[cat]):
        err("sanity", f"{cat[:-1]} '{item}'", "listed as both shipped and planned in profiles.json")


# ---------------------------------------------------------------------------
# Disk existence helpers (mirror install.sh's resolution rules)
# ---------------------------------------------------------------------------
def has_skill(name):
    return os.path.isfile(os.path.join(repo_root, "skills", name, "SKILL.md"))


def has_hook_variant(name, ext):
    return os.path.isfile(os.path.join(repo_root, "hooks", f"{name}.{ext}"))


def has_template(name):
    # Same resolution order as install.sh: specs/_templates/ then docs/_templates/.
    return (
        os.path.isfile(os.path.join(repo_root, "specs", "_templates", name))
        or os.path.isfile(os.path.join(repo_root, "docs", "_templates", name))
    )


def has_agent(name):
    return os.path.isfile(os.path.join(repo_root, "agents", f"{name}.md"))


# ---------------------------------------------------------------------------
# FR-001..004: every shipped item must exist on disk
# ---------------------------------------------------------------------------
for name in sorted(shipped["skills"]):
    if not has_skill(name):
        err("shipped-skill", name, f"declared shipped by profile '{owning_profile['skills'][name]}' but skills/{name}/SKILL.md does not exist")

for name in sorted(shipped["hooks"]):
    missing = [ext for ext in ("sh", "ps1") if not has_hook_variant(name, ext)]
    if missing:
        err("shipped-hook", name, f"declared shipped by profile '{owning_profile['hooks'][name]}' but missing hooks/{name}.{{{','.join(missing)}}}")

for name in sorted(shipped["templates"]):
    if not has_template(name):
        err("shipped-template", name, f"declared shipped by profile '{owning_profile['templates'][name]}' but not found in specs/_templates/ or docs/_templates/")

for name in sorted(shipped["agents"]):
    if not has_agent(name):
        err("shipped-agent", name, f"declared shipped by profile '{owning_profile['agents'][name]}' but agents/{name}.md does not exist")


# ---------------------------------------------------------------------------
# FR-006: planned items must NOT exist on disk yet
# ---------------------------------------------------------------------------
for name in sorted(planned["skills"]):
    if has_skill(name):
        err("planned-drift", f"skill '{name}'", "exists on disk but is still listed as planned in profiles.json — promote it to a shipped 'skills' array")

for name in sorted(planned["hooks"]):
    if has_hook_variant(name, "sh") or has_hook_variant(name, "ps1"):
        err("planned-drift", f"hook '{name}'", "exists on disk but is still listed as planned in profiles.json — promote it to a shipped 'hooks' array")

for name in sorted(planned["templates"]):
    if has_template(name):
        err("planned-drift", f"template '{name}'", "exists on disk but is still listed as planned in profiles.json — promote it to a shipped 'templates' array")

for name in sorted(planned["agents"]):
    if has_agent(name):
        err("planned-drift", f"agent '{name}'", "exists on disk but is still listed as planned in profiles.json — promote it to a shipped 'agents' array")


# ---------------------------------------------------------------------------
# FR-005 + FR-009: orphans (disk artifacts not declared anywhere) and hook
# .sh/.ps1 parity (checked for every hook family on disk, shipped or not).
# ---------------------------------------------------------------------------
skills_dir = os.path.join(repo_root, "skills")
disk_skills = set()
if os.path.isdir(skills_dir):
    for name in os.listdir(skills_dir):
        if os.path.isfile(os.path.join(skills_dir, name, "SKILL.md")):
            disk_skills.add(name)
for name in sorted(disk_skills - shipped["skills"] - planned["skills"]):
    err("orphan-skill", name, "exists on disk (skills/) but is not declared shipped or planned by any profile")

hooks_dir = os.path.join(repo_root, "hooks")
disk_hook_families = {}
if os.path.isdir(hooks_dir):
    for fname in os.listdir(hooks_dir):
        fpath = os.path.join(hooks_dir, fname)
        if not os.path.isfile(fpath) or fname == "README.md":
            continue
        base, ext = os.path.splitext(fname)
        ext = ext.lstrip(".")
        if ext not in ("sh", "ps1"):
            continue
        disk_hook_families.setdefault(base, set()).add(ext)

for name, exts in sorted(disk_hook_families.items()):
    missing = {"sh", "ps1"} - exts
    if missing:
        err("hook-parity", name, f"missing variant(s): {', '.join(sorted(missing))}")

disk_hook_names = set(disk_hook_families.keys())
for name in sorted(disk_hook_names - shipped["hooks"] - planned["hooks"]):
    err("orphan-hook", name, "exists on disk (hooks/) but is not declared shipped or planned by any profile")


def collect_templates(dirpath):
    found = set()
    if os.path.isdir(dirpath):
        for fname in os.listdir(dirpath):
            if os.path.isfile(os.path.join(dirpath, fname)):
                found.add(fname)
    return found


specs_templates_dir = os.path.join(repo_root, "specs", "_templates")
docs_templates_dir = os.path.join(repo_root, "docs", "_templates")
disk_specs_templates = collect_templates(specs_templates_dir)
disk_docs_templates = collect_templates(docs_templates_dir)
disk_templates = disk_specs_templates | disk_docs_templates
for name in sorted(disk_templates - shipped["templates"] - planned["templates"]):
    err("orphan-template", name, "exists on disk (specs/_templates/ or docs/_templates/) but is not declared shipped or planned by any profile")

agents_dir = os.path.join(repo_root, "agents")
disk_agents = set()
if os.path.isdir(agents_dir):
    for fname in os.listdir(agents_dir):
        if fname == "README.md" or not fname.endswith(".md"):
            continue
        if os.path.isfile(os.path.join(agents_dir, fname)):
            disk_agents.add(fname[:-3])
for name in sorted(disk_agents - shipped["agents"] - planned["agents"]):
    err("orphan-agent", name, "exists on disk (agents/) but is not declared shipped or planned by any profile")


# ---------------------------------------------------------------------------
# FR-007: settings template hook wiring
# ---------------------------------------------------------------------------
DEPRECATED_PAIR = ("maven-compile", "java-build-test-guard")
HOOK_REF_RE = re.compile(r"hooks/([A-Za-z0-9_-]+)\.(sh|ps1)")


def check_settings_wiring(filename):
    path = os.path.join(repo_root, filename)
    if not os.path.isfile(path):
        err("settings-wiring", filename, "settings template not found")
        return

    with open(path, encoding="utf-8") as f:
        text = f.read()

    wired_names = set()
    for name, ext in HOOK_REF_RE.findall(text):
        wired_names.add(name)
        if not has_hook_variant(name, ext):
            err("settings-wiring", f"{filename}:{name}.{ext}", f"referenced but hooks/{name}.{ext} does not exist")

    if DEPRECATED_PAIR[0] in wired_names and DEPRECATED_PAIR[1] in wired_names:
        err(
            "settings-wiring",
            filename,
            f"wires both '{DEPRECATED_PAIR[0]}' and '{DEPRECATED_PAIR[1]}' — these must never be wired together (double compile per edit); see profiles.json java-spring-backend note",
        )


check_settings_wiring("settings.template.json")
check_settings_wiring("settings.template.sh.json")


# ---------------------------------------------------------------------------
# Feature 010: Graphify integration consistency (canonical report path,
# SessionStart wiring, setup-graphify references)
# ---------------------------------------------------------------------------
def file_text(rel):
    path = os.path.join(repo_root, rel)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def assert_contains(rel, needle, why):
    text = file_text(rel)
    if text is None:
        err("graphify", rel, "file not found")
    elif needle not in text:
        err("graphify", rel, f"must mention '{needle}' — {why}")


CANONICAL = ".graphify/GRAPH_REPORT.md"
for rel in (
    "hooks/graphify-stale-reminder.sh",
    "hooks/graphify-stale-reminder.ps1",
    "skills/graphify-context/SKILL.md",
    "skills/context-manager/SKILL.md",
):
    assert_contains(rel, CANONICAL, "consumers must resolve the canonical Graphify path (spec 010 FR-001/FR-002)")

for rel in ("settings.template.json", "settings.template.sh.json"):
    assert_contains(rel, "graphify-stale-reminder", "the Graphify hook must be wired on SessionStart (spec 010 FR-004)")

for rel in (
    "docs/INSTALL.md",
    "docs/_templates/GRAPHIFY.md",
    "skills/project-init/SKILL.md",
    "skills/sdd-onboard/SKILL.md",
):
    assert_contains(rel, "setup-graphify", "adoption must point at the setup script (spec 010 FR-008/FR-009)")

for rel in ("scripts/setup-graphify.sh", "scripts/setup-graphify.ps1"):
    if file_text(rel) is None:
        err("graphify", rel, "setup script missing (spec 010 FR-007)")


# ---------------------------------------------------------------------------
# FR-008: README.md count markers
# ---------------------------------------------------------------------------
computed = {
    "skills-total": len(disk_skills),
    "hook-families-total": len(disk_hook_names),
    "hook-scripts-total": sum(len(exts) for exts in disk_hook_families.values()),
    "specs-templates-total": len(disk_specs_templates),
    "docs-templates-total": len(disk_docs_templates),
    "templates-total": len(disk_templates),
    "agents-total": len(disk_agents),
    "profiles-total": len(profiles),
}
for pname, per in shipped_by_profile.items():
    computed[f"{pname}-skills"] = len(per["skills"])
    computed[f"{pname}-hooks"] = len(per["hooks"])
    computed[f"{pname}-templates"] = len(per["templates"])
    computed[f"{pname}-agents"] = len(per["agents"])

REQUIRED_MARKERS = {
    "skills-total", "hook-families-total", "hook-scripts-total",
    "templates-total", "specs-templates-total", "docs-templates-total",
    "agents-total", "profiles-total",
    "core-skills", "core-hooks", "core-templates", "core-agents",
    "java-spring-backend-skills", "java-spring-backend-hooks", "java-spring-backend-templates",
    "messaging-event-driven-templates",
}

readme_path = os.path.join(repo_root, "README.md")
MARKER_RE = re.compile(r"<!-- count:([a-zA-Z0-9_-]+) -->(\d+)<!-- /count -->")

readme_text = None
found_markers = {}  # {key: (old_value, line_no)}

if not os.path.isfile(readme_path):
    err("readme-count", "README.md", "file not found")
else:
    with open(readme_path, encoding="utf-8") as f:
        readme_text = f.read()

    seen_keys = set()
    for m in MARKER_RE.finditer(readme_text):
        key, value = m.group(1), int(m.group(2))
        line_no = readme_text.count("\n", 0, m.start()) + 1
        seen_keys.add(key)
        found_markers[key] = (value, line_no)
        if key not in computed:
            err("readme-count", f"{key} (line {line_no})", f"marker present but '{key}' is not a recognized computed count (stale marker?)")
            continue
        expected = computed[key]
        if value != expected:
            err("readme-count", f"{key} (line {line_no})", f"expected {expected}, found {value}")

    for key in sorted(REQUIRED_MARKERS - seen_keys):
        err("readme-count", key, "required count marker missing from README.md")

    # If --fix mode and no non-auto-fixable violations, update markers in README.
    if fix_mode and readme_text:
        non_readme_errors = [e for e in errors if not e.startswith("[readme-count]")]

        if not non_readme_errors:
            # Safe to fix: no orphans, no wiring issues, etc.
            # Update markers to computed values.
            updated_readme = readme_text
            for key, (old_value, _) in sorted(found_markers.items()):
                if key in computed:
                    new_value = computed[key]
                    if old_value != new_value:
                        pattern = f"<!-- count:{key} -->\\d+<!-- /count -->"
                        replacement = f"<!-- count:{key} -->{new_value}<!-- /count -->"
                        updated_readme = re.sub(pattern, replacement, updated_readme)
                        fixed_markers.append(f"[FIXED] readme {key} — updated from {old_value} to {new_value}")
                        # Remove readme-count error for this key from errors list.
                        errors = [e for e in errors if f"[readme-count] {key}" not in e]

            # Write the updated README.md if any markers were fixed.
            if fixed_markers:
                try:
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(updated_readme)
                except Exception as e:
                    print(f"[ERROR] Failed to write README.md: {e}")
                    sys.exit(1)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
for e in sorted(errors):
    print(e)

for e in sorted(fixed_markers):
    print(e)

if errors:
    print(f"\n{len(errors)} error(s) found.")
    sys.exit(1)

if fixed_markers:
    print(f"\n{len(fixed_markers)} marker(s) fixed in README.md.")

if not errors and not fixed_markers:
    print("Consistency check passed: profiles.json, disk artifacts, settings wiring, and README counts are aligned.")

sys.exit(0)
PYEOF
exit $?
