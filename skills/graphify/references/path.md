# graphify — /graphify path

> Reference for the `graphify` skill. Loaded on demand from
> [`../SKILL.md`](../SKILL.md); not read unless this operation is in play.

## For /graphify path

Find the shortest path between two named concepts in the graph.

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
const { bidirectional } = require('graphology-shortest-path/unweighted');

const data = JSON.parse(fs.readFileSync('.graphify/graph.json', 'utf-8'));
const G = new Graph({type: 'undirected'});
for (const n of data.nodes) { const {id, ...a} = n; G.mergeNode(id, a); }
for (const l of data.links) { const {source, target, ...a} = l; if (G.hasNode(source) && G.hasNode(target)) try { G.mergeEdge(source, target, a); } catch {} }

const aTerm = 'NODE_A';
const bTerm = 'NODE_B';

function findNode(term) {
    term = term.toLowerCase();
    const scored = [];
    G.forEachNode((n, a) => {
        const label = (a.label || '').toLowerCase();
        const score = term.split(/\s+/).filter(w => label.includes(w)).length;
        if (score > 0) scored.push([score, n]);
    });
    scored.sort((a, b) => b[0] - a[0]);
    return scored.length && scored[0][0] > 0 ? scored[0][1] : null;
}

const src = findNode(aTerm);
const tgt = findNode(bTerm);

if (!src || !tgt) {
    console.log(\`Could not find nodes matching: '\${aTerm}' or '\${bTerm}'\`);
    process.exit(0);
}

const path = bidirectional(G, src, tgt);
if (!path) {
    console.log(\`No path found between '\${aTerm}' and '\${bTerm}'\`);
} else {
    console.log(\`Shortest path (\${path.length - 1} hops):\`);
    for (let i = 0; i < path.length; i++) {
        const nid = path[i];
        const label = G.getNodeAttribute(nid, 'label') || nid;
        if (i < path.length - 1) {
            const edgeKey = G.edge(nid, path[i + 1]);
            const edge = edgeKey ? G.getEdgeAttributes(edgeKey) : {};
            console.log(\`  \${label} --\${edge.relation || ''}--> [\${edge.confidence || ''}]\`);
        } else {
            console.log(\`  \${label}\`);
        }
    }
}
"
```

Replace `NODE_A` and `NODE_B` with the actual concept names from the user. Then explain the path in plain language - what each hop means, why it's significant.

After writing the explanation, save it back:

```bash
node -e "
const { saveQueryResult } = require('@sentropic/graphify');
saveQueryResult({
    question: 'Path from NODE_A to NODE_B',
    answer: 'ANSWER',
    memoryDir: '.graphify/memory',
    queryType: 'path_query',
    sourceNodes: PATH_NODES,  // list of node labels on the path
});
console.log('Path result saved to .graphify/memory/');
"
```

---

