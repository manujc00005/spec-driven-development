# graphify — /graphify add

> Reference for the `graphify` skill. Loaded on demand from
> [`../SKILL.md`](../SKILL.md); not read unless this operation is in play.

## For /graphify add

Fetch a URL and add it to the corpus, then update the graph.

```bash
node -e "
(async () => {
const { ingest } = require('@sentropic/graphify');
const out = await ingest('URL', './raw', {author: 'AUTHOR', contributor: 'CONTRIBUTOR'});
console.log(\`Saved to \${out}\`);
})().catch((e) => {
    console.error(\`error: \${e.message}\`);
    process.exit(1);
});
"
```

Replace `URL` with the actual URL, `AUTHOR` with the user's name if provided, `CONTRIBUTOR` likewise. If the command exits with an error, tell the user what went wrong - do not silently continue. After a successful save, automatically run the `--update` pipeline on `./raw` to merge the new file into the existing graph.

Supported URL types (auto-detected):
- Twitter/X → fetched via oEmbed, saved as `.md` with tweet text and author
- arXiv → abstract + metadata saved as `.md`  
- YouTube / video URLs → audio downloaded locally via `yt-dlp`; transcript generated on the next build/update (requires local `yt-dlp`, `ffmpeg`, and `faster-whisper-ts`)
- PDF → downloaded as `.pdf`
- Images (.png/.jpg/.webp) → downloaded, Claude vision extracts on next run
- Any webpage → converted to markdown via html2text

---

