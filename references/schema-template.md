# Schema Template

Copy this file to your project root as `AGENTS.md` (or `CLAUDE.md` for Claude Code).
It is the contract the agent reads before every wiki operation.
Mirror it in `wiki/schema.md` for human browsing.

```markdown
# [Project Name] Wiki — Schema

## Purpose

This wiki compiles curated sources into a persistent, interlinked knowledge base for [your domain or team].
Humans curate sources and ask questions. The agent handles ingestion, cross-referencing, linting, and rendering.

## Directories

- `raw/` — Immutable source material. Never edit files here.
  - `raw/inbox/` — Drop zone for unprocessed sources.
  - `raw/articles/` — Web articles and HTML clips converted to markdown.
  - `raw/papers/` — Papers, reports, long-form documents.
  - `raw/assets/` — Localized images and attachments.
  - `raw/.extracted/` — Generated markdown cache from PDFs/docs/images.
- `wiki/` — LLM-maintained compiled knowledge.
  - `wiki/index.md` — Catalog of all pages.
  - `wiki/log.md` — Append-only operation log.
  - `wiki/schema.md` — Mirror of this file.
  - `wiki/overview.md` — High-level synthesis.
  - `wiki/active-questions.md` — Open questions and follow-ups.
  - `wiki/maps/` — Topic maps and relationship overviews.
  - `wiki/sources/` — One page per ingested source.
  - `wiki/concepts/` — Concepts and reusable ideas.
  - `wiki/entities/` — People, companies, projects, tools.
  - `wiki/decisions/` — Durable decisions and ADR-like notes.
  - `wiki/queries/` — Condensed high-value query answers.
- `outputs/` — Derived answers, reports, slide decks, charts, and HTML views.

## Core Principle

**Markdown is for production; HTML is for consumption.**
Author and maintain everything in markdown. Render to HTML only when the result is meant to be read, shared, or interacted with.

## Page Conventions

Every durable page starts with YAML frontmatter:

```yaml
---
title: Page Title
type: overview | source | concept | entity | decision | query | map | digest
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/articles/example.md]
---
```

- Start each page with a 1-2 sentence summary.
- Use lowercase, hyphenated filenames (e.g. `transformer-architecture.md`).
- Cross-reference with `[[wikilinks]]` or relative markdown links.
- Keep raw facts on `sources/` pages and synthesis on concept/entity/decision/map pages.
- Update existing pages before creating near-duplicates.

## Taxonomy

Allowed tags. Do not invent new tags without updating this list.

- `source`, `concept`, `entity`, `decision`, `query`, `map`, `digest`
- [add domain-specific tags here, e.g. `architecture`, `product`, `research`]

## Ingest Procedure

1. Read the new source in `raw/` (or its extracted markdown companion in `raw/.extracted/`).
2. For web articles, ensure images are downloaded to `raw/assets/` and links are local.
3. Classify contributions: `source`, `concept`, `entity`, `decision`, `query-worthy synthesis`.
4. Create or update the relevant `sources/` page.
5. Update affected concept, entity, map, or decision pages.
6. Update `wiki/overview.md` if the big picture changes.
7. Update `wiki/index.md`.
8. Append to `wiki/log.md` with format: `## [YYYY-MM-DD] ingest | Source Title | raw/articles/file.md`.
9. If git is present, stage changes and suggest a structured commit.

## SYNC Procedure

1. Identify all files in `raw/` newer than the latest `wiki/log.md` entry.
2. Run a lightweight INGEST pass for each.
3. Detect renamed, deleted, or modified sources and repair links.
4. Append a single SYNC log entry summarizing the batch.
5. Stage changes and suggest a single structured commit.

## QUERY Procedure

1. Read `wiki/index.md`.
2. Read the most relevant pages and linked neighbors.
3. Answer with citations to wiki pages.
4. If durable or cross-cutting, write to `outputs/YYYY-MM-DD-query-slug.md`.
5. Optionally file a condensed version in `wiki/queries/`.
6. Render an HTML version when the answer is for human consumption.

## DIGEST Procedure

1. Read recent `wiki/log.md` entries.
2. Read pages created or updated since the last digest.
3. Write a synthesis to `outputs/YYYY-MM-DD-digest-slug.md`.
4. Render an HTML version for reading.
5. Surface patterns, contradictions, emerging questions, and suggested next sources.
6. Optionally append a short entry to `wiki/log.md` and link from `overview.md`.

## Lint Checklist

- [ ] Every page in `wiki/` appears in `wiki/index.md`.
- [ ] Every `[[wikilink]]` resolves to a real file.
- [ ] No two pages cover the same concept.
- [ ] Conflicting claims are flagged, not silently overwritten.
- [ ] Sources in `raw/` are reflected in `wiki/log.md`.
- [ ] `overview.md` and `maps/` are not stale.
- [ ] Images referenced from `raw/articles/` are stored in `raw/assets/`.

## Conflict Resolution

When a new source contradicts an existing wiki page:

1. Do not silently overwrite the old claim.
2. Note the contradiction explicitly and cite both sources.
3. If the new source is clearly more authoritative or recent, update the page and explain the change.

## Output Formats

- Markdown reports for editing and archiving.
- HTML views for reading, sharing, and interaction.
- Marp slide decks for presentations.
- Matplotlib charts for data visualization.

**Rule of thumb:**
- If the output will be edited or reused by another agent → keep it markdown.
- If the output will be read, shared, presented, or interacted with → render it as HTML.
- When in doubt, produce both: a markdown source and a rendered HTML view in `outputs/`.

For complex syntheses, prefer HTML: spatial layouts, tabs, collapsible sections, comparison tables, and inline visualizations make dense knowledge easier to consume than a linear markdown wall.

### HTML Output Checklist

- [ ] Markdown source exists in `outputs/` for future editing.
- [ ] HTML view exists when the output is for human consumption.
- [ ] CSS is clean and readable, not visually noisy.
- [ ] Links between markdown source and HTML view are bidirectional.
- [ ] The output is linked from `wiki/log.md` or the relevant wiki page.

## Git

- Keep the wiki as a git repo.
- Make a structured commit after each significant INGEST, SYNC, or REFRESH.
- Review diffs before committing, especially for modified existing pages.
- Revert rather than layer fixes when a claim is wrong.
```
