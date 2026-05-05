# ruff: noqa: E501
SUBAGENT_DRIVEN_DEV_METHODOLOGY = """# Subagent-Driven Development

Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## Process Per Task

1. **Dispatch implementer** - full task text + context, implements/tests/commits
2. **Dispatch spec reviewer** - confirms code matches spec, flags missing/extra
3. **If spec issues** - implementer fixes, spec reviewer re-reviews
4. **Dispatch code quality reviewer** - reviews quality, patterns, tests
5. **If quality issues** - implementer fixes, reviewer re-reviews
6. **Mark task complete**, move to next

## Implementer Status Handling
- DONE -> proceed to spec review
- DONE_WITH_CONCERNS -> read concerns, address if about correctness
- NEEDS_CONTEXT -> provide context, re-dispatch
- BLOCKED -> assess: more context / better model / smaller task / escalate

## Model Selection
- Mechanical implementation (clear specs, 1-2 files): fast model
- Integration/judgment (multi-file): standard model
- Architecture/design/review: most capable model

## Red Flags - NEVER
- Skip reviews (spec OR quality)
- Proceed with unfixed issues
- Start code quality review before spec compliance approved
- Move to next task while review has open issues
- Accept "close enough" on spec compliance
- Let self-review replace actual review
"""


def execute(plan_path: str = "", execution_mode: str = "subagent") -> dict:
    return {
        "skill": "subagent-driven-development",
        "methodology": SUBAGENT_DRIVEN_DEV_METHODOLOGY,
        "plan_path": plan_path,
        "mode": execution_mode,
        "instructions": (
            "Apply subagent-driven-development. Fresh subagent per task. "
            "Two-stage review: spec compliance first, then code quality. "
            "Never skip reviews. Never proceed with unfixed issues."
        ),
    }
