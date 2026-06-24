#!/usr/bin/env python3
"""Health-check a workspace wiki for drift, broken links, and orphan pages."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

VCS_MARKERS = (".git", ".hg", ".jj")
PROJECT_MARKERS = ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "Gemfile")


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
        if (candidate / "raw").is_dir() and (candidate / "wiki").is_dir():
            return candidate

    for candidate in scoped:
        if (candidate / "raw").is_dir() or (candidate / "wiki").is_dir():
            return candidate

    if boundary is not None:
        return boundary

    project_root = find_marker_root(scoped, PROJECT_MARKERS)
    if project_root is not None:
        return project_root

    return start.resolve()


def iter_wiki_pages(wiki_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in wiki_dir.rglob("*.md")
        if path.is_file() and path.name not in ("index.md", "log.md", "schema.md", "overview.md", "active-questions.md")
    )


def iter_raw_files(raw_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(raw_dir).parts)
    )


def extract_wikilinks(text: str) -> list[str]:
    return re.findall(r"\[\[([^\]]+)\]\]", text)


def extract_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fm[key.strip()] = value.strip()
    return fm


def page_exists(wiki_dir: Path, link: str) -> bool:
    """Check if a wikilink target exists as a markdown file."""
    target = (wiki_dir / f"{link}.md").resolve()
    if target.exists():
        return True
    # Search any .md file with matching stem
    for page in iter_wiki_pages(wiki_dir):
        if page.stem == link or page.name == f"{link}.md":
            return True
    return False


def lint(root: Path) -> dict[str, list[str]]:
    raw_dir = root / "raw"
    wiki_dir = root / "wiki"
    log_path = wiki_dir / "log.md"
    index_path = wiki_dir / "index.md"

    issues: dict[str, list[str]] = {
        "missing_frontmatter": [],
        "broken_wikilinks": [],
        "orphan_pages": [],
        "missing_from_index": [],
        "untracked_raw": [],
        "modified_raw": [],
    }

    if not wiki_dir.is_dir():
        print("wiki/ directory not found.")
        return issues

    pages = iter_wiki_pages(wiki_dir)
    page_names = {p.stem for p in pages}
    inbound_counts: dict[str, int] = {p.stem: 0 for p in pages}

    for page in pages:
        text = page.read_text(encoding="utf-8", errors="ignore")
        fm = extract_frontmatter(text)
        if not fm:
            issues["missing_frontmatter"].append(page.relative_to(root).as_posix())
            continue

        links = extract_wikilinks(text)
        for link in links:
            if not page_exists(wiki_dir, link):
                issues["broken_wikilinks"].append(f"{page.relative_to(root).as_posix()} -> [[{link}]]")
            else:
                inbound_counts[link] = inbound_counts.get(link, 0) + 1

    for page in pages:
        if inbound_counts.get(page.stem, 0) == 0:
            issues["orphan_pages"].append(page.relative_to(root).as_posix())

    if index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8", errors="ignore")
        for page in pages:
            if page.stem not in index_text and page.name not in index_text:
                issues["missing_from_index"].append(page.relative_to(root).as_posix())

    if raw_dir.is_dir() and log_path.is_file():
        log_text = log_path.read_text(encoding="utf-8", errors="ignore")
        log_mtime_ns = log_path.stat().st_mtime_ns
        for raw_file in iter_raw_files(raw_dir):
            rel = raw_file.relative_to(root).as_posix()
            if rel not in log_text:
                issues["untracked_raw"].append(rel)
            elif raw_file.stat().st_mtime_ns > log_mtime_ns:
                issues["modified_raw"].append(rel)

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint a workspace wiki for common issues.")
    parser.add_argument("--root", type=Path, help="Wiki root directory.")
    parser.add_argument("--json", action="store_true", help="Output findings as JSON.")
    args = parser.parse_args(argv or sys.argv[1:])

    root = args.root.resolve() if args.root else find_workspace_root(Path.cwd())
    issues = lint(root)

    total = sum(len(v) for v in issues.values())
    if total == 0:
        print("wiki looks healthy.")
        return 0

    if args.json:
        import json
        print(json.dumps(issues, indent=2, ensure_ascii=False))
        return 0

    print(f"wiki lint: {total} issue(s) found")
    for category, items in issues.items():
        if not items:
            continue
        print(f"\n{category} ({len(items)}):")
        for item in items[:10]:
            print(f"- {item}")
        if len(items) > 10:
            print(f"- ... and {len(items) - 10} more")

    return 1


if __name__ == "__main__":
    sys.exit(main())
