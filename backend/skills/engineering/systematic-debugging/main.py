# ruff: noqa: E501
SYSTEMATIC_DEBUGGING_METHODOLOGY = """# Systematic Debugging

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## The Iron Law

NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

## The Four Phases (complete each before proceeding)

### Phase 1: Root Cause Investigation
1. Read Error Messages Carefully - don't skip, they often contain the solution
2. Reproduce Consistently - exact steps, every time?
3. Check Recent Changes - git diff, recent commits, new deps
4. Gather Evidence in Multi-Component Systems - log at each boundary
5. Trace Data Flow - where does bad value originate? Fix at source, not symptom

### Phase 2: Pattern Analysis
1. Find Working Examples in same codebase
2. Compare Against References - read COMPLETELY
3. Identify Differences - list every difference
4. Understand Dependencies

### Phase 3: Hypothesis and Testing
1. Form Single Hypothesis - "I think X is the root cause because Y"
2. Test Minimally - smallest change, one variable at a time
3. Verify Before Continuing - if not, form NEW hypothesis
4. When You Don't Know - say so, don't pretend

### Phase 4: Implementation
1. Create Failing Test Case - MUST have before fixing
2. Implement Single Fix - ONE change at a time
3. Verify Fix - test passes, no other tests broken
4. If Fix Doesn't Work: if <3 fixes, return to Phase 1; if >=3, question architecture

## Red Flags - STOP
- "Quick fix for now"
- "Just try changing X"
- Proposing solutions before tracing data flow
- "One more fix attempt" (after 2+)

## Common Rationalizations
| Excuse | Reality |
|--------|---------|
| "Too simple for process" | Simple bugs have root causes too |
| "Emergency, no time" | Systematic is FASTER than thrashing |
| "Just try this first" | Do it right from the start |
| "Multiple fixes at once" | Can't isolate what worked |
| "3+ fixes failed" | Architectural problem, stop fixing |
"""


def execute(bug_description: str = "", error_output: str = "") -> dict:
    return {
        "skill": "systematic-debugging",
        "methodology": SYSTEMATIC_DEBUGGING_METHODOLOGY,
        "bug": bug_description,
        "error": error_output,
        "instructions": (
            "Apply systematic-debugging. NEVER propose fixes without Phase 1. "
            "Follow all 4 phases. If 3+ fixes fail, question architecture."
        ),
    }
