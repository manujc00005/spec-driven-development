# graphify — --update (incremental re-extraction)

> Reference for the `graphify` skill. Loaded on demand from
> [`../SKILL.md`](../SKILL.md); not read unless this operation is in play.

## For --update (incremental re-extraction)

Use when you've added or modified files since the last run. Only re-extracts changed files - saves tokens and time.

```bash
node -e "
const fs = require('fs');
const { detectIncremental } = require('@sentropic/graphify');

const result = detectIncremental('INPUT_PATH');
const newTotal = result.new_total || 0;
console.log(JSON.stringify(result, null, 2));
fs.writeFileSync('.graphify/.graphify_incremental.json', JSON.stringify(result));
if (newTotal === 0) {
    console.log('No files changed since last run. Nothing to update.');
    process.exit(0);
}
console.log(\`\${newTotal} new/changed file(s) to re-extract.\`);
"
```

If new files exist, first check whether all changed files are code files:

```bash
node -e "
const fs = require('fs');
const path = require('path');

const result = fs.existsSync('.graphify/.graphify_incremental.json') ? JSON.parse(fs.readFileSync('.graphify/.graphify_incremental.json', 'utf-8')) : {};
const codeExts = new Set(['.py','.ts','.js','.go','.rs','.java','.cpp','.c','.rb','.swift','.kt','.cs','.scala','.php','.cc','.cxx','.hpp','.h','.kts','.lua','.toc']);
const newFiles = result.new_files || {};
const allChanged = Object.values(newFiles).flat();
const codeOnly = allChanged.every(f => codeExts.has(path.extname(f).toLowerCase()));
console.log('code_only:', codeOnly);
"
```

If `code_only` is True: print `[graphify update] Code-only changes detected - skipping semantic extraction (no LLM needed)`, run only Step 3A (AST) on the changed files, skip Step 3B entirely (no subagents), then go straight to merge and Steps 4–8.

If `code_only` is False (any changed file is a doc/paper/image/video): first prepare transcripts and PDF sidecars if needed, then run the full Steps 3A–3C pipeline as normal.

When `code_only` is False, run this before Step 3B:

```bash
node -e "
(async () => {
const fs = require('fs');
const { prepareSemanticDetection } = require('@sentropic/graphify');

const detect = JSON.parse(fs.readFileSync('.graphify/.graphify_incremental.json', 'utf-8'));
const analysis = fs.existsSync('.graphify/.graphify_analysis.json')
  ? JSON.parse(fs.readFileSync('.graphify/.graphify_analysis.json', 'utf-8'))
  : null;

const { detection: semanticDetect, transcriptPaths, pdfArtifacts } = await prepareSemanticDetection(detect, {
  transcriptOutputDir: '.graphify/transcripts',
  pdfOutputDir: '.graphify/converted/pdf',
  godNodes: (analysis && analysis.gods) || [],
  incremental: true,
});

fs.writeFileSync('.graphify/.graphify_incremental_semantic.json', JSON.stringify(semanticDetect, null, 2));
fs.writeFileSync('.graphify/.graphify_transcripts.json', JSON.stringify(transcriptPaths, null, 2));
fs.writeFileSync('.graphify/.graphify_pdf_ocr.json', JSON.stringify(pdfArtifacts, null, 2));
console.log('Prepared semantic inputs: ' + transcriptPaths.length + ' transcript(s), ' + pdfArtifacts.filter((item) => item.markdownPath).length + ' PDF sidecar(s)');
)().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
"
```

When re-running Step 3B in update mode, use `.graphify/.graphify_incremental_semantic.json` instead of `.graphify/.graphify_detect_semantic.json`.

Then:

```bash
node -e "
const fs = require('fs');
const Graph = require('graphology');
const { buildFromJson } = require('@sentropic/graphify');

// Load existing graph
const existingData = JSON.parse(fs.readFileSync('.graphify/graph.json', 'utf-8'));
const GExisting = new Graph({type: 'undirected'});
for (const n of existingData.nodes) { const {id, ...a} = n; GExisting.mergeNode(id, a); }
for (const l of existingData.links) { const {source, target, ...a} = l; if (GExisting.hasNode(source) && GExisting.hasNode(target)) try { GExisting.mergeEdge(source, target, a); } catch {} }

// Load new extraction
const newExtraction = JSON.parse(fs.readFileSync('.graphify/.graphify_extract.json', 'utf-8'));
const GNew = buildFromJson(newExtraction);

// Prune nodes from deleted files
const incremental = JSON.parse(fs.readFileSync('.graphify/.graphify_incremental.json', 'utf-8'));
const deleted = new Set(incremental.deleted_files || []);
if (deleted.size > 0) {
    const toRemove = GExisting.filterNodes((n, a) => deleted.has(a.source_file));
    toRemove.forEach(n => GExisting.dropNode(n));
    console.log(\`Pruned \${toRemove.length} ghost nodes from \${deleted.size} deleted file(s)\`);
}

// Merge: new nodes/edges into existing graph
GNew.forEachNode((n, a) => GExisting.mergeNode(n, a));
GNew.forEachEdge((e, a, s, t) => { try { GExisting.mergeEdge(s, t, a); } catch {} });
console.log(\`Merged: \${GExisting.order} nodes, \${GExisting.size} edges\`);
"
```

Then run Steps 4–8 on the merged graph as normal.

After Step 4, show the graph diff:

```bash
node -e "
const fs = require('fs');
const Graph = require('graphology');
const { graphDiff, buildFromJson } = require('@sentropic/graphify');

const oldData = fs.existsSync('.graphify/.graphify_old.json') ? JSON.parse(fs.readFileSync('.graphify/.graphify_old.json', 'utf-8')) : null;
const newExtract = JSON.parse(fs.readFileSync('.graphify/.graphify_extract.json', 'utf-8'));
const GNew = buildFromJson(newExtract);

if (oldData) {
    const GOld = new Graph({type: 'undirected'});
    for (const n of oldData.nodes) { const {id, ...a} = n; GOld.mergeNode(id, a); }
    for (const l of oldData.links) { const {source, target, ...a} = l; if (GOld.hasNode(source) && GOld.hasNode(target)) try { GOld.mergeEdge(source, target, a); } catch {} }
    const diff = graphDiff(GOld, GNew);
    console.log(diff.summary);
    if (diff.new_nodes && diff.new_nodes.length) {
        console.log('New nodes:', diff.new_nodes.slice(0, 5).map(n => n.label).join(', '));
    }
    if (diff.new_edges && diff.new_edges.length) {
        console.log('New edges:', diff.new_edges.length);
    }
}
"
```

Before the merge step, save the old graph: `cp .graphify/graph.json .graphify/.graphify_old.json`
Clean up after: `rm -f .graphify/.graphify_old.json .graphify/.graphify_incremental_semantic.json .graphify/.graphify_transcripts.json .graphify/.graphify_pdf_ocr.json`

---

