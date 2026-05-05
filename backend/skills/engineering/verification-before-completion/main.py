# ruff: noqa: E501
VERIFICATION_METHODOLOGY = """# Verification Before Completion

**Core principle:** Evidence before claims, always.

## The Iron Law

NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.

## The Gate Function

BEFORE claiming any status:
1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying.

## Red Flags - STOP
- Using "should", "probably", "seems to"
- Expressing satisfaction before verification
- About to commit/push without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"

## Key Patterns
- Tests: [RUN command] [SEE: 34/34 pass] "All tests pass"
- Build: [RUN build] [SEE: exit 0] "Build passes"
- Requirements: Re-read plan -> checklist -> verify each -> report

## The Bottom Line
Run the command. Read the output. THEN claim the result. Non-negotiable.
"""


def execute(claim: str = "", verification_command: str = "") -> dict:
    return {
        "skill": "verification-before-completion",
        "methodology": VERIFICATION_METHODOLOGY,
        "claim": claim,
        "verification_command": verification_command,
        "instructions": (
            "Apply verification-before-completion. NEVER claim success "
            "without running verification. Evidence before assertions."
        ),
    }
