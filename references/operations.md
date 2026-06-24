# Operations

## INIT

Use `scripts/init_wiki.py` when you want deterministic scaffolding.

It should create:

- `raw/`
- `raw/inbox/`
- `raw/articles/`
- `raw/papers/`
- `raw/assets/`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/schema.md`
- `wiki/overview.md`
- `wiki/active-questions.md`
- `wiki/maps/`
- `wiki/concepts/`
- `wiki/entities/`
- `wiki/sources/`
- `wiki/decisions/`
- `wiki/queries/`
- `outputs/`
- `AGENTS.md` (project-level schema contract)

After init:

1. Record an init entry in `wiki/log.md`
2. Initialize git if it is not already present and make a baseline commit
3. If `raw/` already has files, identify them and suggest or run SYNC/INGEST

## INGEST

Recommended ingest loop:

1. Read the source once
2. Decide whether it primarily adds:
   - facts
   - concepts
   - entities
   - decisions
   - open questions
3. Create or update exactly the pages that benefit
4. Add or refresh cross-links
5. Update `index.md`
6. Append a log entry
7. If git is present, stage changes and suggest a structured commit

Good ingest targets in real work:

- meeting notes
- product requirement notes
- customer feedback digests
- research papers or articles
- decision records from discussions or PRs
- incident notes or postmortems
- web articles clipped to markdown

For PDFs, Office docs, HTML exports, screenshots, or document images:

1. Stage the original under `raw/`
2. Run `scripts/extract_with_markitdown.py`
3. Read the generated markdown in `raw/.extracted/`
4. Write the durable wiki page from the extracted text plus the original asset context

For web articles:

1. Convert the page to markdown with a web clipper
2. Save to `raw/articles/YYYY-MM-DD-page-title-slug.md`
3. Add frontmatter: `title`, `url`, `clipped`, `source_type: web_clip`, `tags`
4. Download images to `raw/assets/` and rewrite links to local paths
5. Run INGEST

## SYNC

Use when a batch of sources has accumulated in `raw/` (especially `raw/inbox/`).

1. Identify files in `raw/` newer than the latest `wiki/log.md` entry
2. Run a lightweight INGEST pass for each
3. Detect renamed, deleted, or modified sources and repair wiki links
4. Produce a single SYNC log entry summarizing the batch
5. Stage changes and suggest a single structured commit

## QUERY

Answer from the wiki first when the workspace already contains relevant pages.

A good query answer usually does all of this:

- cites the most relevant pages
- points out disagreements or missing evidence
- links the answer back to source pages
- writes durable answers to `outputs/YYYY-MM-DD-query-slug.md`
- optionally files a condensed version under `wiki/queries/`

**Output format rule of thumb:**
- If the answer will be edited, extended, or reused by another agent operation → keep it markdown.
- If the answer will be read, shared, presented, or interacted with → render it as HTML.
- When in doubt, produce both: `outputs/YYYY-MM-DD-query-slug.md` and `outputs/YYYY-MM-DD-query-slug.html`.

For complex syntheses, prefer HTML: spatial layouts, tabs, collapsible sections, comparison tables, and inline visualizations all make dense knowledge easier to consume than a linear markdown wall.

## DIGEST

Use for periodic syntheses: weekly recaps, milestone summaries, or "what have we learned lately?"

1. Read recent `wiki/log.md` entries
2. Read pages created or updated since the last digest
3. Write a synthesis to `outputs/YYYY-MM-DD-digest-slug.md`
4. Render a readable HTML version when the digest is for human consumption
5. Surface patterns, contradictions, emerging questions, and suggested next sources
6. Optionally append a short digest entry to `wiki/log.md` and link it from `overview.md`

## LINT

Check:

- `raw/` files missing from `wiki/log.md`
- `raw/` files newer than the latest wiki update in `wiki/log.md`
- important topics missing a durable page
- stale summaries in `overview.md`
- duplicated or overlapping pages
- broken relative links or `[[wikilinks]]`
- pages with no useful references from `index.md`
- contradictions between pages
- claims that newer sources may have superseded

## REFRESH

Use after many ingests or when the user asks for a refreshed synthesis.

Most common refresh outputs:

- rewrite `overview.md`
- create or update a topic map in `wiki/maps/`
- summarize unresolved issues in `active-questions.md`
- capture stabilized tradeoffs in `wiki/decisions/`

## Git Workflow

Treat the wiki as a git repo of plain markdown files.

- after each significant INGEST, SYNC, or REFRESH, stage changes and suggest a structured commit
- review diffs before committing, especially when existing pages are modified
- if a claim is wrong, revert the offending commit rather than layering more fixes on top
- run LINT before and after large batches to catch drift early
