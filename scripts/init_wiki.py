#!/usr/bin/env python3
"""Scaffold a workspace wiki structure with schema, templates, and git support."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import shutil
import subprocess
import sys

VCS_MARKERS = (".git", ".hg", ".jj")
PROJECT_MARKERS = ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "Gemfile")

SKILL_DIR = Path(__file__).resolve().parent.parent


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def candidate_roots(start: Path) -> list[Path]:
    resolved = start.resolve()
    return [resolved, *resolved.parents]


def find_marker_root(candidates: list[Path], markers: tuple[str, ...]) -> Path | None:
    for candidate in candidates:
        if any((candidate / marker).exists() for marker in markers):
            return candidate
    return None


def find_workspace_root(start: Path) -> Path:
    candidates = candidate_roots(start)
    boundary = find_marker_root(candidates, VCS_MARKERS)
    scoped = candidates[: candidates.index(boundary) + 1] if boundary else candidates

    for candidate in scoped:
        if (candidate / "raw").is_dir() or (candidate / "wiki").is_dir():
            return candidate

    if boundary is not None:
        return boundary

    project_root = find_marker_root(scoped, PROJECT_MARKERS)
    if project_root is not None:
        return project_root

    return start.resolve()


SCHEMA_TEMPLATE = """# {title} — Schema

## Purpose

{purpose}
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
type: source | concept | entity | decision | query | map | digest
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/articles/example.md]
---
```

- Start each page with a 1-2 sentence summary.
- Use lowercase, hyphenated filenames.
- Cross-reference with `[[wikilinks]]` or relative markdown links.

## Taxonomy

- `source`, `concept`, `entity`, `decision`, `query`, `map`, `digest`

## Output Formats

- Markdown reports for editing and archiving.
- HTML views for reading, sharing, and dashboards.
- Marp slide decks for presentations.
- Matplotlib charts for data visualization.

If `huashu-md-html` is available, render outputs with these themes:
- essay / deep article → `article`
- technical report / whitepaper → `report`
- reading-only distribution → `reading`
- tutorial / explainer / digest → `interactive`
- dashboard → use `outputs/dashboard-template.html`

## Ingest Procedure

1. Read the new source in `raw/` (or its extracted markdown companion in `raw/.extracted/`).
2. For web articles, ensure images are downloaded to `raw/assets/` and links are local.
3. Classify contributions: `source`, `concept`, `entity`, `decision`, `query-worthy synthesis`.
4. Create or update the relevant `sources/` page.
5. Update affected concept, entity, map, or decision pages.
6. Update `wiki/overview.md` if the big picture changes.
7. Update `wiki/index.md`.
8. Append to `wiki/log.md`.

## Lint Checklist

- [ ] Every page in `wiki/` appears in `wiki/index.md`.
- [ ] Every `[[wikilink]]` resolves to a real file.
- [ ] No two pages cover the same concept.
- [ ] Conflicting claims are flagged, not silently overwritten.
- [ ] Sources in `raw/` are reflected in `wiki/log.md`.
"""


def copy_skill_reference(root: Path, name: str, dest_dir: Path) -> None:
    source = SKILL_DIR / "references" / name
    if source.exists():
        shutil.copy2(source, dest_dir / name)


def init_git(root: Path) -> None:
    if not (root / ".git").exists():
        try:
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        except Exception:
            pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a workspace wiki structure.")
    parser.add_argument("title", nargs="?", default="Workspace Wiki", help="Wiki title.")
    parser.add_argument("purpose", nargs="?", default="A compounding knowledge base for this workspace.", help="One-line purpose.")
    parser.add_argument("--root", type=Path, help="Force a specific root directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    root = args.root.resolve() if args.root else Path.cwd().resolve()
    title = args.title
    purpose = args.purpose
    raw_dir = root / "raw"
    wiki_dir = root / "wiki"
    outputs_dir = root / "outputs"
    today = date.today().isoformat()

    # raw layer
    for sub in ("inbox", "articles", "papers", "assets", ".extracted"):
        (raw_dir / sub).mkdir(parents=True, exist_ok=True)

    # wiki layer
    wiki_dir.mkdir(parents=True, exist_ok=True)
    for name in ("maps", "concepts", "entities", "sources", "decisions", "queries"):
        (wiki_dir / name).mkdir(parents=True, exist_ok=True)

    # output layer
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # schema contract
    write_if_missing(
        root / "AGENTS.md",
        SCHEMA_TEMPLATE.format(title=title, purpose=purpose),
    )

    # mirror schema in wiki for browsing
    write_if_missing(
        wiki_dir / "schema.md",
        SCHEMA_TEMPLATE.format(title=title, purpose=purpose),
    )

    # baseline pages
    write_if_missing(
        wiki_dir / "index.md",
        "# Wiki Index\n\n## Core Pages\n"
        "- [Overview](overview.md) — High-level synthesis of the wiki.\n"
        "- [Active Questions](active-questions.md) — Open questions and follow-ups.\n",
    )
    write_if_missing(
        wiki_dir / "overview.md",
        "# Overview\n\nThis wiki is initialized but not yet populated.\n",
    )
    write_if_missing(
        wiki_dir / "active-questions.md",
        "# Active Questions\n\n- What should be ingested first?\n",
    )
    write_if_missing(
        wiki_dir / "log.md",
        f"## [{today}] init | Wiki initialized | {title}\n",
    )

    # reference templates for HTML output
    copy_skill_reference(root, "tokens.css", outputs_dir)
    copy_skill_reference(root, "dashboard-template.html", outputs_dir)

    # git
    init_git(root)

    print(f"Initialized wiki at: {root}")
    print(f"  raw/      -> {raw_dir}")
    print(f"  wiki/     -> {wiki_dir}")
    print(f"  outputs/  -> {outputs_dir}")
    print(f"  AGENTS.md -> {root / 'AGENTS.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
