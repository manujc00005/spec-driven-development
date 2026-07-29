# graphify — /graphify explain

> Reference for the `graphify` skill. Loaded on demand from
> [`../SKILL.md`](../SKILL.md); not read unless this operation is in play.

## For /graphify explain

Give a plain-language explanation of a single node - everything connected to it.

First check the graph exists:
```bash
node -e "
const fs = require('fs');
if (!fs.existsSync('.graphify/graph.json')) {
    console.log('ERROR: No graph found. Run /graphify <path> first to build the graph.');
    process.exit(1);
}
"
```
If it fails, stop and tell the user to run `/graphify <path>` first.

```bash
node -e "
const fs = require('fs');
const Graph = require('graphology');

const data = JSON.parse(fs.readFileSync('.graphify/graph.json', 'utf-8'));
const G = new Graph({type: 'undirected'});
for (const n of data.nodes) { const {id, ...a} = n; G.mergeNode(id, a); }
for (const l of data.links) { const {source, target, ...a} = l; if (G.hasNode(source) && G.hasNode(target)) try { G.mergeEdge(source, target, a); } catch {} }

const term = 'NODE_NAME';
const termLower = term.toLowerCase();

const scored = [];
G.forEachNode((n, a) => {
    const label = (a.label || '').toLowerCase();
    const score = termLower.split(/\s+/).filter(w => label.includes(w)).length;
    if (score > 0) scored.push([score, n]);
});
scored.sort((a, b) => b[0] - a[0]);
if (!scored.length || scored[0][0] === 0) {
    console.log(\`No node matching '\${term}'\`);
    process.exit(0);
}

const nid = scored[0][1];
const dataN = G.getNodeAttributes(nid);
console.log(\`NODE: \${dataN.label || nid}\`);
console.log(\`  source: \${dataN.source_file || 'unknown'}\`);
console.log(\`  type: \${dataN.file_type || 'unknown'}\`);
console.log(\`  degree: \${G.degree(nid)}\`);
console.log();
console.log('CONNECTIONS:');
G.forEachNeighbor(nid, (neighbor) => {
    const edgeKey = G.edge(nid, neighbor);
    const edge = edgeKey ? G.getEdgeAttributes(edgeKey) : {};
    const nlabel = G.getNodeAttribute(neighbor, 'label') || neighbor;
    console.log(\`  --\${edge.relation || ''}--> \${nlabel} [\${edge.confidence || ''}] (\${G.getNodeAttribute(neighbor, 'source_file') || ''})\`);
});
"
```

Replace `NODE_NAME` with the concept the user asked about. Then write a 3-5 sentence explanation of what this node is, what it connects to, and why those connections are significant. Use the source locations as citations.

After writing the explanation, save it back:

```bash
node -e "
const { saveQueryResult } = require('@sentropic/graphify');
saveQueryResult({
    question: 'Explain NODE_NAME',
    answer: 'ANSWER',
    memoryDir: '.graphify/memory',
    queryType: 'explain',
    sourceNodes: ['NODE_NAME'],
});
console.log('Explanation saved to .graphify/memory/');
"
```

---

