# graphify — --cluster-only

> Reference for the `graphify` skill. Loaded on demand from
> [`../SKILL.md`](../SKILL.md); not read unless this operation is in play.

## For --cluster-only

Skip Steps 1–3. Load the existing graph from `.graphify/graph.json` and re-run clustering:

```bash
node -e "
const fs = require('fs');
const Graph = require('graphology');
const { cluster, scoreAll } = require('@sentropic/graphify');
const { godNodes, surprisingConnections } = require('@sentropic/graphify');
const { generateReport } = require('@sentropic/graphify');
const { toJson } = require('@sentropic/graphify');

const data = JSON.parse(fs.readFileSync('.graphify/graph.json', 'utf-8'));
const G = new Graph({type: 'undirected'});
for (const n of data.nodes) { const {id, ...a} = n; G.mergeNode(id, a); }
for (const l of data.links) { const {source, target, ...a} = l; if (G.hasNode(source) && G.hasNode(target)) try { G.mergeEdge(source, target, a); } catch {} }

const detection = {total_files: 0, total_words: 99999, needs_graph: true, warning: null,
             files: {code: [], document: [], paper: []}};
const tokens = {input: 0, output: 0};

const communities = cluster(G);
const cohesion = scoreAll(G, communities);
const gods = godNodes(G);
const surprises = surprisingConnections(G, communities);
const labels = new Map(Array.from(communities.keys(), cid => [cid, 'Community ' + cid]));

const report = generateReport(G, communities, cohesion, labels, gods, surprises, detection, tokens, '.');
fs.writeFileSync('.graphify/GRAPH_REPORT.md', report);
toJson(G, communities, '.graphify/graph.json');

const analysis = {
    communities: Object.fromEntries(Array.from(communities.entries(), ([k, v]) => [String(k), v])),
    cohesion: Object.fromEntries(Array.from(cohesion.entries(), ([k, v]) => [String(k), v])),
    gods,
    surprises,
};
fs.writeFileSync('.graphify/.graphify_analysis.json', JSON.stringify(analysis, null, 2));
console.log(\`Re-clustered: \${communities.size} communities\`);
"
```

Then run Steps 5–9 as normal (label communities, generate viz, benchmark, clean up, report).

---

