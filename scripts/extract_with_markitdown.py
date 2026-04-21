#!/usr/bin/env python3
"""Convert raw workspace documents into markdown cache using MarkItDown."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import sys

VCS_MARKERS = (".git", ".hg", ".jj")
PROJECT_MARKERS = (
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "Gemfile",
)
EXTRACTED_DIRNAME = ".extracted"


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


def iter_visible_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(root).parts)
    )


def resolve_input_path(root: Path, raw_dir: Path, raw_path_text: str) -> Path:
    candidate = Path(raw_path_text)
    candidates: list[Path] = []

    if candidate.is_absolute():
        candidates.append(candidate.resolve())
    else:
        candidates.append((Path.cwd() / candidate).resolve())
        candidates.append((root / candidate).resolve())
        candidates.append((raw_dir / candidate).resolve())

    for resolved in candidates:
        if resolved.exists():
            return resolved

    raise FileNotFoundError(f"Input path does not exist: {raw_path_text}")


def ensure_under_raw(source: Path, raw_dir: Path) -> Path:
    try:
        source.relative_to(raw_dir)
    except ValueError as exc:
        raise ValueError(
            f"Source must live under {raw_dir}. Stage the original file in raw/ first: {source}"
        ) from exc
    return source


def collect_sources(root: Path, raw_dir: Path, args: argparse.Namespace) -> list[Path]:
    if args.all:
        return iter_visible_files(raw_dir)

    sources: list[Path] = []
    seen: set[Path] = set()

    for raw_path_text in args.paths:
        resolved = ensure_under_raw(resolve_input_path(root, raw_dir, raw_path_text), raw_dir)
        expanded = iter_visible_files(resolved) if resolved.is_dir() else [resolved]
        for item in expanded:
            if item not in seen:
                sources.append(item)
                seen.add(item)

    return sources


def build_markitdown(args: argparse.Namespace):
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError(
            "MarkItDown is not installed. Install it with: pip install 'markitdown[all]'"
        ) from exc

    kwargs: dict[str, object] = {"enable_plugins": args.use_plugins}

    if args.docintel_endpoint:
        kwargs["docintel_endpoint"] = args.docintel_endpoint

    if args.llm_model:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The openai package is required for --llm-model. Install it with: pip install openai"
            ) from exc

        client_kwargs: dict[str, object] = {}
        if args.openai_base_url:
            client_kwargs["base_url"] = args.openai_base_url
        kwargs["llm_client"] = OpenAI(**client_kwargs)
        kwargs["llm_model"] = args.llm_model
        if args.llm_prompt:
            kwargs["llm_prompt"] = args.llm_prompt

    return MarkItDown(**kwargs)


def extracted_markdown_path(raw_dir: Path, source: Path) -> Path:
    rel = source.relative_to(raw_dir)
    return raw_dir / EXTRACTED_DIRNAME / rel.parent / f"{rel.name}.md"


def extracted_metadata_path(raw_dir: Path, source: Path) -> Path:
    rel = source.relative_to(raw_dir)
    return raw_dir / EXTRACTED_DIRNAME / rel.parent / f"{rel.name}.meta.json"


def is_up_to_date(source: Path, markdown_path: Path, metadata_path: Path, force: bool) -> bool:
    if force or not markdown_path.is_file() or not metadata_path.is_file():
        return False
    source_mtime_ns = source.stat().st_mtime_ns
    return (
        source_mtime_ns <= markdown_path.stat().st_mtime_ns
        and source_mtime_ns <= metadata_path.stat().st_mtime_ns
    )


def convert_one(markitdown, root: Path, raw_dir: Path, source: Path, args: argparse.Namespace) -> str:
    markdown_path = extracted_markdown_path(raw_dir, source)
    metadata_path = extracted_metadata_path(raw_dir, source)

    if is_up_to_date(source, markdown_path, metadata_path, args.force):
        return f"skip      {source.relative_to(root).as_posix()} -> {markdown_path.relative_to(root).as_posix()}"

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    result = markitdown.convert(source, keep_data_uris=args.keep_data_uris)
    markdown_path.write_text(result.markdown, encoding="utf-8")

    metadata = {
        "source_path": source.relative_to(root).as_posix(),
        "extracted_markdown_path": markdown_path.relative_to(root).as_posix(),
        "converted_at": datetime.now(timezone.utc).isoformat(),
        "source_modified_at": datetime.fromtimestamp(
            source.stat().st_mtime, timezone.utc
        ).isoformat(),
        "markitdown_version": importlib.metadata.version("markitdown"),
        "title": result.title,
        "markdown_characters": len(result.markdown),
        "text_characters": len(result.text_content or ""),
        "used_plugins": args.use_plugins,
        "llm_model": args.llm_model,
        "docintel_endpoint": args.docintel_endpoint,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return f"converted {source.relative_to(root).as_posix()} -> {markdown_path.relative_to(root).as_posix()}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert files under raw/ into markdown cache under raw/.extracted/ "
            "using MarkItDown."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "Paths to raw files or directories. Paths may be absolute, workspace-relative, "
            "or raw/-relative."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Convert every visible file under raw/ except hidden cache directories.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-convert even when raw/.extracted output is already newer than the source.",
    )
    parser.add_argument(
        "--use-plugins",
        action="store_true",
        help="Enable installed MarkItDown plugins.",
    )
    parser.add_argument(
        "--llm-model",
        help="Optional multimodal model name for image- and slide-aware extraction.",
    )
    parser.add_argument(
        "--llm-prompt",
        help="Optional custom prompt passed through to MarkItDown's LLM-backed converters.",
    )
    parser.add_argument(
        "--openai-base-url",
        help="Optional OpenAI-compatible base URL used when --llm-model is set.",
    )
    parser.add_argument(
        "--docintel-endpoint",
        help="Optional Azure Document Intelligence endpoint for supported document parsing.",
    )
    parser.add_argument(
        "--keep-data-uris",
        action="store_true",
        help="Preserve embedded data URIs in the extracted markdown output.",
    )

    args = parser.parse_args(argv)
    if not args.all and not args.paths:
        parser.error("Provide one or more raw paths, or pass --all.")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = find_workspace_root(Path.cwd())
    raw_dir = root / "raw"

    if not raw_dir.is_dir():
        print("raw/ does not exist yet. Initialize the wiki first or stage source files under raw/.")
        return 1

    try:
        sources = collect_sources(root, raw_dir, args)
        markitdown = build_markitdown(args)
    except Exception as exc:
        print(f"error: {exc}")
        return 1

    if not sources:
        print("No visible source files found under raw/.")
        return 0

    converted = 0
    skipped = 0
    failed = 0

    for source in sources:
        try:
            message = convert_one(markitdown, root, raw_dir, source, args)
            print(message)
            if message.startswith("converted"):
                converted += 1
            else:
                skipped += 1
        except Exception as exc:
            failed += 1
            rel = source.relative_to(root).as_posix()
            print(f"failed    {rel} ({exc})")

    print(
        f"summary   converted={converted} skipped={skipped} failed={failed} "
        f"cache={raw_dir.joinpath(EXTRACTED_DIRNAME).relative_to(root).as_posix()}"
    )
    if converted > 0:
        print("next      ingest from the extracted markdown, then update wiki/sources, index.md, and log.md")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
