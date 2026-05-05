# ruff: noqa: E501
ZOOM_OUT_METHODOLOGY = """# Zoom Out

I don't know this area of code well. Go up a layer of abstraction. Give me a map of all the relevant modules and callers, using the project's domain glossary vocabulary.

## How to zoom out

1. **Identify the current scope** — what module, file, or concept are you currently looking at?

2. **Go up one level** — what is the parent module, the calling context, or the broader system that this piece belongs to?

3. **Map the neighborhood** — list all sibling modules, callers, and callees. Show how they relate:
   - Who calls this module?
   - What does this module call?
   - What data flows in and out?
   - What events or side effects does it produce?

4. **Use domain language** — name things using the project's `CONTEXT.md` vocabulary, not implementation-specific names. If `CONTEXT.md` defines "Order," talk about "the Order processing module" not "the OrderHandler class."

5. **Highlight the seams** — where are the interfaces between modules? Where could behavior be substituted or tested independently?

6. **Note the depth** — which modules are deep (simple interface, complex implementation) and which are shallow (interface as complex as implementation)?

The goal is to give the user a mental map they can navigate, not an exhaustive listing. Focus on the relationships and data flow that matter for understanding.
"""


def execute(code_area: str = "", question: str = "") -> dict:
    return {
        "skill": "zoom-out",
        "methodology": ZOOM_OUT_METHODOLOGY,
        "code_area": code_area,
        "question": question,
        "instructions": (
            "Apply the zoom-out methodology. Go up a layer of abstraction and provide "
            "a map of the relevant modules and callers. Use domain glossary vocabulary."
        ),
    }
