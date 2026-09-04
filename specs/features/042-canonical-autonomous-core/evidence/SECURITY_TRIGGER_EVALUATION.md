# Level-3 security-trigger evaluation — T024

The protocol's trigger list is `sdd_runner.policy.SECURITY_TRIGGERS`, ten entries, and
`skills/sdd-orchestrate/SKILL.md` says of it: *"Do not invent a second trigger list."* So this is an
evaluation against that list, not a judgement call about how risky the diff feels.

| Trigger | Matched? | Evidence |
|---|---|---|
| `auth` | no | Nothing in the diff authenticates a person or a request. |
| `authorization` | no | No permission model exists here; the runner is single-operator maintainer tooling. |
| `personal data` | no | No personal data is read, stored or logged. |
| `payment` | no | — |
| `migration` | no | `ORCHESTRATION.md` changes additively; no data is transformed and no migration step runs. |
| `upload` | no | — |
| `secret` | no | `log.py`'s redaction (`SECRET_ENV_HINTS`, `SAFE_NAMES`, `REDACTED`) is **untouched** — T002 classified it as implementation detail and left it in place. Confirm with `git diff main -- runner/sdd_runner/log.py` (empty). |
| **`public api`** | **YES** | The feature's whole purpose: `runner/sdd_runner/protocol.py` introduces `run(RunRequest) -> RunOutcome` and `__init__.__all__` publishes eleven names that anything may now depend on. |
| **`schema`** | **YES** | The durable record gains a `Protocol version` header field, and `state.Orchestration.protocol_version` plus `resume.inspect` add a new read-and-refuse path over that schema. |
| **`persistence`** | **YES** | Same change seen from the other side: `ORCHESTRATION.md` is the run's durable authority, and both its write path (`state.new_document`, `Loop._state_fields`) and its acceptance rules changed. |

**Three triggers matched, so `security-reviewer` runs.** It was dispatched with those three named as
its reason, and with the four security properties the SPEC's NFR section says this refactor must not
weaken: path containment through `realpath` + `commonpath`, the shell-free `--notify` argv boundary,
exclusive-create ownership of the state file, and fail-closed control results.

## Two things that are security-relevant and are *not* on the list

Recorded so the gap is visible rather than silently absorbed:

- **Path containment** moved from `__main__._resolve_feature` to `protocol.resolve_feature`. It is
  the diff's highest-risk change and no trigger word names it — "public api" is what pulled the
  reviewer in, and containment came along because it lives in the same file. The trigger list is
  about the *subject matter* a change touches, not about where its risk actually is.
- **The broad `except Exception` around `loop.run()`** was carried over verbatim from the CLI. It
  is not new, and not a trigger.

Neither observation licenses inventing a second trigger list. Both were handed to the reviewer as
explicit hunting instructions instead, which is the honest way to cover them without changing a rule
this feature promised not to change.
