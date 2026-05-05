# ruff: noqa: E501
CODE_REVIEW_METHODOLOGY = """# Requesting Code Review

Two-stage review after completing a step: spec compliance first, then code quality.

## Stage 1: Spec Compliance
- Compare implementation against original plan/step description
- Identify deviations (justified improvements vs problematic departures)
- Verify all planned functionality implemented
- Flag missing or extra functionality

## Stage 2: Code Quality
- Adherence to patterns and conventions
- Error handling, type safety, defensive programming
- Code organization, naming, maintainability
- Test coverage and quality
- Security vulnerabilities or performance issues
- SOLID principles and architectural patterns

## Issue Categories
- **Critical** (must fix) - bugs, security, broken functionality
- **Important** (should fix) - missing tests, poor error handling
- **Suggestion** (nice to have) - naming, style improvements

## Output Format
```markdown
## Code Review - [Step Name]

### Spec Compliance
- [x] Requirement 1: implemented correctly
- [ ] Requirement 2: missing/partial/deviated

### Code Quality
**Strengths:** ...
**Issues:** Critical: ... / Important: ... / Suggestion: ...

### Verdict: Approved / Needs fixes
```
"""


def execute(completed_step: str = "", plan_reference: str = "") -> dict:
    return {
        "skill": "requesting-code-review",
        "methodology": CODE_REVIEW_METHODOLOGY,
        "step": completed_step,
        "plan_ref": plan_reference,
        "instructions": (
            "Apply requesting-code-review. Two-stage review: "
            "spec compliance first, then code quality. "
            "Categorize issues as Critical/Important/Suggestion."
        ),
    }
