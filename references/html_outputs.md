# HTML Outputs

This reference describes how to turn wiki content into polished HTML views for human consumption.

## Guiding Principle

**Markdown is the source; HTML is the view.**

Always keep a markdown source file in `outputs/` that an agent can edit later. The HTML is a rendered artifact for reading, sharing, and interaction.

## When to Render HTML

Favor HTML when the content is:

- dense or synthesized from multiple sources
- spatial (diagrams, timelines, comparison tables)
- interactive (filters, tabs, sortable tables)
- narrative and polished (reports, essays, presentations)
- visual (charts, annotated images, status dashboards)

Favor markdown when the content is:

- a working draft the user will edit
- an intermediate artifact for another operation
- a log, schema, or source-of-truth page
- constrained by token budget

## File Naming

```text
outputs/YYYY-MM-DD-query-slug.md        # markdown source
outputs/YYYY-MM-DD-query-slug.html      # rendered HTML view
outputs/YYYY-MM-DD-digest-slug.md
outputs/YYYY-MM-DD-digest-slug.html
outputs/YYYY-MM-DD-report-slug.md
outputs/YYYY-MM-DD-report-slug.html
```

## Rendering Workflow

1. Write the answer/report/digest as markdown in `outputs/`.
2. Convert the markdown to HTML with a renderer (Pandoc, `huashu-md-html`, or a small Python script).
3. Apply a clean, readable CSS theme.
4. Link the HTML view from the markdown source.
5. Log the output in `wiki/log.md`.

## Output Format Examples

### Comparison Report

A markdown table becomes an HTML table with:

- sticky header
- sortable columns
- row hover states
- color-coded verdict cells
- collapsible evidence sections per row

### Digest

A weekly digest becomes an HTML page with:

- executive summary at the top
- timeline of new sources
- cards for new/updated concepts
- a "contradictions and open questions" section
- suggested next sources as a checklist

### Architecture Explanation

A concept page becomes an HTML explainer with:

- sidebar table of contents
- diagram placeholders
- tabs for "overview / details / tradeoffs / examples"
- inline citations linking back to `wiki/sources/` pages

## Anti-Patterns

Avoid these common AI-slop visual defaults:

- heavy gradients and glassmorphism
- emoji used as icons
- `#0D1117` dark-blue backgrounds unless explicitly requested
- oversized hero sections that push content below the fold
- animated flourishes that do not add information

Prefer typography, whitespace, and consistent color over decoration.

## Included Templates

This skill ships with two reference files you can copy into a project:

- `references/tokens.css` — cream-paper + ink design tokens, light/dark mode, low-saturation accents
- `references/dashboard-template.html` — static wiki dashboard skeleton with inbox, recent nodes, top concepts, open questions, and stats

Use them as starting points. The dashboard template uses mustache-style placeholders (`{{wiki_title}}`, `{{pending_count}}`, etc.) that any renderer can fill.

- `article` — Tufte-style editorial, long essays
- `report` — whitepaper / technical report
- `reading` — Medium-style clean reading
- `interactive` — tutorials and explainers with sidebar navigation

If rendering manually, start with a minimal stylesheet:

- system font stack
- ~65 characters per line for body text
- clear hierarchy: `h1` > `h2` > `h3`
- subtle borders and alternating row backgrounds for tables
- code blocks with light background and monospace font

## Dashboard as a Primary Output

The most valuable HTML view for a compounding wiki is often not a single article but a **dashboard**.

A good wiki dashboard shows:

- inbox of pending sources, grouped by bucket
- today's new nodes / recent growth
- islands (nodes with no inbound links)
- top-cited concepts
- open questions from `wiki/active-questions.md`
- recent digests and query answers
- aggregate stats: pages, sources, cross-links, recent ingests

Generate the dashboard during DIGEST or REFRESH operations, or on demand when the user asks "show me the state of the wiki."

See `references/dashboard-template.html` for a concrete layout.

## Linking Back

Every HTML view should link to its markdown source, and vice versa. Example header in HTML:

```html
<header>
  <h1>Report Title</h1>
  <p><a href="YYYY-MM-DD-report-slug.md">Edit source markdown</a></p>
</header>
```

Example note in markdown:

```markdown
> Rendered HTML view: [YYYY-MM-DD-report-slug.html](YYYY-MM-DD-report-slug.html)
```
