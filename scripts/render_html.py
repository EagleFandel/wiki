#!/usr/bin/env python3
"""Render a markdown file in outputs/ to HTML."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

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


def try_huashu_md_html(md_path: Path, theme: str, output_path: Path) -> bool:
    """Try rendering with huashu-md-html if available."""
    commands = [
        ["python", "-m", "huashu_md_html.render", str(md_path), "--theme", theme, "--output", str(output_path)],
        ["python", "-m", "huashu_md_html", str(md_path), "--theme", theme, "--output", str(output_path)],
        ["huashu-md-html", str(md_path), "--theme", theme, "--output", str(output_path)],
    ]
    for cmd in commands:
        if shutil.which(cmd[0]) or (cmd[0] == "python" and shutil.which("python")):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    return True
            except Exception:
                continue
    return False


def try_pandoc(md_path: Path, output_path: Path, root: Path) -> bool:
    """Fallback to pandoc with tokens.css."""
    if not shutil.which("pandoc"):
        return False
    tokens_css = root / "outputs" / "tokens.css"
    css_arg = f"--css={tokens_css}" if tokens_css.is_file() else ""
    cmd = ["pandoc", str(md_path), "-o", str(output_path), "--standalone"]
    if css_arg:
        cmd.append(css_arg)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a markdown file to HTML.")
    parser.add_argument("markdown", help="Path to the markdown file to render.")
    parser.add_argument(
        "--theme",
        default="report",
        choices=("article", "report", "reading", "interactive"),
        help="Theme for huashu-md-html rendering.",
    )
    parser.add_argument("--output", help="Output HTML path (defaults to same name with .html).")
    parser.add_argument("--root", type=Path, help="Wiki root directory.")
    args = parser.parse_args(argv or sys.argv[1:])

    md_path = Path(args.markdown).resolve()
    if not md_path.is_file():
        print(f"error: markdown file not found: {md_path}")
        return 1

    root = args.root.resolve() if args.root else find_workspace_root(Path.cwd())
    output_path = Path(args.output).resolve() if args.output else md_path.with_suffix(".html")

    if try_huashu_md_html(md_path, args.theme, output_path):
        print(f"rendered with huashu-md-html ({args.theme}) -> {output_path.relative_to(root)}")
        return 0

    if try_pandoc(md_path, output_path, root):
        print(f"rendered with pandoc -> {output_path.relative_to(root)}")
        return 0

    print("error: no renderer available.")
    print("  Install huashu-md-html, or install pandoc, or render manually.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
