# Scenario corpus — superseded, do not run a sweep against these

The nine scenarios in this directory are **format-conformant but substantively invalid**. They
describe repository state (files, paths, existing code) that the model cannot see, so an agent
runner answers about the mismatch instead of the scenario. Two sweeps built on them were discarded.

See `specs/features/022-skill-evidence-harness/DECISIONS.md` D010 for what went wrong, and
`../README.md` → *Scenarios must be self-contained* for the rule any replacement must follow.

They are kept as the **starting point for spec 023**, whose first task is rewriting them as
self-contained prompts. Until that lands, a sweep run against this corpus produces tallies that
look plausible and mean nothing.
