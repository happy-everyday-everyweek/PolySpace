# ruff: noqa: E501
GRILL_WITH_DOCS_METHODOLOGY = """# Grill with Docs

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Domain awareness

During codebase exploration, also look for existing documentation:

### File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives.

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen.

CONTEXT.md format:
- Be opinionated. When multiple words exist for the same concept, pick the best one and list the others as aliases to avoid.
- Flag conflicts explicitly.
- Keep definitions tight. One sentence max. Define what it IS, not what it does.
- Show relationships. Use bold term names and express cardinality where obvious.
- Only include terms specific to this project's context.
- Write an example dialogue.

Don't couple `CONTEXT.md` to implementation details. Only include terms that are meaningful to domain experts.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR.

ADR format:
- Title and 1-3 sentences: what's the context, what did we decide, and why.
- Optional sections: Status, Considered Options, Consequences — only when they add genuine value.
- Sequential numbering: `0001-slug.md`, `0002-slug.md`, etc.
"""


def execute(plan_description: str = "", focus_area: str = "") -> dict:
    return {
        "skill": "grill-with-docs",
        "methodology": GRILL_WITH_DOCS_METHODOLOGY,
        "plan": plan_description,
        "focus_area": focus_area,
        "instructions": (
            "Apply the grill-with-docs methodology. Challenge the plan against the "
            "existing domain model, sharpen terminology, and update documentation inline. "
            "Ask questions one at a time. Explore the codebase when questions can be "
            "answered by code inspection."
        ),
    }
