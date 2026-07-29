# graphify — /graphify query

> Reference for the `graphify` skill. Loaded on demand from
> [`../SKILL.md`](../SKILL.md); not read unless this operation is in play.

## For /graphify query

Two traversal modes - choose based on the question:

| Mode | Flag | Best for |
|------|------|----------|
| BFS (default) | _(none)_ | "What is X connected to?" - broad context, nearest neighbors first |
| DFS | `--dfs` | "How does X reach Y?" - trace a specific chain or dependency path |

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

### Step 0 - Constrained query expansion (before traversal)

`graphify query` matches nodes by case-folded substring + IDF - **no stemming, no synonyms, no cross-language match**. When the question uses different vocabulary than the graph labels (user says "обработчик" / graph says "handler"; "authentication" / "Guardian"), the literal matcher returns 0 hits. Expand the query against the **actual graph vocabulary** first - never invent tokens:

```bash
node -e "
const fs = require('fs');
const g = JSON.parse(fs.readFileSync('.graphify/graph.json','utf-8'));
const vocab = new Set();
for (const n of (g.nodes || [])) {
  for (const c of String(n.label || '').match(/[^\W\d_]+/gu) || []) {
    for (const p of (c.match(/[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+/g) || [c])) {
      if (p.length > 1) vocab.add(p.toLowerCase());
    }
  }
}
fs.writeFileSync('.graphify/.vocab.txt', [...vocab].sort().join('\n'));
console.log('vocab: ' + vocab.size + ' tokens');
"
```

Read `.graphify/.vocab.txt`, then pick **up to 12 tokens from that exact list** that match the query intent. Hard constraints:
- Use only tokens present in `.vocab.txt` - do **not** invent tokens.
- A concept with no plausible vocab token: skip it, no near-synonym from memory.
- No vocab token matches at all: output an empty list and tell the user the corpus has no relevant vocabulary; do not fabricate a search.
- Cross-language: e.g. Russian "аутентификация" - look for `auth`, `credential`, `token`, `security` **iff present** in the vocab.

Print the selection before querying (`Query expanded to (from graph vocab, N tokens): [...]`), then run `graphify query` with the joined expanded tokens (keep the original question only for `save-result`).

Before deep traversal, run the compact first-hop summary and use it to choose the right graph action:

```bash
graphify summary --graph .graphify/graph.json
graphify recommend-commits --files src/auth.ts,src/session.ts --graph .graphify/graph.json
graphify review-analysis --files src/auth.ts --graph .graphify/graph.json
graphify review-eval --cases .graphify/review-cases.json --graph .graphify/graph.json
```

Load `.graphify/graph.json`, then:

1. Find the 1-3 nodes whose label best matches key terms in the question.
2. Run the appropriate traversal from each starting node.
3. Read the subgraph - node labels, edge relations, confidence tags, source locations.
4. Answer using **only** what the graph contains. Quote `source_location` when citing a specific fact.
5. If the graph lacks enough information, say so - do not hallucinate edges.

```bash
node -e "
const fs = require('fs');
const Graph = require('graphology');

const data = JSON.parse(fs.readFileSync('.graphify/graph.json', 'utf-8'));
const G = new Graph({type: 'undirected'});
for (const n of data.nodes) { const {id, ...a} = n; G.mergeNode(id, a); }
for (const l of data.links) { const {source, target, ...a} = l; if (G.hasNode(source) && G.hasNode(target)) try { G.mergeEdge(source, target, a); } catch {} }

const question = 'QUESTION';
const mode = 'MODE';  // 'bfs' or 'dfs'
const terms = question.split(/\s+/).filter(t => t.length > 3).map(t => t.toLowerCase());

// Find best-matching start nodes
const scored = [];
G.forEachNode((nid, ndata) => {
    const label = (ndata.label || '').toLowerCase();
    const score = terms.filter(t => label.includes(t)).length;
    if (score > 0) scored.push([score, nid]);
});
scored.sort((a, b) => b[0] - a[0]);
const startNodes = scored.slice(0, 3).map(s => s[1]);

if (!startNodes.length) {
    console.log('No matching nodes found for query terms:', terms);
    process.exit(0);
}

const subgraphNodes = new Set();
const subgraphEdges = [];

if (mode === 'dfs') {
    const visited = new Set();
    const stack = [...startNodes].reverse().map(n => [n, 0]);
    while (stack.length) {
        const [node, depth] = stack.pop();
        if (visited.has(node) || depth > 6) continue;
        visited.add(node);
        subgraphNodes.add(node);
        G.forEachNeighbor(node, neighbor => {
            if (!visited.has(neighbor)) {
                stack.push([neighbor, depth + 1]);
                subgraphEdges.push([node, neighbor]);
            }
        });
    }
} else {
    let frontier = new Set(startNodes);
    startNodes.forEach(n => subgraphNodes.add(n));
    for (let i = 0; i < 3; i++) {
        const nextFrontier = new Set();
        for (const n of frontier) {
            G.forEachNeighbor(n, neighbor => {
                if (!subgraphNodes.has(neighbor)) {
                    nextFrontier.add(neighbor);
                    subgraphEdges.push([n, neighbor]);
                }
            });
        }
        nextFrontier.forEach(n => subgraphNodes.add(n));
        frontier = nextFrontier;
    }
}

const tokenBudget = BUDGET;  // default 2000
const charBudget = tokenBudget * 4;

const relevance = nid => {
    const label = (G.getNodeAttributes(nid).label || '').toLowerCase();
    return terms.filter(t => label.includes(t)).length;
};

const rankedNodes = [...subgraphNodes].sort((a, b) => relevance(b) - relevance(a));

const lines = [\`Traversal: \${mode.toUpperCase()} | Start: \${JSON.stringify(startNodes.map(n => G.getNodeAttribute(n, 'label') || n))} | \${subgraphNodes.size} nodes\`];
for (const nid of rankedNodes) {
    const d = G.getNodeAttributes(nid);
    lines.push(\`  NODE \${d.label || nid} [src=\${d.source_file || ''} loc=\${d.source_location || ''}]\`);
}
for (const [u, v] of subgraphEdges) {
    if (subgraphNodes.has(u) && subgraphNodes.has(v)) {
        const edge = G.hasEdge(u, v) ? G.getEdgeAttributes(G.edge(u, v)) : {};
        lines.push(\`  EDGE \${G.getNodeAttribute(u, 'label') || u} --\${edge.relation || ''} [\${edge.confidence || ''}]--> \${G.getNodeAttribute(v, 'label') || v}\`);
    }
}

let output = lines.join('\n');
if (output.length > charBudget) {
    output = output.slice(0, charBudget) + \`\n... (truncated at ~\${tokenBudget} token budget - use --budget N for more)\`;
}
console.log(output);
"
```

Replace `QUESTION` with the user's actual question, `MODE` with `bfs` or `dfs`, and `BUDGET` with the token budget (default `2000`, or whatever `--budget N` specifies). Then answer based on the subgraph output above.

After writing the answer, save it back into the graph so it improves future queries:

```bash
node -e "
const { saveQueryResult } = require('@sentropic/graphify');
saveQueryResult({
    question: 'QUESTION',
    answer: 'ANSWER',
    memoryDir: '.graphify/memory',
    queryType: 'query',
    sourceNodes: SOURCE_NODES,  // list of node labels cited, or []
});
console.log('Query result saved to .graphify/memory/');
"
```

Replace `QUESTION` with the question, `ANSWER` with your full answer text, `SOURCE_NODES` with the list of node labels you cited. This closes the feedback loop: the next `--update` will extract this Q&A as a node in the graph.

---

