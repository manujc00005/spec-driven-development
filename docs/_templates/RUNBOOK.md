# Runbook: <system or service name>

> Copy this template into your project as `docs/RUNBOOK.md` and fill it in.
> This is the **single ordered procedure** for deploying and recovering this system.
>
> Its one job is to be the only place the procedure lives. A procedure split across an
> `infra/` README, a checklist at the end of a closed spec, and an audit note cannot be
> followed — it has to be reconstructed, under pressure, by whoever is on call.
> `/deployment-review` reports that fragmentation as a High-severity finding.
>
> Companion file: `docs/DEPLOYMENT.md` describes the **topology** — what gets built, where
> it runs. This file describes the **procedure** — what to do, in what order. Keep them apart.

**Last followed end to end:** <YYYY-MM-DD> by <name>
**Last rollback rehearsed:** <YYYY-MM-DD> by <name> | never
**Last restore rehearsed:** <YYYY-MM-DD> by <name> | never

> An undated "yes" counts as *written but untested* in `/release-readiness`. Dates are the
> whole value of these three lines.

## Who can run this

| Role | Who | Has access to |
|---|---|---|
| Deployer | | SSH / CI trigger / registry |
| Secret holder | | password manager / vault |
| Escalation | | |

## Prerequisites

Everything that must be true **before** step 1. If any of these is false, stop.

- [ ] <e.g. DNS record resolves to the host>
- [ ] <e.g. reverse proxy is already running — it must be up *before* provisioning, not after>
- [ ] <e.g. TLS certificate issued and not expiring within 30 days>
- [ ] <e.g. secrets present at `<path>`, mode 0600, owned by `<user>`>
- [ ] <e.g. a backup taken within the last 24h, and its restore verified>

## Deploy procedure

> Number every step. State its precondition and how to verify it succeeded. Mark whether it is
> safe to repeat — that is what someone re-running after a failure needs to know.

### Step 1 — <name>

| | |
|---|---|
| **Precondition** | <what must be true> |
| **Command** | `<exact command>` |
| **Verify** | <the observable proof it worked — not "no error", something you can see> |
| **Safe to re-run** | yes / no — <why> |
| **First boot only** | yes / no |
| **If it fails** | <stop / retry / roll back to step N> |

### Step 2 — <name>

<repeat the block>

## What a re-run does

The procedure will die halfway at some point. That is the normal case.

| Died at | Re-running from step 1 will | Safe? |
|---|---|---|
| step 2 | | |
| step 4 | | |

**Steps that are NOT safe to repeat:** <list them, or state "none">
**How to get back to a clean starting state:** <or state that you cannot, which is itself the answer>

## First deployment versus converge

| Step | First deployment only | Safe on every converge |
|---|---|---|
| <create database> | ✅ | ❌ — <what it would overwrite> |
| <apply migrations> | | ✅ |

## Health verification

After a deploy, before declaring success:

- [ ] <check the service is **serving**, not just running — an open port is not enough>
- [ ] <check the thing users actually do, end to end>
- [ ] <check background jobs are still running>

## Rollback

| | |
|---|---|
| **Trigger** | <when to roll back rather than fix forward> |
| **Who decides** | |
| **Time to complete** | |

### Procedure

1. <ordered steps>

### Point of no return

**After <step N / this event>, rollback is no longer possible** because <reason>.
State this even if the answer is "there isn't one" — it is what the operator most needs to know
and is almost never written down.

### Data

- Does rollback cover the database, or only the application?
- <A rolled-back application against a forward-migrated schema is a second outage.>

## Restore from backup

| | |
|---|---|
| **Backup location** | |
| **Encrypted with** | <and where that key lives> |
| **Retention** | |
| **Restore command** | |
| **Time to restore** | |

- [ ] A restore has actually been performed from a real artifact into a usable state.
      <A backup job reporting success proves a file was written, not that it can be read back.>
- [ ] The backup **fails closed** — it errors rather than producing an unencrypted or truncated
      artifact when something is missing.
- [ ] The artifact is not readable by others while it is being written.

## Perimeter

| Service | Reachable from | Bound to | Enforced by |
|---|---|---|---|
| | | | |

> On Linux, Docker inserts iptables rules **ahead of** the host firewall, so a published port is
> typically reachable even when `ufw`/`firewalld` appears to deny it. The binding address is the
> real perimeter. `/container-review` checks this.

## When it breaks

| Symptom | Likely cause | What to do |
|---|---|---|
| | | |

## Known counter-intuitive details

> The knowledge that dies when it is not written down. If something looks wrong but is correct,
> record it here — otherwise someone will "fix" it into an outage.

- <e.g. the bootstrap step must call `localhost`, not the public URL, because DNS does not
  resolve at that point>
- <e.g. this container binds to 127.0.0.1 deliberately; publishing it would bypass the firewall>
