---
name: wiki
description: "Build and maintain a persistent workspace wiki - a compounding knowledge base of interlinked markdown files inspired by Karpathy's LLM Wiki pattern, but adapted for real project work. TRIGGER when: user says 'add to wiki', 'ingest this', 'update the wiki', 'start a wiki', asks synthesis questions over accumulated sources, wants a research/project knowledge base, or requests a wiki health check, drift check, or gap analysis. Also use when a workspace already has wiki/ and the answer would benefit from persistent project knowledge. Good inputs include articles, papers, notes, meeting summaries, product context, PR notes, ADRs, screenshots, pasted text, PDFs, Office docs, and document images. DO NOT TRIGGER for source-code architecture analysis alone; use opensource-analyzer for that."
---

# Wiki

This skill turns one-off research and project context into a persistent knowledge base that compounds over time.

Use it when the user does not just want an answer right now, but wants the answer to become part of the workspace's memory.

Core principles:

- `raw/` is immutable source material curated by the user or captured during work
- `raw/.extracted/` is a hidden conversion cache for PDFs, docs, and images
- `wiki/` is maintained knowledge written for future reuse
- good answers should compound back into the wiki when they have lasting value
- the wiki should help with real work: research, onboarding, decisions, product context, recurring questions, and handoffs

## Decision Tree

```text
Does wiki/ exist?
|- No
|  |- User explicitly wants a persistent wiki or says "init/start wiki" -> INIT
|  `- Otherwise answer normally and suggest wiki only if durable memory would help
`- Yes
   |- New or changed files in raw/ not reflected in wiki/log.md? -> INGEST
   |- User asks "what do we know about X" / "compare A and B" / "summarize current state" -> QUERY
   |- User asks "check drift" / "health check" / "find gaps" / "lint wiki" -> HEALTH
   |- User pastes content, notes, meeting summary, PR summary, source URL, PDF, or screenshot to keep -> SAVE TO RAW, then INGEST
   `- User asks to refresh overview/topic map after many changes -> REFRESH
```

## Recommended Structure

```text
raw/                    # Immutable source material
  .extracted/           # Hidden markdown cache generated from PDFs/docs/images
wiki/
|- index.md            # Catalog of important pages
|- log.md              # Append-only operation log
|- schema.md           # Wiki conventions
|- overview.md         # Current high-level synthesis
|- active-questions.md # Open questions and follow-ups
|- maps/               # Topic maps and relationship overviews
|- concepts/           # Concepts and reusable ideas
|- entities/           # People, companies, projects, tools
|- sources/            # One page per ingested source
|- decisions/          # Durable decisions, tradeoffs, ADR-like notes
`- queries/            # High-value query answers worth keeping
```

The wiki should stay intentionally small and useful. Do not create pages just because a folder exists.

## Operations

### INIT

Use when the user wants a persistent workspace wiki.

1. Create `raw/` and `wiki/` if missing
2. Scaffold the recommended structure
3. Write baseline `schema.md`, `index.md`, `log.md`, `overview.md`, and `active-questions.md`
4. If `raw/` already has files, immediately queue INGEST
5. If the workspace has an instruction or memory file, add a brief note that the project maintains a wiki in `wiki/`

If you want deterministic scaffolding, use `scripts/init_wiki.py`.

### INGEST

Use when there is new durable material to preserve.

Suitable source types:

- articles, papers, docs, notes
- meeting notes and user interviews
- product context and requirements
- PR summaries or architectural decisions
- screenshots with explanatory notes
- PDFs, Office docs, HTML exports, and document images

Workflow:

1. For PDFs, Office docs, HTML, or document images, first run `scripts/extract_with_markitdown.py` and read the generated markdown in `raw/.extracted/`
2. Read the new item in `raw/` or its extracted markdown companion
3. Classify what it contributes: `source`, `concept`, `entity`, `decision`, or `query-worthy synthesis`
4. Create or update a `sources/` page
5. Update affected concept, entity, map, or decision pages instead of duplicating content
6. Update `overview.md` if the big picture changes
7. Update `index.md`
8. Append to `log.md`

Use log entries that include the raw path, and append to `log.md` after every ingest/update so drift checks can detect both new and modified sources, for example:

`## [2026-04-20] ingest | Prompt Design Notes | raw/prompt-design-notes.md`

### QUERY

Use when the user asks a question that should be answered from accumulated wiki knowledge.

1. Read `wiki/index.md`
2. Read the most relevant pages and linked neighbors
3. Answer with citations to wiki pages when possible
4. If the synthesis is durable, store it in `queries/`
5. Update `index.md` and append to `log.md` if a new page was created

### HEALTH

Use when the user asks to check the wiki's integrity or freshness.

Look for:

- raw files not yet ingested
- stale overview or maps
- orphan pages with no useful inbound links
- broken wikilinks
- duplicated pages that should be merged
- concepts mentioned often but missing their own page
- decisions implied in notes but not captured durably

For quick drift detection, use `scripts/check_wiki_drift.py`.

### REFRESH

Use when the wiki exists and many pages were recently touched, or the user wants a refreshed synthesis.

Typical targets:

- `overview.md`
- `maps/*.md`
- `active-questions.md`
- `decisions/` summaries after a batch of related updates

## Page Conventions

Every durable wiki page should start with YAML frontmatter:

```yaml
---
title: Page Title
type: overview | source | concept | entity | decision | query | map
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/example.md]
---
```

Additional conventions:

- start each page with a 1-2 sentence summary
- prefer `[[wikilinks]]` or relative markdown links for cross-references
- keep raw facts on `sources/` pages and reusable synthesis on concept/entity/decision/map pages
- update existing pages before creating near-duplicates
- for binary sources, keep the original file in frontmatter and link the derived markdown cache in the body

Detailed templates and workflows live in:

- `references/operations.md`
- `references/markitdown-ingestion.md`
- `references/page_templates.md`

## Output Expectations

At the end of a wiki task, say what changed in the wiki, not just what you learned.

Typical useful outputs:

- which pages were created or updated
- what remains un-ingested or unresolved
- the current best synthesis
- recommended next source or next question

## Important Rules

- never modify files in `raw/`
- treat `raw/.extracted/` as generated cache, not as the durable source of truth
- if new durable knowledge appears during the task, prefer capturing it once into the wiki instead of re-deriving it later
- if the wiki exists, consult it before rebuilding the same synthesis from scratch
- do not route pure codebase architecture questions here; use `opensource-analyzer`
