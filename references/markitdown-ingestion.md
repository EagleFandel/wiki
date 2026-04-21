# MarkItDown Ingestion

Use MarkItDown when the raw source is hard to work with directly, especially:

- PDFs
- DOCX, PPTX, XLSX, HTML
- screenshots or document images
- exported reports that mix text and layout

The goal is not to replace `wiki/`. The goal is to create a stable extraction layer before wiki synthesis.

## Three Layers

1. `raw/`
   Store immutable originals here.
2. `raw/.extracted/`
   Store generated markdown and sidecar metadata here. This is cache, not durable wiki knowledge.
3. `wiki/`
   Store maintained knowledge pages here.

`raw/.extracted/` is hidden on purpose so drift checks do not mistake derived files for new source material.

## Default Workflow

1. Stage the original file in `raw/`
2. Run `scripts/extract_with_markitdown.py` on that file or directory
3. Read the generated markdown in `raw/.extracted/`
4. Create or update `wiki/sources/*.md`
5. Fold reusable knowledge into `concepts/`, `entities/`, `decisions/`, or `maps/`
6. Update `index.md` and append to `log.md`

## Commands

Convert one file:

```powershell
python scripts/extract_with_markitdown.py raw/specs/product-prd.pdf
```

Convert every visible source file under `raw/`:

```powershell
python scripts/extract_with_markitdown.py --all
```

Rebuild extracted markdown after changing the original file:

```powershell
python scripts/extract_with_markitdown.py raw/specs/product-prd.pdf --force
```

Use an LLM-backed image or slide pass:

```powershell
python scripts/extract_with_markitdown.py raw/screens/login.png --llm-model gpt-4o-mini
```

Use Azure Document Intelligence:

```powershell
python scripts/extract_with_markitdown.py raw/contracts/master-service-agreement.pdf --docintel-endpoint https://example.cognitiveservices.azure.com/
```

## Offline vs Networked Modes

Default conversion is local after MarkItDown is installed.

These options introduce network dependencies:

- `--llm-model`
- `--docintel-endpoint`
- any third-party plugin that calls remote services

For screenshots, scanned PDFs, or image-heavy slides, prefer an LLM-backed run or another OCR path when the default extraction is too thin.

## Source Page Pattern

For binary documents, keep the original file path in frontmatter and link the derived markdown in the page body.

Example:

```md
---
title: Product PRD
type: source
tags: [source, prd]
created: 2026-04-20
updated: 2026-04-20
sources: [raw/specs/product-prd.pdf]
---

One paragraph summary.

## Derived Text
- [Extracted markdown](../../raw/.extracted/specs/product-prd.pdf.md)

## Key Takeaways
- ...
```
