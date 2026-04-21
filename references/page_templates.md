# Page Templates

## Source Page

```md
---
title: Source Title
type: source
tags: [source]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/source-file.md]
---

One paragraph summary of why this source matters.

## Derived Text
- [Extracted markdown](../../raw/.extracted/source-file.pdf.md)

## Key Takeaways
- ...

## Important Claims
- ...

## Related Pages
- [[Concept A]]
- [[Entity B]]
```

## Concept Page

```md
---
title: Concept Name
type: concept
tags: [concept]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
---

One paragraph summary of the concept and why it matters in this workspace.

## Definition
- ...

## Where It Shows Up
- ...

## Related Sources
- [Source X](../sources/source-x.md)
```

## Decision Page

```md
---
title: Decision Title
type: decision
tags: [decision]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
---

One paragraph summary of the decision.

## Context
- ...

## Decision
- ...

## Tradeoffs
- ...

## Follow-up
- ...
```

## Query Page

```md
---
title: Query Title
type: query
tags: [query]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
---

One paragraph answer summary.

## Answer
- ...

## Evidence
- ...

## Open Questions
- ...
```
