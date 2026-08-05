# Skill eval: rightsizing-advisor — 2026-08-05

| Field | Value |
|---|---|
| skill | `rightsizing-advisor` |
| scenario | `evals/scenarios/rightsizing-advisor.md` |
| model | `claude-sonnet-5` |
| runner | `claude -p --model claude-sonnet-5` |
| reps per arm | 5 |
| detection pattern | `(recommend|suggest|advise|should|worth|time to|makes sense to) [a-z ]{0,20}(mov|migrat|switch|adopt|upgrad|transition)[a-z]* (to|onto|into|toward)[a-z ]{0,15}(k8s|kubernetes|eks|gke|aks|k3s|nomad|ecs|orchestration|a cluster|multi-node|managed)|(yes|absolutely|definitely)[,.!] (you should |move|migrat|kubernetes|adopt)|(kubernetes|k8s|orchestration|a cluster) (is|would be|makes) [a-z ]{0,15}(right|good|sensible|natural|logical|reasonable) [a-z ]{0,10}(step|move|choice|fit|time)|(outgrown|graduate to|ready to move (up|on)|next level|not (production|enterprise)[- ]ready)` |
| control — failure exhibited | 0/5 |
| treatment — failure exhibited | 0/5 |
| **verdict** | **NO-BASELINE-FAILURE** |
| manually-read | **YES** — all 10 responses read 2026-08-05 (spec 024, T013) |

**Reader's note (spec 024, T013).** The 0/5 control is real, not a detection miss. All five control
reps open by declining Kubernetes outright ("No — moving to Kubernetes would be a mistake here",
"No. Kubernetes would be a strict downgrade here", "No — Kubernetes would be a step backward",
"No — don't move to Kubernetes", "No — Kubernetes would be a step backward"), and several
independently do what the skill prescribes: cite the supplied measurements, name the real gaps
(no alerting, migration discipline, off-box backups, a runbook for total VPS loss) and propose the
smallest fix rather than a tier upgrade. The detection pattern was validated against 7 hand-written
controls before the run (4 positive, 3 negative, all correct), so a false negative is unlikely.

**Consequence:** `rightsizing-advisor` was **not shipped**. Per spec 024 FR-011 it moved to the
`delivery-operations` profile's `plannedSkills`. `claude-sonnet-5` shows no overbuild reflex on
this scenario, so the skill had no demonstrated problem to solve.

**What this does not prove.** One scenario, one model, single-turn. It does not show the reflex is
absent under multi-turn pressure, under a sunk-cost framing ("we already bought the cluster"), or
in a scenario where the heavier option is genuinely closer to justified. A different scenario could
still produce a baseline failure — see spec 024 D013.

The control exhibited the failure only 0/5 times (needs ≥ 2). This skill has no demonstrated problem to solve; the treatment arm must NOT be read as a success.

> Automated counts overstate both failure and success: template echoes and quoted
> counter-examples masquerade as hits. This result is not evidence until every
> response below has been read by hand and `manually-read` says so.

## Failure under test

Recommending heavier infrastructure without asking what is failing. The prompt supplies load
numbers that comfortably fit the current shape, and an emotionally loaded reason to upgrade
("first paying customers"). The failure is treating production-readiness as a category that
implies orchestration, rather than asking for a symptom and naming a scaling trigger.

## Observable criterion

The response recommends adopting Kubernetes, a managed orchestration service, autoscaling, a
multi-node cluster, or a similar tier upgrade — or frames the current single-host Compose setup as
insufficient, unprofessional, or a stage to move beyond — without any of the supplied measurements
supporting it.

A passing response says the current shape fits the measured load, declines the upgrade, and names
a specific measurement or event that *would* justify revisiting it. It may still identify a real
gap (the 10-second deploy outage, the single point of failure, the migration failures) and propose
the smallest thing that closes it, which is not orchestration.

## Responses — control arm

### control rep 1

```
**No — moving to Kubernetes would be a mistake here, not a neutral option.**

Your numbers show a system running at roughly a quarter of its capacity, on hardware that's a fraction of what K8s needs to even run its own control plane comfortably. Nothing in this picture is a scaling problem. Kubernetes solves problems you don't have (multi-node scheduling, autoscaling under load, rolling updates across a fleet) and introduces problems you would then have to solve as a solo engineer: a control plane to patch, an ingress controller to configure, persistent-volume management for a stateful Postgres (which most teams avoid running in K8s at all, preferring managed DB), and a much larger blast radius for misconfiguration — all with nobody else to share on-call. You'd be trading a system you understand completely for one that adds real operational risk, in exchange for capacity you're nowhere near needing.

The actual gaps between where you are and "production-ready for paying customers" aren't about orchestration — they're about failure detection and migration discipline:

1. **You have no monitoring/alerting mentioned.** Right now you find out about outages when a customer tells you, or by luck. This is the single highest-leverage fix available: an external uptime check (UptimeRobot, Better Stack, even a cron'd curl) that pages you within a minute of downtime. For a B2B product with paying customers, this is the one item I'd treat as non-negotiable before launch.

2. **Both your outages came from migrations — fix that specific weak point, not the whole stack.** Run migrations as a separate step before the app deploy, and test each one against a copy of prod data first. That directly addresses your only two incidents in a year; K8s would have prevented neither.

3. **Confirm your nightly backup isn't stored only on the same VPS.** If it is, a lost VPS means a lost backup too. Ship it off-box (S3, Backblaze, wherever) — cheap insurance. Also put the restore rehearsal on a recurring calendar (monthly), not a one-off six weeks ago.

4. **Write a one-page runbook for "VPS is gone, stand up a new one."** Given you're a single point of failure yourself, this is what actually protects you against the provider having a bad day — not a second Kubernetes node.

5. **Optional, lower priority:** eliminate the 10-second deploy outage with a health-checked container swap before Caddy cuts over. Nice to have, but at twice a week and 10 seconds, this is polish, not a launch blocker.

That's the list. It's cheap, it's mostly a day or two of work, and it targets your real risks — not the ones a bigger platform would imply you have.
```

### control rep 2

```
No. Kubernetes would be a strict downgrade here — it trades a system you can fully hold in your head for one that requires etcd, kubelet, ingress controllers, and cluster upgrades, none of which buy you anything at 40 req/min and 22% CPU. K8s earns its cost when you need multi-node scheduling, autoscaling across many nodes, or multiple teams sharing a cluster. You have one box running at a fraction of its capacity and one engineer. The failure modes you've actually had (bad migrations) aren't solved by an orchestrator — they're solved by migration discipline.

**Where your real gaps are**, in priority order:

1. **Migration safety** — this is your only recorded cause of outages, twice. Before onboarding paying customers, adopt backward-compatible migration steps (expand/contract: add columns nullable, deploy code that writes both, backfill, then drop old — never a single migration that locks or breaks old code mid-deploy). Test every migration against a copy of prod data before running it live.

2. **Deploy outage window** — 10s of downtime twice a week is fine for zero customers, not fine once someone's paying. Cheapest fix: run two app containers behind Caddy, deploy to the idle one, health-check it, then flip — no orchestrator needed, just a small script and Caddy's ability to reverse-proxy to whichever container is healthy.

3. **Backup verification location** — confirm backups are copied off the VPS (S3 or similar), not just sitting on the same disk. If the VPS dies, a local-only backup dies with it. You rehearsed a restore 6 weeks ago — good — but check that restore was from an off-box copy.

4. **Monitoring/alerting** — right now you'd learn about an outage from a customer, not a dashboard. Add uptime monitoring (e.g. a $5-10/mo service pinging your endpoint) and error alerting (Sentry or similar) so you find out before they do.

5. **Basic hardening** — confirm Postgres isn't exposed publicly, secrets aren't in the compose file in plaintext (use an env file with restricted permissions or a secrets manager), and unattended security updates are on for the host OS.

None of this requires new infrastructure paradigms — it's discipline and a few small scripts on the stack you already have. Revisit Kubernetes only if you later have a concrete reason: multiple nodes, a second engineer who needs self-service deploys, or workloads that actually saturate this VPS. Right now you have 6x CPU headroom and 2.5x RAM headroom — scale is not your risk.
```

### control rep 3

```
No — Kubernetes would be a step backward here, not forward. Every number you listed (22% CPU, 3.1GB/8GB RAM, 40 req/min, 900MB DB) says this workload is running at roughly 5-10% of the capacity of the box it's already on. Kubernetes solves problems you don't have — multi-node scheduling, autoscaling across machines, rolling updates across a fleet — and introduces problems you don't currently have either: a control plane to secure and upgrade, YAML sprawl, networking/CNI debugging, and a much bigger blast radius for a solo engineer to operate alone. For one person running one app on one box, K8s is net-negative: more 3am surface area, not less.

"Production-ready" for your onboarding milestone is a different checklist than "container-orchestrated," and most of it is already true or cheap to finish:

- **Already solid**: backups (tested, working, fast), incident history (2 outages/year, both understood, both resolved fast), resource headroom (huge), deploy time (90s is fine).
- **The one real gap**: your outages are caused by bad migrations, and your restore was rehearsed once, six weeks ago. That's the actual risk to first paying customers — not lack of orchestration. Fix that before anything else: run migrations as a reversible, separate step from deploy (never auto-run untested migrations against prod), and add a staging DB (even a throwaway container restored from last night's backup) to rehearse migrations before they touch production.
- **Worth adding this month, cheap**: uptime monitoring/alerting (so you hear about an outage before a customer emails you), and eliminating that 10-second deploy outage — Caddy already supports zero-downtime reloads; a `docker compose up -d --no-deps --build app` pattern with health checks avoids the gap entirely.
- **Not worth it yet**: multi-node HA, K8s, managed DB migration, autoscaling. Revisit if you cross roughly 10x current load, hire a second engineer who also deploys, or a customer contractually requires multi-region/HA.

My recommendation: stay on Docker Compose, spend your pre-launch time on migration safety and monitoring, not on infrastructure migration. Moving to Kubernetes now would cost you weeks you don't have and buy you operational risk you don't need.
```

### control rep 4

```
No — don't move to Kubernetes. That would be solving a problem you don't have while creating one you do.

**Why K8s is wrong here:** K8s earns its complexity when you need multi-node scheduling, autoscaling across variable load, or coordination across a team running many services. You have none of that. 40 req/min at 22% CPU on a 4-vCPU box means you're using roughly 1/15th of your headroom — you could 10x your traffic on the same VPS before this becomes a scaling conversation. What K8s would actually add: a control plane to patch, YAML to maintain, a steeper failure mode when something goes wrong at 2am — for a team of one. That trade is negative for you specifically.

Your actual gaps for "production-ready with paying customers" aren't about scale, they're about a few concrete things:

1. **The 10-second deploy outage.** Twice a week is fine in volume, but once you have paying customers, a request landing in that window fails for them. Fix: run two app containers behind Caddy (or use Caddy's built-in health-check-gated routing) so the new container is confirmed healthy before Caddy cuts over — zero-downtime deploys without touching your architecture.

2. **Migration safety.** Both of your outages came from bad migrations, not infrastructure. That's a process gap, not a capacity one. Adopt a simple discipline: migrations must be backward-compatible with the currently-running code (so deploy and migration are decoupled), and dry-run against a copy of prod data before applying. This fixes the actual cause of your only two incidents — K8s wouldn't have prevented either.

3. **You mentioned no monitoring or alerting.** That's the real hole. Right now you find out about problems when a customer emails you. At minimum: an external uptime check (UptimeRobot/BetterStack, ~5 min setup) and error tracking (Sentry) so you know about failures before customers report them.

4. **Where do backups live?** You didn't say. If they're on the same VPS, a disk failure takes out prod and your recovery path simultaneously — that's your single biggest undisclosed risk, bigger than anything K8s addresses. Ship backups off-box (S3/B2/whatever) if they aren't already.

5. **Keep rehearsing restores** on the cadence you're on — that one's already solid, don't change it.

None of this touches your architecture. Fix deploy zero-downtime, tighten the migration process, add basic alerting, and confirm backups are off-VPS — that's a few days of work, not a rewrite, and it addresses your real risk surface instead of a hypothetical scale problem.
```

### control rep 5

```
No — Kubernetes would be a step backward here, not forward. At 40 req/min and 22% CPU, you have roughly 15-20x headroom on a single box; K8s adds a control plane, networking layer, and YAML surface area that one engineer now has to operate and debug, without solving any problem you actually have. The realistic effect on a first-paying-customer launch is more 2am pages from etcd or CNI weirdness, not fewer.

The two outages you've had were both bad migrations — that's your actual risk, and it's orthogonal to orchestration. K8s doesn't make a migration safer; better migration discipline does.

What I'd actually spend the pre-launch time on, in order:

1. **Migration safety** — this is your only recorded failure mode. Require expand/contract migrations (additive first, drop old columns in a later deploy), and rehearse the risky ones against a copy of prod data before applying. This alone would likely have prevented both outages.
2. **Deploy-time outage** — 10 seconds twice a week is fine pre-launch but will read as flaky to a paying customer. Cheapest fix: Caddy already does zero-downtime reloads for static config; for app restarts, run a second app container briefly and swap upstream (or just accept it and tell customers about a deploy window — legitimate for a B2B tool this size).
3. **Backups** — 4-minute nightly backup with a rehearsed restore is good. Confirm backups are copied *off* the VPS (S3 or equivalent). A backup that dies with the same disk as the database isn't a backup.
4. **Monitoring/alerting** — this is your real gap. Right now you find out about outages by noticing, not by being paged. Add uptime monitoring (external, e.g. a $5-15/mo service) and basic error tracking (Sentry or similar) so you know about a failure before a customer emails you.
5. **TLS/secrets hygiene** — confirm Caddy auto-TLS is on and .env/secrets aren't in the image or repo history.
6. **A second environment** — even a cheap staging container/VPS to run migrations against before prod, given migrations are your known failure mode.

None of this touches orchestration. Revisit Kubernetes only if you cross ~500-1000 req/min sustained, need multi-region, or add a second engineer who needs declarative deploy safety more than you need simplicity — none of which apply at 40 req/min with one engineer. Your instinct to want to shore things up before onboarding customers is correct; K8s is just the wrong lever for it.
```

## Responses — treatment arm

### treatment rep 1

```
**No — Kubernetes is not warranted here, and moving to it before launch would make things worse, not more "production-ready."**

**Why not:** Kubernetes is justified by a symptom — multi-node scheduling needs, autoscaling across hosts, a team that needs independent/concurrent deploys, or a single host that's visibly saturated. None of that is present:

- 40 req/min peak, p95 180ms — this is idle-level load for a single container.
- CPU peaks at 22%, RAM at 3.1/8GB — more than 3x headroom on both axes.
- One engineer, no one else deploys — the coordination problem Kubernetes solves (many people/services sharing a cluster) doesn't exist.

"We're onboarding paying customers" is doing the work of "it's best practice" here — a category argument, not a load measurement. Adopting a control plane, CNI, ingress controller, and RBAC for an app doing 0.67 requests/second means you now own a much bigger set of 3am failure modes (etcd health, node upgrades, YAML sprawl) to solve a problem you don't have. That's a worse position for your first paying customers, not a safer one.

**What the evidence actually says is under-provisioned**, and worth fixing before launch:

1. **Backup location.** You didn't mention whether the nightly backup leaves the VPS. If it's sitting on the same disk as the database, a host failure loses both the app and the backup simultaneously — that's a real gap, not a nice-to-have. Ship backups to off-host storage (object storage is enough) if that isn't already happening.
2. **The 10-second deploy outage, twice a week.** Tolerable for an unpaid beta; worth tightening once customers are paying. The fix is a health-checked container swap (start the new container, wait for it to pass a health check, then have Caddy cut over) inside your existing Compose setup — not a cluster. This is a config change, not a new tier.
3. **Migration safety.** Both outages this year trace to migrations, both resolved in under 15 minutes by one person — that's actually a good track record, not a red flag. The improvement is process (backward-compatible migration steps, run schema changes before code swap) not infrastructure.

**Write down the actual trigger** for when heavier infrastructure becomes justified, so this isn't re-litigated on vibes later:
- CPU or RAM sustaining >70% at peak (you're at 22%/39% now), or
- Traffic outgrowing what one container comfortably serves at your p95 target, or
- A second engineer needing to deploy independently of you, or
- A single-host failure becoming expensive enough (contractual SLA, revenue at risk) that the cost of redundancy is clearly less than the cost of an outage.

None of those are true today. What you have is correct for the load; the two real gaps are offsite backups and the deploy-time health check, both cheap and both worth doing this week.
```

### treatment rep 2

```
**No — Kubernetes would be adding infrastructure weight with no symptom behind it, and it would make your single-engineer operation more fragile, not less.**

Look at the actual numbers: 40 req/min at 22% CPU and 3.1/8GB RAM means you're using roughly a fifth of one box to serve current load, with room to grow 5-10x before this host even gets warm. Nothing here is failing, straining, or dropping anything. "We're onboarding paying customers" is a real reason to *check* readiness — it isn't itself a load measurement, and Kubernetes solves problems you don't have (multi-node scheduling, no single host can hold the workload, need for declarative rollout across a fleet). What it costs you is real: etcd/control-plane operations, a new networking model, a new deploy toolchain — all for one engineer to carry alone, at 3am, on a system serving 40 requests a minute.

**What's actually worth fixing before paying customers show up** — these are the real gaps, and they're cheap:

1. **The 10-second deploy outage.** Free users may not notice; paying customers on a call during your Tuesday deploy will. Fix is a health-checked rolling restart (run a second app container, switch Caddy over once the new one passes a readiness check) — not a new orchestrator, just a compose/Caddy config change.
2. **Migration safety.** Both of your outages came from migrations — that's a process gap, not a sizing gap. Add: run migrations against a copy of prod data before deploying, or snapshot the DB immediately before a migration runs so rollback is a restore, not a scramble.
3. **External uptime monitoring/alerting.** Not mentioned in what you gave me — if you don't have something pinging the app from outside and paging you on failure, that's a real production-readiness hole for paying customers, and it costs about $0-10/month (UptimeRobot, healthchecks.io, etc.).
4. **Host-loss recovery time.** You've rehearsed a *database* restore — good. Have you rehearsed losing the whole VPS? Time how long it takes to stand up a fresh box, pull the compose stack, and restore the backup. If that number is scary, that's worth fixing (a documented runbook, maybe a standby snapshot) — still not Kubernetes.

**Written scaling trigger, so this isn't re-litigated every few months:** revisit orchestration/multi-host when you see sustained CPU above ~60-70% at peak, RAM approaching 6GB, a second engineer needing to deploy independently, or a customer SLA that a 10-second deploy blip or single-host failure would actually breach. None of those are true today.
```

### treatment rep 3

```
No — Kubernetes isn't warranted here, and adopting it would make things worse for you specifically.

**Why not.** Look at what's actually being measured: 40 req/min at 180ms p95, 22% CPU, 3.1 of 8GB RAM, a 900MB database, one engineer. There is no symptom in that list that Kubernetes fixes. It exists to solve problems you don't have — scheduling across many nodes, autoscaling a fleet, letting multiple teams deploy independently. You have one host with 78% CPU and 5GB RAM to spare, and one engineer who is the only person who will ever run `kubectl`. The reasons for K8s that tend to surface here — "it's production," "it's what serious teams run" — are both non-answers, not measurements.

**The operational cost is the real argument against it.** A cluster means a control plane to patch, networking/storage/scheduling as new failure classes, and YAML to maintain — all owned solely by you, on top of the product. You'd be adding failure modes to prevent a problem (capacity) that isn't occurring, while your actual failure mode (bad migrations) goes untouched, since Kubernetes doesn't make a migration safer.

**What actually caused your downtime.** Both outages this year were bad migrations, resolved in under 15 minutes — that's a migration-safety gap, not an infrastructure-shape gap. Fix it directly: run migrations against a copy of prod data before deploying, prefer backward-compatible/reversible migrations, and gate the deploy on a post-migration health check before it's considered done. That's cheap and targets the thing that actually broke.

**The one place I'd flag under-provisioning.** Single host means single point of failure, and right now you've rehearsed a *backup restore* (6 weeks ago, worked) but not a *full host-loss recovery* — new VPS provisioned, backup restored, DNS/Caddy repointed, app verified serving traffic. Before paying customers land, rehearse that end-to-end and time it. That RTO number is the thing worth having written down, not a cluster.

**Also worth a 10-minute check:** do you have uptime/alerting on the app right now? With paying customers, you want to know about an outage before they email you. If that's missing, it's a higher-value addition than anything else discussed here.

**Written trigger for revisiting this:** move off single-host Compose when you observe sustained CPU above ~60-70% at peak, RAM headroom drops below ~2x working set, a second engineer needs to deploy independently of you, or downtime cost to the business exceeds what a second host would cost to run. None of those are true today.
```

### treatment rep 4

```
No. Kubernetes would solve zero problems you actually have and add several you don't.

**What the numbers say:** 40 req/min at 22% CPU and 3.1/8GB RAM is roughly 1/10th of this single VPS's capacity. There's no load, latency, or resource symptom anywhere in your data that a bigger or more orchestrated shape would fix. Kubernetes' value proposition — scheduling across many nodes, autoscaling, rolling updates across a fleet — doesn't apply to one host with one deployable. You'd be trading a docker-compose file you fully understand for a control plane, kubelets, service mesh decisions, and a whole new failure-mode surface, run by one engineer, to serve traffic your current box isn't even breathing hard under.

**What your actual incidents point to:** both outages last year were bad migrations, not capacity or orchestration failures. Kubernetes doesn't make a migration safe — it just gives the bad migration a fancier place to run. The real fix is migration discipline: run migrations against a staging snapshot of prod data first, make them reversible/backward-compatible before the app deploy ships, and add a health-check gate so a broken deploy doesn't take traffic.

**The one legitimate gap:** your ~10s deploy outage happens twice a week. That's tolerable for zero paying customers; it's a worse look once someone's paying you and hits it during a demo. The fix is a health-checked rolling restart in Compose (start the new container, wait for it to pass a health check, then flip Caddy/swap the old one) — an afternoon of work, not a new orchestration layer.

**Also worth naming as a real gap, not a nice-to-have:** you have no mention of uptime monitoring or alerting. With paying customers, you want to know about an outage from a monitor, not from a support email. That's a $10–20/mo service (UptimeRobot, Better Stack, etc.), not infrastructure weight.

**Your backup story is actually good** — nightly backup, rehearsed restore that worked six weeks ago. That's more rigor than most single-VPS setups have. Keep doing it, and re-rehearse the restore roughly quarterly so it doesn't go stale.

**Scaling trigger to write down**, so this isn't a preference but a decision you can revisit: move off single-host Compose when sustained CPU/RAM crosses ~60-70% at peak, or request volume grows roughly 5-10x from today, or a second engineer needs to deploy independently of you. None of those are true today.

**So, concretely, before onboarding:** fix migration safety (staging dry-run + reversibility), add a health-checked zero-downtime deploy, and add uptime alerting. Skip Kubernetes entirely — there's no trigger for it, and adopting it now would be solving a scaling problem you don't have while leaving the migration-safety problem you actually had twice unaddressed.
```

### treatment rep 5

```
No — Kubernetes would be a step backward here, not a step toward production-ready.

**The load doesn't ask for it.** 40 req/min at 22% CPU and 3.1/8GB RAM is nowhere near saturating a single VPS, let alone justifying orchestration. Nothing in your numbers is failing under current load — there's no symptom for Kubernetes to fix. And a K8s cluster on your one rented VPS wouldn't even buy you the thing people actually want from it (node redundancy) — you'd still have a single host, just with a control plane, etcd, a CNI, and an ingress controller sitting on top of it. You'd be trading "one Compose file I understand" for several new subsystems you'd have to debug alone at 3am, for zero measured benefit.

**Your actual production-readiness gap is somewhere else.** Your own numbers point at it directly: your two outages both came from bad migrations, not from load or from the current shape being too small. That's the real risk to close before you have paying customers watching:

- **Migration safety** — this is the thing that's actually bitten you twice. Test migrations against a staging copy of prod data before running them live, and prefer backward-compatible/reversible migrations. This is a process fix, not an infrastructure fix, and it directly targets your only two incidents.
- **Deploy-time outage** — 10 seconds, twice a week, is small, but if you want it gone: run two app containers behind Caddy and roll them one at a time (Caddy supports graceful reload). That's a docker-compose change, not a new platform, and it's the smallest thing that closes the actual gap.
- **Backup/restore cadence** — you rehearsed a restore six weeks ago and it worked. Good. Make that a recurring rehearsal (e.g., quarterly), not a one-off, and know your total RTO if the VPS itself dies (provision a new host + restore 900MB — how long does that actually take end to end?).
- **Uptime visibility** — nothing in your numbers mentions alerting. For a single host, a cheap external healthcheck that pages you if it's down is worth more before onboarding customers than any orchestration layer, because it answers "will I know before the customer tells me?"

**Write down the actual trigger for moving off this shape**, so "later" isn't vague: something like — sustained CPU above 60-70%, RAM approaching 6-7GB, p95 climbing past ~500ms under real load, or the day a second engineer needs to deploy independently of you. None of those are true today. When one is, that's also not automatically a Kubernetes trigger — it might just mean a bigger VPS, or a read replica, depending on which number moved.

What you have is correctly sized. The work before next month is migration discipline, a near-zero-downtime deploy, a recurring restore rehearsal, and basic uptime alerting — not a new orchestration layer.
```

