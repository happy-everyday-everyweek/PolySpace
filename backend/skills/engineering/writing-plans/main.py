# ruff: noqa: E501
WRITING_PLANS_METHODOLOGY = """# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

## Scope Check

If the spec covers multiple independent subsystems, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]
**Architecture:** [2-3 sentences about approach]
**Tech Stack:** [Key technologies/libraries]
---
```

## Task Structure

Each task should include:
- **Files:** exact paths to create, modify, and test
- **Steps:** with checkboxes, each containing actual code (not placeholders)
- **Verification:** exact commands with expected output

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code)
- Steps that describe what to do without showing how
- References to types, functions, or methods not defined in any task

## Self-Review

After writing the complete plan, check the plan against the spec:

**1. Spec coverage:** Can you point to a task that implements each requirement? List any gaps.

**2. Placeholder scan:** Search your plan for red flags from the "No Placeholders" section. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names in later tasks match what you defined in earlier tasks?

If you find issues, fix them inline. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, offer execution choice:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — execute tasks in this session with checkpoints for review

## Remember
- Exact file paths always
- Complete code in every step
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
"""


def execute(spec_content: str = "", tech_stack: str = "") -> dict:
    return {
        "skill": "writing-plans",
        "methodology": WRITING_PLANS_METHODOLOGY,
        "spec": spec_content,
        "tech_stack": tech_stack,
        "instructions": (
            "Apply the writing-plans methodology. Create a detailed implementation "
            "plan with bite-sized tasks. No placeholders. Complete code in every step. "
            "TDD, YAGNI, DRY. Offer execution choice after saving."
        ),
    }
