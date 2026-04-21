#!/usr/bin/env python3
"""Scaffold a workspace wiki structure."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

VCS_MARKERS = (".git", ".hg", ".jj")
PROJECT_MARKERS = ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "Gemfile")


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


def main() -> int:
    root = find_workspace_root(Path.cwd())
    raw_dir = root / "raw"
    wiki_dir = root / "wiki"
    today = date.today().isoformat()

    raw_dir.mkdir(parents=True, exist_ok=True)
    wiki_dir.mkdir(parents=True, exist_ok=True)
    for name in ("maps", "concepts", "entities", "sources", "decisions", "queries"):
        (wiki_dir / name).mkdir(parents=True, exist_ok=True)

    write_if_missing(
        wiki_dir / "schema.md",
        "# Wiki Schema\n\n- `raw/` stores immutable source material.\n- `raw/.extracted/` stores generated markdown cache for PDFs, docs, and images.\n- `wiki/` stores maintained knowledge.\n- Update `index.md` and `log.md` whenever the wiki changes.\n",
    )
    write_if_missing(
        wiki_dir / "index.md",
        "# Wiki Index\n\n## Core Pages\n- [Overview](overview.md) — High-level synthesis of the wiki.\n- [Active Questions](active-questions.md) — Open questions and follow-ups.\n",
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
        f"## [{today}] init | Wiki initialized\n",
    )

    print(f"Initialized wiki at: {wiki_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
