#!/usr/bin/env python3
"""Build a wiki dashboard HTML view from the current wiki state."""

from __future__ import annotations

import argparse
from datetime import datetime
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
        if path.is_file() and path.name not in ("index.md", "log.md", "schema.md")
    )


def iter_raw_files(raw_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(raw_dir).parts)
    )


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


def extract_wikilinks(text: str) -> list[str]:
    return re.findall(r"\[\[([^\]]+)\]\]", text)


def fmt_size(bytes_count: int) -> str:
    if bytes_count < 1024:
        return f"{bytes_count}B"
    if bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f}KB"
    return f"{bytes_count / 1024 / 1024:.1f}MB"


def build(root: Path, title: str) -> tuple[str, str]:
    raw_dir = root / "raw"
    wiki_dir = root / "wiki"
    outputs_dir = root / "outputs"
    log_path = wiki_dir / "log.md"
    today = datetime.now().strftime("%Y-%m-%d")

    pages = iter_wiki_pages(wiki_dir)
    page_data: list[dict] = []
    inbound: dict[str, int] = {}

    for page in pages:
        text = page.read_text(encoding="utf-8", errors="ignore")
        fm = extract_frontmatter(text)
        links = extract_wikilinks(text)
        page_data.append({
            "path": page.relative_to(root).as_posix(),
            "stem": page.stem,
            "title": fm.get("title", page.stem),
            "kind": fm.get("type", "page"),
            "date": fm.get("updated", fm.get("created", "")),
        })
        for link in links:
            inbound[link] = inbound.get(link, 0) + 1

    # Inbox: raw files not mentioned in log
    pending: list[dict] = []
    if raw_dir.is_dir() and log_path.is_file():
        log_text = log_path.read_text(encoding="utf-8", errors="ignore")
        buckets: dict[str, list[dict]] = {}
        for raw_file in iter_raw_files(raw_dir):
            rel = raw_file.relative_to(root).as_posix()
            if rel in log_text:
                continue
            bucket = raw_file.relative_to(raw_dir).parts[0] if raw_file.relative_to(raw_dir).parts else "raw"
            buckets.setdefault(bucket, []).append({
                "title": raw_file.stem.replace("-", " "),
                "size": fmt_size(raw_file.stat().st_size),
            })
        for bucket_name, items in sorted(buckets.items()):
            pending.append({"name": bucket_name, "items": items})

    # Today's nodes
    today_nodes = [p for p in page_data if p["date"] == today]

    # Orphan pages: no inbound wikilinks
    orphan_pages = [p for p in page_data if inbound.get(p["stem"], 0) == 0 and p["kind"] not in ("source",)]

    # Top concepts by inbound links
    concepts = [p for p in page_data if p["kind"] == "concept"]
    top_concepts = sorted(concepts, key=lambda p: inbound.get(p["stem"], 0), reverse=True)[:5]

    # Open questions from active-questions.md
    questions: list[str] = []
    aq_path = wiki_dir / "active-questions.md"
    if aq_path.is_file():
        for line in aq_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("-") or stripped.startswith("*"):
                questions.append(stripped.lstrip("-* ").strip())

    # Recent digests from outputs/
    digests: list[dict] = []
    if outputs_dir.is_dir():
        for html in sorted(outputs_dir.glob("*-digest*.html"), reverse=True)[:5]:
            digests.append({
                "title": html.stem.replace("-", " ").replace("digest", "Digest"),
                "html_path": html.name,
                "date": html.stem[:10],
            })

    # Stats
    total_pages = len(page_data)
    total_sources = len([p for p in page_data if p["kind"] == "source"])
    total_links = sum(inbound.values())

    # Recent ingests: count log entries with "ingest |" in last 14 days
    recent_ingests = 0
    if log_path.is_file():
        for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "ingest |" in line:
                try:
                    entry_date = line.split("]")[0].strip("[ ")
                    if entry_date >= (datetime.now().strftime("%Y-%m-%d")[:8] + "01"):
                        recent_ingests += 1
                except Exception:
                    recent_ingests += 1

    # Markdown source
    md_source = f"""---
title: "Wiki Dashboard"
type: digest
tags: [digest, dashboard]
created: {today}
updated: {today}
sources: []
---

> Rendered HTML view: [{today}-wiki-dashboard.html]({today}-wiki-dashboard.html)

Snapshot of {title} as of {today}.

## Stats

- {total_pages} pages
- {total_sources} sources
- {total_links} cross-references
- {recent_ingests} recent ingests
- {len(orphan_pages)} islands

## Recent Growth

{chr(10).join(f"- [[{p['stem']}]]" for p in today_nodes[:10]) or "- No new nodes today."}

## Top Concepts

{chr(10).join(f"- [[{p['stem']}]] ({inbound.get(p['stem'], 0)} citations)" for p in top_concepts) or "- No concepts yet."}

## Open Questions

{chr(10).join(f"- {q}" for q in questions[:5]) or "- No open questions."}
"""

    # HTML output
    html_output = generate_html(title, today, pending, today_nodes, orphan_pages, top_concepts, questions, digests, total_pages, total_sources, total_links, recent_ingests, inbound)

    return md_source, html_output


def generate_html(
    title: str,
    today: str,
    pending: list[dict],
    today_nodes: list[dict],
    orphan_pages: list[dict],
    top_concepts: list[dict],
    questions: list[str],
    digests: list[dict],
    total_pages: int,
    total_sources: int,
    total_links: int,
    recent_ingests: int,
    inbound: dict[str, int],
) -> str:
    pending_html = ""
    for bucket in pending:
        chips = "".join(
            f'<span class="chip">{item["title"]} <span class="chip-meta">{item["size"]}</span></span>'
            for item in bucket["items"][:8]
        )
        if len(bucket["items"]) > 8:
            chips += f'<span class="chip">+ {len(bucket["items"]) - 8} more</span>'
        pending_html += f"""
        <div class="bucket">
          <div class="bucket-header">
            <span class="bucket-name">{bucket["name"]}</span>
            <span class="badge active">{len(bucket["items"])}</span>
          </div>
          <div class="page-chips">{chips}</div>
        </div>
        """
    if not pending_html:
        pending_html = '<div class="meta">收件箱空了。</div>'

    nodes_html = "".join(
        f"""
        <div class="node-item">
          <div class="node-kind">{p['kind']}</div>
          <div>
            <div class="node-title"><a href="../{p['path']}">{p['title']}</a></div>
            <div class="node-meta">· {inbound.get(p['stem'], 0)} 条引用</div>
          </div>
        </div>
        """
        for p in today_nodes[:10]
    )
    if not nodes_html:
        nodes_html = '<div class="meta">今天还没有新节点。</div>'

    top_html = "".join(
        f'<li><a href="../{p["path"]}">{p["title"]}</a> · {inbound.get(p["stem"], 0)} 次引用</li>'
        for p in top_concepts
    ) or "<li>还没有概念页。</li>"

    questions_html = "".join(f"<li>{q}</li>" for q in questions[:5]) or "<li>没有问题。</li>"

    digests_html = "".join(
        f'<li><a href="{d["html_path"]}">{d["title"]}</a> · {d["date"]}</li>'
        for d in digests
    ) or "<li>还没有 digest。</li>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Wiki Dashboard</title>
  <link rel="stylesheet" href="tokens.css" />
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font-body);
      background: var(--paper);
      color: var(--text-primary);
      line-height: 1.6;
    }}
    .container {{
      max-width: var(--max-width);
      margin: 0 auto;
      padding: var(--sp-6) var(--sp-5);
    }}
    header.page-header {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: var(--sp-6);
      padding-bottom: var(--sp-4);
      border-bottom: 1px solid var(--hairline);
    }}
    h1 {{ font-family: var(--font-display); font-size: 2rem; margin: 0; }}
    .meta {{ color: var(--text-muted); font-size: 0.9rem; }}
    .grid {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: var(--sp-5);
      margin-bottom: var(--sp-5);
    }}
    @media (max-width: 860px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .card {{
      background: var(--paper-raised);
      border: 1px solid var(--hairline);
      border-radius: var(--radius);
      padding: var(--sp-5);
      box-shadow: 0 1px 2px var(--shadow-soft);
    }}
    .card h2 {{
      font-family: var(--font-display);
      font-size: 1.25rem;
      margin: 0 0 var(--sp-4) 0;
      display: flex;
      align-items: center;
      gap: var(--sp-3);
    }}
    .card h2::after {{ content: ""; flex: 1; height: 1px; background: var(--hairline); }}
    .count {{ color: var(--text-muted); font-size: 0.85rem; font-family: var(--font-mono); }}
    .bucket-list {{ display: flex; flex-direction: column; gap: var(--sp-4); }}
    .bucket {{ border-left: 3px solid var(--accent-coral); padding-left: var(--sp-4); }}
    .bucket-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-2); }}
    .bucket-name {{ font-weight: 600; font-family: var(--font-serif); }}
    .badge {{
      display: inline-flex; align-items: center;
      padding: var(--sp-1) var(--sp-2); border-radius: var(--radius-sm);
      font-size: 0.75rem; font-family: var(--font-mono);
      background: var(--paper-sunk); color: var(--text-secondary);
    }}
    .badge.active {{ background: rgba(122, 140, 100, 0.12); color: var(--accent-moss); }}
    .page-chips {{ display: flex; flex-wrap: wrap; gap: var(--sp-2); }}
    .chip {{
      display: inline-flex; align-items: center; gap: var(--sp-2);
      padding: var(--sp-2) var(--sp-3); background: var(--paper);
      border: 1px solid var(--hairline); border-radius: var(--radius-sm);
      font-size: 0.85rem;
    }}
    .chip-meta {{ color: var(--text-muted); font-family: var(--font-mono); font-size: 0.75rem; }}
    .node-list {{ display: flex; flex-direction: column; gap: var(--sp-3); }}
    .node-item {{
      display: flex; gap: var(--sp-3); align-items: flex-start;
      padding: var(--sp-3); background: var(--paper);
      border: 1px solid var(--hairline); border-radius: var(--radius-sm);
    }}
    .node-kind {{ font-size: 0.7rem; font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.03em; color: var(--text-muted); min-width: 4.5rem; }}
    .node-title {{ font-weight: 600; margin-bottom: var(--sp-1); }}
    .node-meta {{ font-size: 0.8rem; color: var(--text-secondary); }}
    .peripheral-strip {{
      display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--sp-5);
      margin-bottom: var(--sp-5);
    }}
    @media (max-width: 860px) {{ .peripheral-strip {{ grid-template-columns: 1fr; }} }}
    .peripheral-list {{ list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: var(--sp-2); }}
    .peripheral-list li {{ font-size: 0.9rem; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    footer.stats {{ display: flex; gap: var(--sp-6); padding-top: var(--sp-5); border-top: 1px solid var(--hairline); }}
    .stat {{ text-align: center; }}
    .stat-num {{ font-family: var(--font-display); font-size: 2rem; line-height: 1; color: var(--text-primary); }}
    .stat-label {{ font-size: 0.8rem; color: var(--text-muted); margin-top: var(--sp-1); }}
    a {{ color: var(--text-link); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="container">
    <header class="page-header">
      <div>
        <h1>{title}</h1>
        <div class="meta">Wiki Dashboard · 最后更新 {today}</div>
      </div>
      <div class="meta">
        <a href="../wiki/index.md">索引</a> ·
        <a href="../wiki/log.md">日志</a> ·
        <a href="{today}-wiki-dashboard.md">编辑源文件</a>
      </div>
    </header>

    <div class="grid">
      <section class="card">
        <h2>待处理 <span class="count">{sum(len(b['items']) for b in pending)} 项</span></h2>
        <div class="bucket-list">{pending_html}</div>
      </section>

      <section class="card">
        <h2>今日生长 <span class="count">{len(today_nodes)} 节点</span></h2>
        <div class="node-list">{nodes_html}</div>
        <div style="margin-top: var(--sp-4); padding-top: var(--sp-4); border-top: 1px solid var(--hairline);">
          <span class="badge">孤岛 {len(orphan_pages)}</span>
          <span class="meta" style="margin-left: var(--sp-2);">没有入站引用的页面</span>
        </div>
      </section>
    </div>

    <div class="peripheral-strip">
      <section class="card">
        <h2>高频概念</h2>
        <ul class="peripheral-list">{top_html}</ul>
      </section>
      <section class="card">
        <h2>待回答问题</h2>
        <ul class="peripheral-list">{questions_html}</ul>
      </section>
      <section class="card">
        <h2>最近 Digest</h2>
        <ul class="peripheral-list">{digests_html}</ul>
      </section>
    </div>

    <footer class="stats">
      <div class="stat"><div class="stat-num">{total_pages}</div><div class="stat-label">页面</div></div>
      <div class="stat"><div class="stat-num">{total_sources}</div><div class="stat-label">源</div></div>
      <div class="stat"><div class="stat-num">{total_links}</div><div class="stat-label">交叉引用</div></div>
      <div class="stat"><div class="stat-num">{recent_ingests}</div><div class="stat-label">近两周 ingest</div></div>
    </footer>
  </div>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a wiki dashboard HTML view.")
    parser.add_argument("--root", type=Path, help="Wiki root directory.")
    parser.add_argument("--title", default="Workspace Wiki", help="Wiki title displayed on dashboard.")
    parser.add_argument("--date", help="Override dashboard date (YYYY-MM-DD).")
    args = parser.parse_args(argv or sys.argv[1:])

    root = args.root.resolve() if args.root else find_workspace_root(Path.cwd())
    outputs_dir = root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    md_source, html_output = build(root, args.title)

    md_path = outputs_dir / f"{date_str}-wiki-dashboard.md"
    html_path = outputs_dir / f"{date_str}-wiki-dashboard.html"

    md_path.write_text(md_source, encoding="utf-8")
    html_path.write_text(html_output, encoding="utf-8")

    print(f"dashboard markdown -> {md_path.relative_to(root)}")
    print(f"dashboard html     -> {html_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
