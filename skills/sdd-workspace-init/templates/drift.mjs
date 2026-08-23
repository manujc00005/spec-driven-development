#!/usr/bin/env node
/**
 * drift.mjs — compares what governance documents CLAIM against the files that back them.
 *
 * Why this exists, with a real case from the workspace this pattern was extracted from:
 * a dependency graph asserted a vendored bundle was at 1.2.3 — citing the file as
 * evidence — while the file had contained 1.3.2 for three days. Three successive human
 * readings took the document's word for it without opening the cited file. A whole audit
 * finding, a task instruction and a high-priority follow-up were built on that one stale
 * line. The rule everyone already knew ("the code wins") failed because applying it
 * depended on someone remembering to.
 *
 * Contracts are workspace-specific, so this ships as a DECLARATIVE skeleton: fill in
 * CONTRACTS below during workspace init. Each entry names one source of truth (a data
 * file owned by a project — a manifest, a package.json) and where its value must, or
 * must not, appear.
 *
 * With CONTRACTS empty it exits 0 and says so — no contract checks is a fact worth
 * printing, not an error.
 *
 * Usage:  node .sdd-workspace/scripts/drift.mjs [--quiet]
 *         --quiet  print only if drift is found. For the SessionStart hook.
 */

import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.env.SDD_WS_ROOT || join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const p = (...a) => join(ROOT, ...a);

/**
 * Declare one entry per shared contract. Worked example (from the source workspace,
 * where the widget's contract manifest owns the protocol version):
 *
 * {
 *   name: "webchat protocol",
 *   // Source of truth: a DATA file, never prose.
 *   source: { file: "chat-widget/docs/schemas/contract-manifest.json",
 *             extract: (t) => JSON.parse(t).protocol_version },
 *   // Files that must AGREE with the source (implementations, vendored copies):
 *   mustMatch: [
 *     { file: "lead-platform/src/lib/webchat/schemas.ts",
 *       extract: (t) => t.match(/PROTOCOL_VERSION\s*=\s*"([^"]+)"/)?.[1] },
 *   ],
 *   // Governance docs that must NOT pin any stale version number when talking about it
 *   // (lines mentioning these keywords are scanned for version-shaped numbers):
 *   docsGlob: ".sdd-workspace",  // every .md directly under this dir
 *   keywords: /widget|protocol/i,
 * }
 */
const CONTRACTS = [];

/** Generated files are derived from specs — checking them is checking the source twice. */
const GENERATED = new Set(["BOARD.md"]);

const findings = [];
const notes = [];

for (const c of CONTRACTS) {
  const srcPath = p(c.source.file);
  if (!existsSync(srcPath)) { notes.push(`${c.name}: source ${c.source.file} not found — skipped`); continue; }
  const current = c.source.extract(readFileSync(srcPath, "utf8"));
  if (!current) { findings.push({ c: c.name, msg: `could not extract value from ${c.source.file}` }); continue; }

  for (const m of c.mustMatch ?? []) {
    const f = p(m.file);
    if (!existsSync(f)) continue;
    const v = m.extract(readFileSync(f, "utf8"));
    if (v && v !== current)
      findings.push({ c: c.name, msg: `\`${m.file}\` says **${v}**, source of truth says **${current}**` });
  }

  if (c.docsGlob && c.keywords) {
    const dir = p(c.docsGlob);
    if (existsSync(dir))
      for (const f of readdirSync(dir).filter((x) => x.endsWith(".md") && !GENERATED.has(x))) {
        let struck = false;
        readFileSync(join(dir, f), "utf8").split("\n").forEach((line, i) => {
          const marks = (line.match(/~~/g) || []).length;
          const was = struck;
          if (marks % 2 === 1) struck = !struck;
          if (was || struck || /~~.*~~/.test(line)) return;      // struck-through = history
          if (line.includes("drift-ok")) return;                 // explicit escape hatch
          if (!c.keywords.test(line)) return;
          for (const mm of line.matchAll(/\bv?(\d+\.\d+(?:\.\d+)?)\b/g)) {
            const v = mm[1];
            if (v === current || `v${v}` === current) continue;
            const [maj, min] = v.split(".");
            if (maj.length > 2 || min.length > 2) continue;      // counts, dates, thousands
            if (/[§#]/.test(line.slice(Math.max(0, mm.index - 2), mm.index))) continue; // §refs
            findings.push({ c: c.name, msg: `\`${c.docsGlob}/${f}:${i + 1}\` pins **${v}** (current: **${current}**). ` +
              "If deliberate history, add `<!-- drift-ok -->` to the line.\n    > " + line.trim().slice(0, 100) });
          }
        });
      }
  }
}

const quiet = process.argv.includes("--quiet");
if (!CONTRACTS.length) {
  if (!quiet) console.log("drift: no contracts declared yet — edit CONTRACTS in .sdd-workspace/scripts/drift.mjs when the workspace has one.");
  process.exit(0);
}
if (!findings.length) {
  if (!quiet) console.log(`drift: clean. ${CONTRACTS.length} contract(s) checked.` + (notes.length ? ` (${notes.join("; ")})` : ""));
  process.exit(0);
}
console.log(`\n⚠︎  DRIFT — ${findings.length} finding(s).\n`);
for (const f of findings) console.log(`  [${f.c}] ${f.msg}\n`);
process.exit(1);
