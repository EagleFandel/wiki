# Operations

## INIT

Use `scripts/init_wiki.py` when you want deterministic scaffolding.

It should create:

- `raw/`
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

After init:

1. Record an init entry in `wiki/log.md`
2. If `raw/` already has files, identify them and suggest or run INGEST

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

Good ingest targets in real work:

- meeting notes
- product requirement notes
- customer feedback digests
- research papers or articles
- decision records from discussions or PRs
- incident notes or postmortems

For PDFs, Office docs, HTML, screenshots, or document images:

1. Stage the original under `raw/`
2. Run `scripts/extract_with_markitdown.py`
3. Read the generated markdown in `raw/.extracted/`
4. Write the durable wiki page from the extracted text plus the original asset context

## QUERY

Answer from the wiki first when the workspace already contains relevant pages.

A good query answer usually does all of this:

- cites the most relevant pages
- points out disagreements or missing evidence
- links the answer back to source pages
- suggests whether the answer should be filed under `queries/`

## HEALTH

Check:

- `raw/` files missing from `wiki/log.md`
- `raw/` files newer than the latest wiki update in `wiki/log.md`
- important topics missing a durable page
- stale summaries in `overview.md`
- duplicated or overlapping pages
- broken relative links
- pages with no useful references from `index.md`

## REFRESH

Use after many ingests or when the user asks for a refreshed synthesis.

Most common refresh outputs:

- rewrite `overview.md`
- create or update a topic map in `wiki/maps/`
- summarize unresolved issues in `active-questions.md`
- capture stabilized tradeoffs in `wiki/decisions/`
