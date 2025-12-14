# Known Tensions

Documented contradictions and tradeoffs in CSP design. This file exists to prevent "Cathedral failure modes" where contradictions become undocumented loyalty tests rather than explicit engineering decisions.

## Purpose

When building governance systems, some tensions are unavoidable. The goal isn't to eliminate all contradictions—it's to:

1. **Document them explicitly** rather than leaving them implicit
2. **Decide whether they're acceptable tradeoffs** or bugs to fix
3. **Track resolution** when we fix them

## Tension Log

| ID | Tension | Status | Resolution | Commit |
|----|---------|--------|------------|--------|
| T-001 | ESCALATE appeared in "before execution" list, implying it permits execution | RESOLVED | Clarified: "Only ALLOW permits execution; ESCALATE blocks until subsequent ALLOW" | `9c1a6b0` |
| T-002 | Reference gateway claims "sandbox enforcement" but Python can't enforce OS-level isolation | DOCUMENTED | Added explicit note in MCP_MINIMUM_PROFILE.md: enforcement is OS/container level, gateway can only declare policy | `9c1a6b0` |
| T-003 | Receipt schema allows `passthrough_detected: true` but conformance requires false | DOCUMENTED | Clarified in schema: true indicates blocked violation attempt (forensic evidence), conforming impls MUST emit false | `9c1a6b0` |

## How to Add a Tension

When you discover a say-do gap or logical inconsistency:

1. Add a row to the table above with status `OPEN`
2. Decide: Is this a bug to fix, or an acceptable tradeoff to document?
3. If fixing: update status to `RESOLVED` with commit hash
4. If accepting: update status to `DOCUMENTED` with rationale

## Lint Integration

The `scripts/ritual_lint.py` L3 check:
- Verifies this file exists
- Scans SPEC.md for known "footgun phrases" that suggest undocumented tensions
- Fails CI if new tensions are introduced without documentation

## Philosophy

> "If you're holding A and ~A, label it."

Some contradictions are load-bearing and intentional. Others are bugs. The difference is whether you've explicitly decided. Undocumented contradictions become tribal loyalty tests; documented contradictions become engineering decisions.
