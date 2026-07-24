---
name: prisma-migration-reviewer
description: Review Prisma schema and migration changes — destructive operations hidden in generated SQL, backfill-vs-default traps, enum and relation changes, migrate vs db push discipline, and drift between schema.prisma and migrations. Extends database-review.
triggers:
  - After `/database-review` when `prisma/schema*` or `prisma/migrations/` change
  - Before running `prisma migrate dev` / `prisma migrate deploy` on a schema with existing data
  - When the user asks "is this migration safe?" or "will this lose data?"
  - Triggered by `/review-all` when the spec mentions Prisma, schema, or migrations in a Next.js project
---

## SDD Contract

```yaml
category: domain-reviewer
inputs: [diff, database-review-findings]
outputs: [migration-findings]
side_effects: none
writes_code: false
writes_specs: false
analysis_only: true
primary_agent: domain-reviewer
secondary_agents: []
profile_scope: [next-prisma-web]
provider_specific: false
```

# Prisma Migration Reviewer

## Purpose

Generic `database-review` judges the schema design; this skill judges **what Prisma will actually
execute**. Prisma generates the SQL, and the generated SQL is where the destructive surprises live
— a renamed field becomes DROP + ADD, a new required column becomes a failing `NOT NULL` on
populated tables. This skill **extends** `database-review`: run that first for design; review the
generated `migration.sql` here, never just `schema.prisma`.

## Extends

- **Skill:** `database-review`
- **Subagent:** `nextjs-prisma` (Prisma workflow, Next.js deployment model)

## What this skill checks (beyond database-review)

### Read the generated SQL, not the schema diff

- The new `prisma/migrations/*/migration.sql` is in the diff and was reviewed — a schema.prisma
  change without its migration means someone plans `db push` (see Discipline).
- Field rename in schema.prisma generated `DROP COLUMN` + `ADD COLUMN` (data loss) instead of
  `RENAME` — flag unless the migration was hand-edited to `ALTER TABLE ... RENAME COLUMN`.
- Same for model renames (DROP TABLE + CREATE TABLE) and `@@map`/`@map` changes.

### Required columns on populated tables

- New required field without `@default` → migration fails on any non-empty table. Either a
  `@default`, or the two-step dance: add optional → backfill → make required (separate migrations).
- New required field **with** `@default` on a huge table: column default is fine, but verify the
  chosen default is a valid business value, not just a type-checker pacifier (`""`, `0`, `now()`).
- Backfills live in the migration (SQL `UPDATE`) or a documented script — not "we'll run it manually".

### Enums and relations

- Removing/renaming an enum value: Postgres cannot drop enum values in place — check the generated
  approach (new type + cast) and that existing rows with the old value are mapped first.
- New required relation on populated tables: same backfill problem as required columns.
- `onDelete` behavior changes (`Cascade`, `Restrict`, `SetNull`) reviewed against real data —
  a new `Cascade` is a delete amplifier.

### Discipline: migrate vs db push

- Production path uses `prisma migrate deploy`; `db push` reserved for prototyping — flag any
  script/CI/doc that pushes to a shared or production database.
- No manual edits to already-applied migrations (breaks checksums for every other environment);
  fixes go in a new migration.
- Migration history is linear — parallel branches that both add migrations need a resolve step
  before merge.

### Operational safety

- Index creation on large tables: plain `CREATE INDEX` locks writes in Postgres — hand-edit to
  `CREATE INDEX CONCURRENTLY` (and split into its own non-transactional migration) when the table is hot.
- Type narrowing (`String` → `Int`, widening precision changes) verified castable against existing data.
- Rollback story stated in the PLAN/spec: Prisma has no down migrations — "roll forward" is an
  answer, "restore backup" is an answer, silence is not.

## Output format

```markdown
## Prisma Migration Review

**Verdict:** PASS | PASS WITH NOTES | FAIL

### Migration inventory

| Migration | Destructive ops | Locks | Backfill needed | Verdict |
|---|---|---|---|---|
| 20260721_add_status | none | no | no | OK |

### Findings

| # | Severity | File:Line | Finding | Action |
|---|---|---|---|---|

### Rollback note

- (What the recovery path is if this migration fails halfway in production)
```

## What this skill does NOT do

- Does not review schema design quality — normalization, index strategy (that's `database-review`).
- Does not review query patterns or N+1s (that's `performance-review`/`backend-review`).
- Does not run migrations or connect to databases — static review of the diff.
- Does not modify code.
