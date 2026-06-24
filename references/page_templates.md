# Page Templates

## Source Page

```md
---
title: Source Title
type: source
tags: [source]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/articles/source-file.md]
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

## Entity Page

```md
---
title: Entity Name
type: entity
tags: [entity]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
---

One paragraph summary of the entity and its relevance.

## Description
- ...

## Relationships
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

## Digest Page

```md
---
title: Digest Title
type: digest
tags: [digest]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
---

One paragraph summary of the period and what changed.

## New Sources
- ...

## New or Updated Pages
- ...

## Patterns
- ...

## Contradictions
- ...

## Emerging Questions
- ...

## Suggested Next Steps
- ...
```

## Map Page

```md
---
title: Topic Map Title
type: map
tags: [map]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
---

One paragraph overview of this topic area.

## Key Concepts
- [[Concept A]]
- [[Concept B]]

## Key Entities
- [[Entity X]]
- [[Entity Y]]

## Relationships
- ...

## Coverage Gaps
- ...
```
