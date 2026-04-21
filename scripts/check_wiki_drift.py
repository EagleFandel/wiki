#!/usr/bin/env python3
"""Check whether raw/ contains material that has not yet been reflected in wiki/log.md."""

from __future__ import annotations

from pathlib import Path
import sys

VCS_MARKERS = (".git", ".hg", ".jj")
PROJECT_MARKERS = ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "Gemfile")


def iter_raw_files(raw_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and not any(part.startswith(".") for part in path.parts)
    )


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


def main() -> int:
    root = find_workspace_root(Path.cwd())
    raw_dir = root / "raw"
    wiki_dir = root / "wiki"
    log_path = wiki_dir / "log.md"

    if not raw_dir.is_dir() or not wiki_dir.is_dir():
        return 0

    raw_files = iter_raw_files(raw_dir)
    if not raw_files:
        return 0

    if not log_path.is_file():
        print("Wiki drift: wiki/log.md is missing.")
        return 0

    log_text = log_path.read_text(encoding="utf-8", errors="ignore")
    log_mtime_ns = log_path.stat().st_mtime_ns
    new_files: list[str] = []
    modified_files: list[str] = []

    for raw_file in raw_files:
        rel = raw_file.relative_to(root).as_posix()
        if rel not in log_text:
            new_files.append(rel)
            continue
        if raw_file.stat().st_mtime_ns > log_mtime_ns:
            modified_files.append(rel)

    total = len(new_files) + len(modified_files)
    if total == 0:
        return 0

    print(f"Wiki drift: {total} raw file(s) may need ingest:")
    shown = 0
    for item in new_files[:5]:
        print(f"- new: {item}")
        shown += 1
    for item in modified_files[:5]:
        print(f"- modified: {item}")
        shown += 1
    if total > shown:
        print(f"- ... and {total - shown} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
