# T013 — Codex install from the local checkout

Date: 2026-09-04T19:49:50Z · codex-cli 0.152.1 · macOS 26.5.2

> Redacted 2026-09-05 (public release): home paths rewritten to `~`, unrelated marketplaces elided.
> Commands, exit codes and every line about `sdd@spec-driven-development` are unchanged.

```
$ codex plugin marketplace add ~/Proyectos/spec-driven-development
Added marketplace `spec-driven-development` from ~/Proyectos/spec-driven-development.
Installed marketplace root: ~/Proyectos/spec-driven-development
[exit 0]
```

```
$ codex plugin add sdd@spec-driven-development
Added plugin `sdd` from marketplace `spec-driven-development`.
Installed plugin root: ~/.codex/plugins/cache/spec-driven-development/sdd/0.1.0
[exit 0]
```

```
$ codex plugin list
[… 207 lines elided on 2026-09-05 before the repository went public: the other marketplaces on the
 maintainer's machine and their plugins. They are not the plugin under test. …]

Marketplace `spec-driven-development`
~/Proyectos/spec-driven-development/.claude-plugin/marketplace.json

PLUGIN                       STATUS              VERSION  PATH                                         
sdd@spec-driven-development  installed, enabled  0.1.0    ~/Proyectos/spec-driven-development
[exit 0]
```

```
$ codex plugin marketplace list
MARKETPLACE              ROOT
openai-primary-runtime   ~/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime
openai-bundled           ~/.codex/.tmp/bundled-marketplaces/openai-bundled
openai-curated           ~/.codex/.tmp/plugins
spec-driven-development  ~/Proyectos/spec-driven-development
[exit 0]
```

## Skill-execution attempt (`codex exec`, 2026-09-04T20:01:58Z)

Asked for beyond AC-007 by `/qa-review`: does a Codex session actually load the plugin's skills? Run in the disposable project with `-s read-only`:

```
$ codex exec -C /tmp/sdd-e2e-x5x1 -s read-only 'Using the spec-status skill provided by the sdd plugin, report what that skill would output for this directory. ...'
OpenAI Codex v0.152.1
--------
workdir: /tmp/sdd-e2e-x5x1
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: xhigh
reasoning summaries: none
session id: 01a06e02-9f30-7c00-aef7-d5ae613d512d
--------
warning: Skill descriptions were shortened to fit the skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest.
hook: SessionStart
hook: SessionStart Completed
hook: UserPromptSubmit
hook: UserPromptSubmit Completed
ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 7th, 2026 9:35 PM.
ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 7th, 2026 9:35 PM.
```

Two facts, one gap. (1) The skills context was built with the plugin's skills in it: `warning: Skill descriptions were shortened to fit the skills context budget. Codex can still see every skill` — 72 additional skills exceed Codex's per-session description budget. (2) Codex ran its SessionStart and UserPromptSubmit hooks. The gap: the model call failed with `You've hit your usage limit ... try again at Sep 7th, 2026`, so no skill was executed. AC-007 (install exits 0) stands as written; skill execution on Codex is unobserved because of quota, not because of the plugin, and is recorded as such in DECISIONS.md D012.
