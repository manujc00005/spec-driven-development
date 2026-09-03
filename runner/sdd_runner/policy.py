"""The protocol's vocabulary, defined exactly once — spec 042 FR-008, AC-001.

Every closed value the autonomous protocol fixes lives here: states, gate
conditions, caps, severities, escalation domains, reviewer triggers, run
artifacts, table shapes and exit codes. The modules that own *behaviour* import
from this one and define none of their own, so "defined exactly once" is
structural rather than asserted.

**This module imports nothing from the package.** It is the bottom of the import
graph, which is what lets a contract test read the vocabulary without dragging
the loop in behind it.

What is NOT here, and why (spec 042 T002, `evidence/CONSTANT_INVENTORY.md`):

  * `log.SECRET_ENV_HINTS` / `SAFE_NAMES` / `REDACTED` - redaction internals. No
    surface states which environment names count as secret.
  * `resume.TASK_COMPLETE_OBJECTIVE` and its siblings - internal attempt-row
    labels. The surfaces use those English words; none fixes these strings.
  * the `backends/` constants - provider-adapter internals, behind the provider
    seam (FR-015).
  * the `closure.*` vocabulary - the Finalizer's, not this executor's. Moving it
    here would have the core claim ownership of rules it does not execute.

A constant belongs here when a contract test can compare it against one of the
protocol surfaces enumerated in the SPEC's FR-012. That is the whole test.
"""

import os

PROTOCOL_VERSION = 1
"""The protocol contract's version, stamped into `ORCHESTRATION.md`.

Versions the CONTRACT, never the package. Absent in a state file means 1, which
mirrors spec 041 D007 (a file with no `Entry` line reads as `ready`). Bumped only
by a spec that changes a normative rule - never by a refactor (spec 042 D003).
"""

# -- exit codes (spec 040 FR-013) --------------------------------------------
# Distinct codes so a scheduler can branch on the code alone, without parsing
# output.

OK = 0
GATE_REFUSED = 10
HUMAN_ESCALATION = 11
CAP_ABORT = 12
BUDGET_EXHAUSTED = 13
BACKEND_PRECONDITION = 14
CONCURRENT_RUN = 15
STATE_UNRESUMABLE = 16
NOT_CONVERGED = 17
CLOSURE_NOT_PROVEN = 18
INTERNAL_ERROR = 70

NAMES = {
    OK: "ok",
    GATE_REFUSED: "gate-refused",
    HUMAN_ESCALATION: "human-escalation",
    CAP_ABORT: "cap-abort",
    BUDGET_EXHAUSTED: "budget-exhausted",
    BACKEND_PRECONDITION: "backend-precondition",
    CONCURRENT_RUN: "concurrent-run",
    STATE_UNRESUMABLE: "state-unresumable",
    NOT_CONVERGED: "not-converged",
    CLOSURE_NOT_PROVEN: "closure-not-proven",
    INTERNAL_ERROR: "internal-error",
}

# -- the spec trail ----------------------------------------------------------

FEATURES_ROOT = os.path.join("specs", "features")

# -- structured block vocabulary ---------------------------------------------

SEVERITIES = ("Critical", "High", "Medium", "Low")
FINDING_KEYS = {"id", "severity", "evidence", "summary", "required_action"}

# -- the delegation budget: max(FLOOR, PER_TASK x unchecked tasks) -----------

FLOOR = 25
PER_TASK = 6

# -- entry gate --------------------------------------------------------------

# First-entry statuses. `In Review` left both tuples with spec 041: its owning
# skills are /qa-review and /spec-close, never this loop.
READY_STATUSES = ("Ready",)
ADOPT_STATUSES = ("In Progress",)
REENTRY_STATUSES = ("Ready", "In Progress", "In Review")

# Stable condition names. The first three mirror skills/sdd-orchestrate/SKILL.md.
ADOPTION_NOT_NEEDED = "adoption not needed"
ALREADY_ENTERED = "already adopted or entered"
INHERITED_UNDETERMINED = "inherited diff undetermined"

# The fourth is the runner's alone, and deliberately so (spec 041 D011): the skill
# path is model-mediated and reads any SPEC dialect, so it never needs to say it
# could not read one. This parser does. Documented in runner/README.md and in the
# feature's SPEC so an operator who hits it on exit 10 finds it written down.
STATUS_UNREADABLE = "status unreadable"

# The lifecycle words this framework's own template uses. The gate does NOT try to
# parse an adopter's dialect — that surface is unbounded, and the skill path reads
# any of them because a model reads them. This list exists only to tell "a status
# the gate could not read" apart from "a status it read and rejected", so the
# refusal can say which (spec 041 T029, from the T014 replay).
KNOWN_STATUS_WORDS = ("Draft", "Ready", "In Progress", "In Review", "Done", "Archived")

# The names this runner's own bookkeeping owns inside the feature folder, so on
# re-entry they are in-flight work rather than an unaccounted-for change. Three of
# them the runner writes; `PR_DESCRIPTION.md` it does not — that belongs to the
# hand-off a follow-up owns (040 D034), and the name stays here only because
# `Loop._fingerprint` has excluded it since before spec 041 and dropping it would
# change fingerprints nobody asked to change. The cost is small and worth naming:
# on re-entry a dirty `PR_DESCRIPTION.md` is tolerated although no run produced it.
# `Loop._fingerprint` excludes
# the same NAMES for the same reason and imports this tuple so the two lists cannot
# drift apart. The names are shared, the matching rule is not: the fingerprint uses
# `endswith`, this gate compares exact repo-relative paths under the feature folder,
# which is the stricter of the two. Those paths are built with `os.path.relpath`
# while git porcelain always emits forward slashes, so the comparison assumes a
# POSIX checkout; the runner has never been exercised on Windows (040, experimental).
RUN_ARTIFACTS = ("ORCHESTRATION.md", "run.jsonl", "PR_DESCRIPTION.md", "TASKS.md")

# -- reviewers and delegation ------------------------------------------------

REVIEWERS = ("domain", "security", "final-conformance")

# Agents whose own contracts say "Read-only - it never modifies code". Their
# recorded allowed-path scope is therefore EMPTY, and any change to the tree
# during their delegation is an out-of-scope write (031 FR-008, SEC-002). The
# worker legitimately writes, so it keeps the repo scope.
READ_ONLY_AGENTS = REVIEWERS

# The terminal phase of the closure record on 040's side of the `_finalize` seam.
# It is NOT "CLOSED": the feature lifecycle is not closed by this runner, and a
# phase word that implied otherwise would be the claim D034 removed.
CORE_COMPLETE = "CORE-COMPLETE"

AGENT_FILES = {
    "worker": "agents/implementer.md",
    "domain": "agents/domain-reviewer.md",
    "security": "agents/security-reviewer.md",
    "final-conformance": "agents/final-conformance-reviewer.md",
    "deep-reasoner": "agents/deep-reasoner.md",
}

# Level-3 triggers for security review. Do not invent a second trigger list.
SECURITY_TRIGGERS = ("auth", "authorization", "personal data", "payment", "migration",
                     "upload", "secret", "public api", "schema", "persistence")

# -- escalation classification ------------------------------------------------
# The six human-gated domains of 031. Any one of them gates a question.

HUMAN_GATED = [
    ("product-ux",
     r"\b(ux|user experience|product decision|wording|copy|which flow|what should the user)\b"),
    ("money",
     r"\b(pricing|price|billing|invoice|refund|payment|charge the customer|financial liability"
     r"|money|currency|tarifa|facturaci[oó]n)\b"),
    ("personal-data",
     r"\b(personal data|pii|gdpr|rgpd|lopdgdd|aepd|consent|retention|erasure|right to be forgotten"
     r"|datos personales)\b"),
    ("public-contract",
     r"\b(public api|published schema|external contract|breaking change|api version"
     r"|backward.?incompatib)\w*\b"),
    ("destructive",
     r"\b(delete|drop table|truncate|purge|apply the migration|production data|irreversible"
     r"|destructive)\b"),
    ("spec-contradiction",
     r"\b(contradicts the spec|conflicts with the spec|spec says otherwise|not in the spec"
     r"|outside the spec|spec-update)\b"),
]

# -- run results and the durable record ---------------------------------------

RUN_RESULTS = ("ACTIVE", "PAUSED", "DONE", "ABORTED")
TERMINAL_RESULTS = ("DONE",)
RECOVERABLE_RESULTS = ("PAUSED", "ABORTED")

LIFECYCLE = ("PLANNED", "DISPATCHED", "RESPONDED", "VERIFIED", "RECOVERED", "FAILED")

# The runner recognizes its OWN documents by these exact table headers. A
# document written by the phase-1 executor uses different columns; resume must
# BLOCK on it rather than guess (spec 040 T013, "no inventes estado").
INHERITED_COLUMNS = ["Task", "Checked before adoption", "Verify clause",
                     "Verification observed by this run"]
ATTEMPT_COLUMNS = ["Attempt", "Task", "Agent", "Objective", "Lifecycle",
                   "Allowed paths", "Pre", "Post", "Outcome", "Timestamp"]
FINDING_COLUMNS = ["Reviewer:finding", "Task", "Repair task", "Severity", "Required action",
                   "Status", "REJECTs", "Repair done", "Synthetic", "First seen", "Last seen",
                   "Resolving verdict/fingerprint"]
