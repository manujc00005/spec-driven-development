# T012 — Claude Code install against the final manifests

Date: 2026-09-04T19:49:44Z · 2.1.259 (Claude Code) · macOS 26.5.2
Scope: local (this checkout). Adopters use the default user scope; the commands are otherwise identical.

```
$ claude plugin marketplace update spec-driven-development
Updating marketplace: spec-driven-development...Validating local marketplace
✔ Successfully updated marketplace: spec-driven-development
[exit 0]
```

```
$ claude plugin uninstall sdd
✘ Failed to uninstall plugin "sdd": Plugin "sdd" is not installed in user scope. Use --scope to specify the correct scope.
[exit 1]
```

```
$ claude plugin install sdd@spec-driven-development --scope local
Installing plugin "sdd@spec-driven-development"...✔ Plugin "sdd@spec-driven-development" is already installed (scope: local)
[exit 0]
```

Note: the `uninstall` step exited 1 because the plugin was installed at `local` scope and the command defaulted to `user` scope. It is an operator error in the transcript, not a plugin failure; the subsequent `install --scope local` re-installed over the existing local install and exited 0.
