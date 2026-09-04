# Security review — spec 044

Date: 2026-09-04 · reviewer: `security-reviewer` agent (framework core profile), delegated by `/security-review`

## Verdict returned: Partial — no Critical/High; one confirmed Medium, two potential Medium, one Low

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| SEC-044-001 | Medium, confirmed | `check_plugin_wiring` compared `(event, matcher, hook-name, timeout)` with the name found by substring; a chained command or an absolute path with the same basename passed as equivalent (`scripts/check-consistency.sh`, `_wiring_tuples`). Tests only mutated hook presence. | **Fixed (D013):** per-side canonical-shape `fullmatch`; `type` and `statusMessage` added to the tuple; two new suite cases (`plugin-wiring-chained-command`, `plugin-wiring-absolute-path`). |
| SEC-044-002 | Medium, potential | Plugin hooks run project-controlled code (`npx eslint --fix`, `npx prettier`, `npx tsc`, `./mvnw`/`./gradlew`) in every enabled project; at user scope that includes freshly cloned untrusted repos. | **Documented (D013):** "What you are trusting" caveat, `--scope project` recommended for untrusted checkouts. |
| SEC-044-003 | Medium, potential | In-place loading executes whatever branch the marketplace clone has checked out, e.g. a contributor's PR branch under review. | **Documented (D013):** separate fast-forward-only clone or GitHub source; branch switches take effect next session. |
| SEC-044-004 | Low | No trust statement for the GitHub install path. | **Documented (D013):** what is executed, with whose privileges, and how updates arrive. |

Classes checked clean by the agent: information exposure (manifests carry only public URLs and
relative paths), grants (same ten hooks, `${CLAUDE_PLUGIN_ROOT}` quoted), injection/path traversal in
the check (fixed paths under `repo_root`, `json.load` only), supply chain (no dependency, lockfile or
CI change), privacy (no personal data).

Residual noted by the agent and left open: whether the harness pins plugin versions or verifies the
cache is harness behaviour outside this repository.
