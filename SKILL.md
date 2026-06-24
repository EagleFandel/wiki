---
name: wiki
description: "Build and maintain a persistent workspace wiki - a compounding knowledge base of interlinked markdown files inspired by Karpathy's LLM Wiki pattern, adapted for real project work. TRIGGER when: user says 'add to wiki', 'ingest this', 'update the wiki', 'start a wiki', asks synthesis questions over accumulated sources, wants a research/project knowledge base, or requests a wiki health check, drift check, or gap analysis. Also use when a workspace already has wiki/ and the answer would benefit from persistent project knowledge. Good inputs include articles, papers, notes, meeting summaries, product context, PR notes, ADRs, screenshots, pasted text, PDFs, Office docs, HTML exports, web clips, and document images. DO NOT TRIGGER for source-code architecture analysis alone; use opensource-analyzer for that."
---

# Wiki

This skill turns one-off research and project context into a **persistent, compounding knowledge base**.

Use it when the user does not just want an answer right now, but wants the answer to become part of the workspace's memory.

The key shift from RAG: instead of retrieving and re-synthesizing raw documents on every question, the LLM **compiles** sources into a structured, interlinked wiki once. The wiki then becomes the query layer. Cross-references, contradictions, and synthesis are already written down — not re-derived from scratch each time.

A related framing: **markdown is for production; HTML is for consumption.** The wiki is authored and maintained in markdown because it is token-efficient, diff-friendly, and easy for agents to edit. But when the result is meant to be read, shared, or interacted with, render it as HTML — slide decks, dashboards, visual comparisons, or annotated documents. Do not treat "markdown vs HTML" as a choice; they are two ends of the same workflow.

Core principles:

- `raw/` is immutable source material curated by the user or captured during work
- `raw/.extracted/` is a hidden conversion cache for PDFs, docs, images, and HTML clips
- `wiki/` is the LLM-maintained compiled knowledge layer
- `outputs/` holds durable answers, reports, and derived artifacts from queries
- good answers and syntheses should file back into the wiki so they compound
- the wiki should help with real work: research, onboarding, decisions, product context, recurring questions, and handoffs

## Architecture

Three layers:

1. **Raw sources** (`raw/`): immutable inputs — articles, papers, screenshots, web clips, transcripts, PDFs. The source of truth.
2. **The wiki** (`wiki/`): LLM-generated markdown — summaries, concept/entity pages, comparisons, syntheses. The compiled knowledge layer.
3. **The schema** (`AGENTS.md` or `CLAUDE.md` at the project root, or `wiki/schema.md`): the human-defined contract that tells the agent how to ingest, query, lint, and maintain the wiki. The agent enforces the schema; the human owns it.

## Decision Tree

```text
Does wiki/ exist?
|- No
|  |- User explicitly wants a persistent wiki or says "init/start wiki" -> INIT
|  `- Otherwise answer normally and suggest wiki only if durable memory would help
`- Yes
   |- New or changed files in raw/ not reflected in wiki/log.md? -> INGEST or SYNC
   |- User asks "what do we know about X" / "compare A and B" / "summarize current state" -> QUERY
   |- User asks "check drift" / "health check" / "find gaps" / "lint wiki" -> LINT
   |- User pastes content, notes, meeting summary, PR summary, source URL, PDF, or screenshot to keep -> SAVE TO RAW, then INGEST
   |- User asks for periodic recap / weekly synthesis / "digest this" -> DIGEST
   `- User asks to refresh overview/topic map after many changes -> REFRESH
```

## Recommended Structure

```text
raw/                    # Immutable source material
  inbox/                # Drop zone for new, unprocessed sources
  articles/             # Web articles / HTML clips converted to markdown
  papers/               # Papers / reports
  assets/               # Localized images and attachments
  .extracted/           # Hidden markdown cache generated from PDFs/docs/images
wiki/
  index.md              # Catalog of important pages
  log.md                # Append-only operation log
  schema.md             # Wiki conventions (mirror of project AGENTS.md/CLAUDE.md)
  overview.md           # Current high-level synthesis
  active-questions.md   # Open questions and follow-ups
  maps/                 # Topic maps and relationship overviews
  sources/              # One page per ingested source
  concepts/             # Concepts and reusable ideas
  entities/             # People, companies, projects, tools
  decisions/            # Durable decisions, tradeoffs, ADR-like notes
  queries/              # High-value query answers worth keeping
outputs/                # Derived answers, reports, slide decks, charts, HTML views
```

The wiki should stay intentionally small and useful. Do not create pages just because a folder exists.

## Operations

### INIT

Use when the user wants a persistent workspace wiki.

1. Create `raw/`, `wiki/`, and `outputs/` if missing
2. Scaffold the recommended structure
3. Write baseline `schema.md`, `index.md`, `log.md`, `overview.md`, and `active-questions.md`
4. Create or update the project-level schema file (`AGENTS.md` or `CLAUDE.md`) so future agent sessions read it automatically
5. If `raw/` already has files, immediately queue SYNC/INGEST
6. If the workspace has an instruction or memory file, add a brief note that the project maintains a wiki in `wiki/`
7. Initialize a git repo if one does not exist, and make a baseline commit

If you want deterministic scaffolding, use `scripts/init_wiki.py "Title" "Purpose"`.

### INGEST

Use when there is new durable material to preserve.

Suitable source types:

- articles, papers, docs, notes
- meeting notes and user interviews
- product context and requirements
- PR summaries or architectural decisions
- screenshots with explanatory notes
- PDFs, Office docs, HTML exports, web clips, and document images

Workflow:

1. For PDFs, Office docs, HTML, or document images, first run `scripts/extract_with_markitdown.py` and read the generated markdown in `raw/.extracted/`
2. For web clips / HTML articles, ensure they are saved as markdown in `raw/articles/` with YAML frontmatter (`url`, `clipped`, `title`, `source_type`). Download referenced images to `raw/assets/` so the LLM can view them locally
3. Read the new item in `raw/` or its extracted markdown companion
4. Classify what it contributes: `source`, `concept`, `entity`, `decision`, or `query-worthy synthesis`
5. Create or update a `sources/` page
6. Update affected concept, entity, map, or decision pages instead of duplicating content
7. Update `overview.md` if the big picture changes
8. Update `index.md`
9. Append to `log.md`
10. If git is present, stage the changes and suggest a structured commit

Use log entries that include the raw path, for example:

`## [2026-04-20] ingest | Prompt Design Notes | raw/articles/prompt-design-notes.md`

### SYNC

Use when a batch of sources has accumulated in `raw/` (especially `raw/inbox/`) and the wiki needs to be reconciled.

1. Identify all files in `raw/` newer than the latest `log.md` entry
2. For each file, run a lightweight INGEST pass
3. Detect renamed, deleted, or modified sources and update wiki links accordingly
4. Produce a single SYNC log entry summarizing the batch
5. Stage changes and suggest a single structured commit

### QUERY

Use when the user asks a question that should be answered from accumulated wiki knowledge.

1. Read `wiki/index.md`
2. Read the most relevant pages and linked neighbors
3. Answer with citations to wiki pages when possible
4. If the synthesis is durable or cross-cutting, write it to `outputs/YYYY-MM-DD-query-slug.md` and optionally file a condensed version in `wiki/queries/`
5. Update `index.md` and append to `log.md` if a new page was created

Query answers may take many forms: markdown report, comparison table, slide deck (Marp), chart (matplotlib), or an HTML view for reading and sharing. The important part is that valuable answers are filed back so they compound.

**Output format rule of thumb:**
- If the answer will be edited, extended, or reused by another agent operation → write it as markdown (`.md`).
- If the answer will be read, shared, presented, or interacted with → render it as HTML (`.html`).
- When in doubt, produce both: a markdown source in `outputs/` and a rendered HTML view next to it.

For complex syntheses, prefer HTML: spatial layouts, tabs, collapsible sections, comparison tables, and inline visualizations all make dense knowledge easier to consume than a linear markdown wall.

### DIGEST

Use when the user wants a periodic synthesis — weekly recap, milestone summary, or "what have we learned lately?"

1. Read recent `log.md` entries
2. Read pages created or updated since the last digest
3. Write a synthesis to `outputs/YYYY-MM-DD-digest-slug.md`
4. Render an HTML version at `outputs/YYYY-MM-DD-digest-slug.html` for reading and sharing
5. Surface patterns, contradictions, emerging questions, and suggested next sources
6. Optionally append a short digest entry to `wiki/log.md` and link it from `overview.md`

### LINT / HEALTH

Use when the user asks to check the wiki's integrity or freshness.

Look for:

- raw files not yet ingested
- stale overview or maps
- orphan pages with no useful inbound links
- broken wikilinks
- duplicated pages that should be merged
- concepts mentioned often but missing their own page
- decisions implied in notes but not captured durably
- contradictions between pages
- claims that newer sources may have superseded

For quick drift detection, use `scripts/check_wiki_drift.py`. For a fuller lint, use `scripts/lint_wiki.py`.

### REFRESH

Use when the wiki exists and many pages were recently touched, or the user wants a refreshed synthesis.

Typical targets:

- `overview.md`
- `maps/*.md`
- `active-questions.md`
- `decisions/` summaries after a batch of related updates

## Schema as Contract

The schema is the most important file in the system. A weak schema produces a weak wiki.

Keep it at the project root as `AGENTS.md` (or `CLAUDE.md` for Claude Code) so the agent reads it automatically before every operation. Mirror it in `wiki/schema.md` for human browsing.

The schema should define:

- purpose and scope of the wiki
- directory structure and naming conventions
- page types and frontmatter fields
- cross-reference style (`[[wikilinks]]` vs relative markdown links)
- taxonomy of tags
- conflict-resolution policy
- ingest procedure
- lint checklist
- output formats (reports, slides, charts, HTML views)

The human defines the schema once; the agent enforces it. Update the schema when conventions drift, not on a whim.

## HTML / Web Capture

Web pages are a common source. Treat them as HTML inputs to be converted to markdown, not consumed raw. This keeps the ingestion side aligned with the markdown-as-production principle.

Capture workflow:

1. Use Obsidian Web Clipper or another web-to-markdown browser extension to convert the page to markdown
2. Save to `raw/articles/YYYY-MM-DD-page-title-slug.md`
3. Add YAML frontmatter: `title`, `url`, `clipped`, `source_type: web_clip`, `tags`
4. Download referenced images to `raw/assets/` and rewrite image links to local relative paths
5. Run INGEST

Note: LLMs cannot natively read markdown with inline images in one pass. The workaround is to read the text first, then view selected images separately for additional context.

## Markdown for Production, HTML for Consumption

Do not force a false choice between markdown and HTML.

- **Produce in markdown.** `raw/`, `wiki/`, and operation logs stay in markdown because agents edit it cheaply, diffs are readable, and context windows go further.
- **Consume as HTML.** When a query answer, digest, report, or concept page needs to be read, shared, or interacted with, render it to HTML. HTML is for the human eye; markdown is for the agent hand.

Practical rule of thumb: if you are going to edit it again, keep it markdown. If you are going to show it to someone else or read it without editing, render it HTML.

### When to Render HTML

Favor HTML outputs when the content is:

- **Dense or multi-source**: side-by-side comparisons, evidence matrices, tradeoff tables
- **Spatial**: architecture diagrams, call graphs, timelines, maps
- **Interactive**: dashboards, filters, sortable tables, parameter explorers
- **Narrative and polished**: reports meant for stakeholders, presentations, published essays
- **Visual**: charts, annotated screenshots, color-coded status views

Favor markdown outputs when the content is:

- a working draft the user will edit
- an intermediate artifact for another agent operation
- a log, schema, or source-of-truth page
- constrained by token budget

### How to Render HTML

1. Write the answer first as markdown in `outputs/YYYY-MM-DD-slug.md`.
2. Convert the markdown to HTML using a renderer.
3. Apply a clean, readable CSS theme. Avoid AI-slop defaults: no heavy gradients, no emoji-as-icons, no dark-blue `#0D1117` backgrounds unless requested.
4. Save the HTML as `outputs/YYYY-MM-DD-slug.html`.
5. Link the HTML from the markdown source and from `wiki/log.md` if useful.

#### Using `huashu-md-html`

If the project has `huashu-md-html` installed, prefer it. Map outputs to themes by purpose:

| Output type | Theme |
|---|---|
| Essay / deep article | `article` |
| Technical report / whitepaper | `report` |
| Reading-only distribution | `reading` |
| Tutorial / explainer / digest | `interactive` |
| Dashboard | use `references/dashboard-template.html` instead |

Example:

```bash
python -m huashu_md_html.render outputs/2026-06-21-digest.md --theme interactive
```

#### Fallback

If `huashu-md-html` is not available, use Pandoc with `references/tokens.css` or any minimal markdown-to-HTML tool.

### Output Checklist

- [ ] Markdown source exists in `outputs/` for future editing
- [ ] HTML view exists when the output is for human consumption
- [ ] CSS is clean and readable, not visually noisy
- [ ] Links between markdown source and HTML view are bidirectional
- [ ] The output is linked from `wiki/log.md` or the relevant wiki page

## Page Conventions

Every durable wiki page should start with YAML frontmatter:

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
- `references/html_outputs.md`
- `references/schema-template.md`
- `references/dashboard-template.html`
- `references/tokens.css`

## Git, Versioning, and Epistemic Drift

A wiki is a compiled artifact written by an LLM. Errors introduced during ingest can compound across future ingests. Version control is the safety net.

Recommended practice:

- keep the wiki as a git repo of plain markdown files
- after each significant INGEST, SYNC, or REFRESH, stage changes and make a structured commit
- review diffs before committing, especially when existing pages are modified
- if a claim is wrong, revert the offending commit rather than layering more fixes on top
- run LINT before and after large batches to catch drift early

This human-in-the-loop diff review is the strongest protection against epistemic drift.

## Scale and Limits

The compiled-wiki approach works best when the relevant subset fits in context.

Practical ceiling:

- ~50,000–100,000 tokens of dense wiki text
- roughly 150–250 pages
- ~100 sources per focused topic

Beyond that:

- rely on `index.md` plus selective page loading
- add a local search tool such as `qmd` (BM25 + vector + LLM re-ranking)
- consider a hybrid: compiled wiki for stable core knowledge, RAG for dynamic or overflow content

For multi-user teams, add a coordination layer (git branches + review) because the pattern assumes a single curator.

## Optional Tooling

- **Obsidian**: IDE/viewer for the wiki; graph view shows hubs and orphans
- **Obsidian Web Clipper**: browser extension for one-click web-to-markdown capture
- **qmd**: local markdown search engine; useful when the wiki outgrows the context window
- **Marp**: markdown slide decks from wiki content
- **Dataview**: Obsidian plugin for querying page frontmatter

## Output Expectations

At the end of a wiki task, say what changed in the wiki, not just what you learned.

Typical useful outputs:

- which pages were created or updated
- what was saved to `outputs/`
- what remains un-ingested or unresolved
- the current best synthesis
- recommended next source or next question

## Important Rules

- never modify files in `raw/`
- treat `raw/.extracted/` as generated cache, not as the durable source of truth
- if new durable knowledge appears during the task, prefer capturing it once into the wiki instead of re-deriving it later
- if the wiki exists, consult it before rebuilding the same synthesis from scratch
- do not route pure codebase architecture questions here; use `opensource-analyzer`
- the agent enforces the schema, but the human owns it; do not change schema conventions silently
