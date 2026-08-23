#!/usr/bin/env node
/**
 * board.mjs — generates `.sdd-workspace/BOARD.md` by reading every project's specs.
 *
 * Why: a hand-maintained "active work" register goes stale within days and then issues
 * false instructions with full authority. This derives the state instead — the board can
 * only lie if a spec lies, and then the fix belongs in the spec.
 *
 * Deterministic, no LLM: same tree, same output.
 *
 * Usage:  node .sdd-workspace/scripts/board.mjs [--list|--check]
 *         (no flags)  regenerate BOARD.md, one-line summary. For the SessionStart hook.
 *         --list      regenerate and print everything open, grouped, with its blocker.
 *         --check     don't write; exit 1 on real warnings. For CI.
 *
 * Projects: read from `.sdd-workspace/workspace.json` ({"projects": [...]}) if present —
 * an explicit list is a decision, not an inference. Otherwise auto-detect: any top-level
 * directory containing `specs/features/`, plus `.sdd-workspace` itself (cross-repo specs).
 */

import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.env.SDD_WS_ROOT || join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = join(ROOT, ".sdd-workspace", "BOARD.md");

function detectProjects() {
  const cfg = join(ROOT, ".sdd-workspace", "workspace.json");
  if (existsSync(cfg)) {
    const j = JSON.parse(readFileSync(cfg, "utf8"));
    if (Array.isArray(j.projects) && j.projects.length) return [".sdd-workspace", ...j.projects];
  }
  const found = [".sdd-workspace"];
  for (const e of readdirSync(ROOT, { withFileTypes: true })) {
    if (!e.isDirectory() || e.name.startsWith(".")) continue;
    if (existsSync(join(ROOT, e.name, "specs", "features"))) found.push(e.name);
  }
  return found;
}
const PROJECTS = detectProjects();

/**
 * Status vocabulary. `canon` is the normalized state; `bucket` decides placement.
 * Legacy aliases are accepted on purpose: migrating every historical spec to a new
 * vocabulary would be the mass rewrite this tool exists to avoid. They are flagged,
 * not blocked.
 */
const VOCAB = [
  { match: /^in[\s-]?progress\b/i, canon: "In Progress", bucket: "active" },
  { match: /^in[\s-]?review\b/i, canon: "In Review", bucket: "review" },
  { match: /^ready\b/i, canon: "Ready", bucket: "ready" },
  { match: /^draft\b/i, canon: "Draft", bucket: "draft" },
  { match: /^blocked\b/i, canon: "Blocked", bucket: "blocked" },
  { match: /^parked\b/i, canon: "Parked", bucket: "parked" },
  { match: /^aparcada\b/i, canon: "Parked", bucket: "parked", legacy: true },
  // `Merged` is NOT closure: it means "code is in main, liveness not yet verified".
  // By definition it may keep activation tasks open and may carry a Blocked-by.
  { match: /^merged\b/i, canon: "Merged", bucket: "merged" },
  { match: /^live\b/i, canon: "Live", bucket: "closed" },
  { match: /^superseded\b/i, canon: "Superseded", bucket: "closed" },
  { match: /^archived\b/i, canon: "Archived", bucket: "closed" },
  { match: /^done\b/i, canon: "Done", bucket: "closed", legacy: true },
  { match: /^complete/i, canon: "Complete", bucket: "closed", legacy: true },
  { match: /^cerrada\b/i, canon: "Cerrada", bucket: "closed", legacy: true },
  { match: /^entregada\b/i, canon: "Entregada", bucket: "closed", legacy: true },
  { match: /^✅/, canon: "green", bucket: "closed", legacy: true },
];

const BUCKET_ORDER = ["active", "review", "merged", "ready", "draft", "blocked", "parked", "closed"];
const BUCKET_TITLE = {
  active: "In Progress — active work",
  review: "In Review — implemented, pending close",
  merged: "Merged — in main, not verified live (not `Live`)",
  ready: "Ready — planned, not started",
  draft: "Draft — written, not authorized",
  blocked: "Blocked — declared blocked",
  parked: "Parked — deliberately set aside",
  closed: "Closed",
};

const clean = (s) =>
  (s || "").replace(/\*\*/g, "").replace(/[`_~]/g, "").replace(/^[>\-\s]+/, "").trim();

function normalise(raw) {
  const t = clean(raw);
  for (const v of VOCAB) if (v.match.test(t)) return v;
  return null;
}

/**
 * Header extraction, in order of reliability:
 *  0. YAML frontmatter (status:)          2. `## Status` section, first line
 *  1. Canonical block (Estado|Status: /   3. `**Status:**` header line
 *     Blocked-by: / Parent:)              4. fallback: the repo's specs/README.md index
 */
function parseSpec(specPath) {
  const lines = readFileSync(specPath, "utf8").split("\n");
  const out = { estado: null, blockedBy: null, parent: null };

  if (lines[0]?.trim() === "---") {
    const end = lines.slice(1).findIndex((l) => l.trim() === "---");
    if (end !== -1) {
      for (const line of lines.slice(1, end + 1)) {
        const m = line.match(/^\s*(status|estado|blocked-by|parent)\s*:\s*(.+)$/i);
        if (!m) continue;
        const k = m[1].toLowerCase(), v = clean(m[2]);
        if ((k === "status" || k === "estado") && !out.estado) out.estado = v;
        else if (k === "blocked-by") out.blockedBy = v;
        else if (k === "parent") out.parent = v;
      }
      if (out.estado) return out;
    }
  }
  for (const line of lines.slice(0, 40)) {
    const m = line.match(/^\s*(Estado|Status|Blocked-by|Parent)\s*:\s*(.*)$/);
    if (!m) continue;
    const k = m[1].toLowerCase(), v = clean(m[2]);
    if ((k === "estado" || k === "status") && !out.estado && normalise(v)) out.estado = v;
    else if (k === "blocked-by") out.blockedBy = v;
    else if (k === "parent") out.parent = v;
  }
  if (out.estado) return out;

  const i = lines.findIndex((l) => /^##\s+Status\s*$/i.test(l));
  if (i !== -1)
    for (const line of lines.slice(i + 1, i + 8)) {
      if (!line.trim()) continue;
      if (/^#/.test(line)) break;
      out.estado = clean(line);
      return out;
    }
  for (const line of lines.slice(0, 20)) {
    const m = line.match(/^\*\*(Estado|Status)\s*:?\*\*\s*:?\s*(.+)$/i);
    if (m) { out.estado = clean(m[2]); return out; }
  }
  return out;
}

/**
 * Task counting. Two live conventions:
 *  - checkboxes:  `- [x] T001` / `- [ ]` / `- [~]` (deferred)
 *  - headings:    `### T001 — title` with the state INSIDE the block body.
 * Heading form requires a delimiter after the number, or a narrative title like
 * `## T038 and T039 resolved` counts as an open task. Status markers are only read
 * from the heading itself and from lines that declare state — scanning whole blocks
 * made prose that *describes* the notation count as a marker.
 */
const DONE_RE = /✅|\bcompletad[oa]\b|\bhech[oa]\b|\bresuelt[oa]s?\b|\bdone\b|\bcompleted\b|\bcerrada\b/i;
const DEFER_RE = /\[~\]|\bdiferid[oa]\b|\bdeferred\b|\bsuperseded\b|\baparcad[oa]\b|→\s*BACKLOG/i;
const STATUS_LINE = /^\s*[*_>\s]*(Estado|Status|Hecho|Done when|Resultado|Result)\b\s*[:：]?/i;

function parseTasks(tasksPath) {
  if (!existsSync(tasksPath)) return null;
  const lines = readFileSync(tasksPath, "utf8").split("\n");
  let done = 0, open = 0, deferred = 0;
  const heads = [];
  lines.forEach((l, i) => { if (/^#{2,4}\s+T\d+\s*[—–\-:]/.test(l)) heads.push(i); });
  for (const l of lines) {
    const box = l.match(/^\s*[-*]\s*\[([ xX~])\]/);
    if (!box) continue;
    const c = box[1].toLowerCase();
    if (c === "x") done++; else if (c === "~") deferred++; else open++;
  }
  heads.forEach((start, idx) => {
    const end = idx + 1 < heads.length ? heads[idx + 1] : lines.length;
    const signal = lines.slice(start, end).filter((l, j) => j === 0 || STATUS_LINE.test(l)).join("\n");
    if (DEFER_RE.test(signal)) deferred++;
    else if (DONE_RE.test(signal)) done++;
    else open++;
  });
  const total = done + open + deferred;
  return total ? { done, open, deferred, total } : null;
}

/** Fallback: find the spec's status in the repo's specs/README.md index, by folder name. */
function indexLookup(project, specDir) {
  const readme = join(ROOT, project, "specs", "README.md");
  if (!existsSync(readme)) return null;
  const folder = basename(specDir);
  const num = (folder.match(/^(\d+)/) || [])[1];
  for (const line of readFileSync(readme, "utf8").split("\n")) {
    if (!line.startsWith("|")) continue;
    const cells = line.split("|").map((c) => c.trim());
    const hit = line.includes(folder) || (num && (cells[1] === num || cells[1]?.startsWith(num + " ")));
    if (!hit) continue;
    for (const cell of cells.slice(1)) {
      if (cell.includes(folder)) continue;
      if (normalise(cell)) return clean(cell);
    }
  }
  return null;
}

function collect() {
  const specs = [];
  for (const project of PROJECTS) {
    const featDir = join(ROOT, project, "specs", "features");
    if (!existsSync(featDir)) continue;
    for (const e of readdirSync(featDir, { withFileTypes: true })) {
      if (!e.isDirectory()) continue;
      const specPath = join(featDir, e.name, "SPEC.md");
      if (!existsSync(specPath)) continue;
      const head = parseSpec(specPath);
      let raw = head.estado;
      if (!normalise(raw)) raw = indexLookup(project, e.name) ?? raw;
      const v = normalise(raw);
      specs.push({
        project, name: e.name,
        num: (e.name.match(/^(\d+)/) || [])[1] || "—",
        raw, canon: v?.canon ?? null, bucket: v?.bucket ?? "unknown", legacy: !!v?.legacy,
        blockedBy: head.blockedBy && head.blockedBy !== "—" ? head.blockedBy : null,
        parent: head.parent && head.parent !== "—" ? head.parent : null,
        tasks: parseTasks(join(featDir, e.name, "TASKS.md")),
        path: `${project}/specs/features/${e.name}`,
      });
    }
  }
  return specs;
}

/**
 * WIP is measured over `In Progress` specs WITHOUT a declared blocker — the only ones
 * anyone can advance right now. Without that distinction, "WIP = 1" forces people to
 * lie about state in order to comply.
 */
function warnings(specs) {
  const w = [];
  const active = specs.filter((s) => s.bucket === "active");
  const movable = active.filter((s) => !s.blockedBy);
  if (movable.length > 1)
    w.push(`**WIP > 1.** ${movable.length} unblocked \`In Progress\` specs: ` +
      movable.map((s) => `\`${s.project}/${s.num}\``).join(", ") +
      ". Only one should be; the rest need `Blocked-by:` or a return to `Ready`.");
  else if (active.length > 1)
    w.push(`NOTE · ${active.length} specs \`In Progress\`, but ${active.length - movable.length} wait ` +
      `on something external. Real WIP: **${movable.length}**. If the blocker is the owner and only ` +
      "verification remains, the right state is probably `In Review`.");
  for (const s of specs) {
    if (s.bucket === "closed" && s.tasks?.open > 0)
      w.push(`**Closed with open tasks.** \`${s.path}\` is \`${s.canon}\` with **${s.tasks.open}** ` +
        "unchecked task(s). A task that will not be done gets `[~]` with destination and date.");
    if (s.bucket === "unknown")
      w.push(`**Unrecognized status.** \`${s.path}\` → ${s.raw ? `"${s.raw.slice(0, 60)}"` : "no detectable status"}.`);
    if (s.blockedBy && s.bucket === "closed")
      w.push(`**\`Blocked-by\` on a closed spec.** \`${s.path}\` (\`${s.canon}\`).`);
    if (s.bucket === "merged" && !s.blockedBy && !s.tasks?.open)
      w.push(`**\`Merged\` with nothing pending.** \`${s.path}\` has no open tasks and no blocker: ` +
        "if the behavior is verified in production, it should be `Live` with date and evidence.");
  }
  return w;
}

function render(specs) {
  const by = Object.fromEntries(BUCKET_ORDER.map((b) => [b, []]));
  by.unknown = [];
  for (const s of specs) (by[s.bucket] ??= []).push(s);
  for (const b of Object.keys(by))
    by[b].sort((a, c) => a.project.localeCompare(c.project) || a.num.localeCompare(c.num));
  const open = specs.filter((s) => !["closed", "parked"].includes(s.bucket));
  const openTasks = open.reduce((n, s) => n + (s.tasks?.open ?? 0), 0);
  const w = warnings(specs);

  const L = [];
  L.push("# BOARD — workspace work", "");
  L.push(
    "> **Generated. Do not edit.** Produced by `node .sdd-workspace/scripts/board.mjs` from each",
    "> project's specs. If a line here is wrong, the defect is in the source spec or in the",
    "> script — fix it there and regenerate. Editing this file reintroduces exactly the failure",
    "> mode it exists to eliminate: a hand-maintained state register.",
  );
  L.push("", `**${specs.length}** specs · **${open.length}** open · **${openTasks}** open tasks in them · **${by.active.length}** \`In Progress\``, "");
  if (w.length) { L.push("## Warnings", ""); for (const x of w) L.push(`- ${x}`); L.push(""); }

  for (const b of BUCKET_ORDER.concat("unknown")) {
    const rows = by[b] ?? [];
    if (!rows.length) continue;
    if (b === "closed") {
      const per = {};
      for (const s of rows) per[s.project] = (per[s.project] ?? 0) + 1;
      L.push(`## ${BUCKET_TITLE.closed}`, "",
        Object.entries(per).map(([p, n]) => `\`${p}\` ${n}`).join(" · ") + `  —  **${rows.length}** total.`, "");
      continue;
    }
    L.push(`## ${BUCKET_TITLE[b] ?? "Unrecognized status"}`, "");
    L.push("| Project | Spec | Status | Tasks | Blocked by | Parent |", "|---|---|---|---|---|---|");
    for (const s of rows) {
      const t = s.tasks ? `${s.tasks.done}/${s.tasks.total}${s.tasks.deferred ? ` (+${s.tasks.deferred} def.)` : ""}` : "—";
      L.push(`| \`${s.project}\` | [${s.num}](../${s.path}/SPEC.md) ${s.name.replace(/^\d+-/, "")} | ` +
        `${s.canon ?? "?"}${s.legacy ? " ⚠︎" : ""} | ${t} | ${s.blockedBy ?? "—"} | ${s.parent ?? "—"} |`);
    }
    L.push("");
  }
  const legacy = specs.filter((s) => s.legacy).length;
  L.push("---", "",
    `⚠︎ = legacy vocabulary (\`Done\`, \`Complete\`…). **${legacy}** specs use it. Not an error: ` +
    "migrating historical specs to new names would be the mass rewrite this tool avoids. New specs " +
    "use `Merged` / `Live`.", "",
    "**Status source, in order:** canonical block (`Estado|Status:` / `Blocked-by:` / `Parent:`) → " +
    "`## Status` section → header line → the repo's `specs/README.md` index.");
  return L.join("\n") + "\n";
}

// --- main ---
const specs = collect();
const md = render(specs);
const check = process.argv.includes("--check");
const list = process.argv.includes("--list");
const w = warnings(specs);

if (check) {
  const real = w.filter((x) => !x.startsWith("NOTE ·"));
  process.stdout.write(w.length ? w.map((x) => "• " + x.replace(/\*\*/g, "")).join("\n") + "\n" : "BOARD: no warnings.\n");
  process.exit(real.length ? 1 : 0);
}
mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, md, "utf8");

if (list) {
  const plain = (s) => (s ?? "").replace(/\*\*/g, "").replace(/`/g, "");
  const open = specs.filter((s) => s.bucket !== "closed");
  const movable = specs.filter((s) => s.bucket === "active" && !s.blockedBy);
  const T = { active: "IN PROGRESS", review: "IN REVIEW", merged: "MERGED · verify in production",
    ready: "READY", draft: "DRAFT · not authorized", blocked: "BLOCKED", parked: "PARKED", unknown: "UNRECOGNIZED" };
  const L = ["", `  ${specs.length} specs · ${open.length} open · real WIP ${movable.length}`];
  for (const b of ["active", "review", "merged", "ready", "draft", "blocked", "parked", "unknown"]) {
    const rows = open.filter((s) => s.bucket === b);
    if (!rows.length) continue;
    L.push("", `  ${T[b]}`);
    for (const s of rows.sort((a, c) => a.project.localeCompare(c.project) || a.num.localeCompare(c.num))) {
      const t = s.tasks ? `${s.tasks.done}/${s.tasks.total}` : "—";
      L.push(`    ${s.project.padEnd(15)} ${s.num}  ${s.name.replace(/^\d+-/, "").padEnd(38).slice(0, 38)} ${t.padStart(7)}`);
      if (s.blockedBy) L.push(`    ${" ".repeat(15)}      └─ ${plain(s.blockedBy).slice(0, 90)}`);
    }
  }
  if (w.length) { L.push("", "  WARNINGS"); for (const x of w) L.push(`    • ${plain(x).slice(0, 150)}`); }
  L.push("");
  process.stdout.write(L.join("\n") + "\n");
} else {
  process.stdout.write(`BOARD.md generated — ${specs.length} specs, ${specs.filter((s) => !["closed", "parked"].includes(s.bucket)).length} open, ${w.length} warning(s).\n`);
}
