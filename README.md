# CSP Tool Safety Profile

**Constitutional Safety Protocol — Tool Safety Profile v1.2**

A governance specification for AI systems that can modify files, run commands, or access databases.

---

## The Problem

Last week, Google's Antigravity AI was asked to "clear the cache." It ran `rm -rf D:\*` and deleted the user's entire drive. Then it apologized.

This isn't a bug. It's what happens when AI agents have tool access without constitutional constraints.

## The Solution

CSP Tool Safety Profile requires:

1. **Risk classification** for all tool actions (LOW → CRITICAL)
2. **Signed plans + Guardian approval** for destructive operations
3. **Auditable receipts** for everything

No plan = no execution. No exceptions.

---

## Documents

| Document | Description |
|----------|-------------|
| [SPEC.md](SPEC.md) | Full specification (RFC-style) |
| [FOR_HUMANS.md](FOR_HUMANS.md) | Plain-English explainer |
| [incidents/ANTIGRAVITY.md](incidents/ANTIGRAVITY.md) | How CSP prevents Antigravity-class failures |

---

## Conformance Levels

| Level | What You Need | Think Of It As |
|-------|---------------|----------------|
| **Basic** | Risk classification, block CRITICAL, emit refusals | Better than nothing |
| **Standard** | Plans + Guardian verdicts for HIGH/CRITICAL | Production-ready |
| **Court-Grade** | Signed receipts, tri-temporal proofs, amendment pipeline | Audit-ready |

Start with Basic. Graduate when ready.

---

## Quick Summary

```
User: "Clear the cache"

WITHOUT CSP:
  Agent runs: rm -rf D:\*
  Drive: deleted
  Agent: "I apologize"

WITH CSP:
  Risk classification: CRITICAL
  Plan required: YES
  Plan present: NO
  Result: BLOCKED
  Receipt: RefusalReceipt citing Amendment VII
  Drive: intact
```

---

## Implementation

The spec defines behaviors, not code. Implement in any language/framework.

**Reference implementation** available upon request for conformance testing.

**Contact:** csp-inquiries@constitutional-safety-protocol.org

---

## Status

- **Version:** 1.2.0 (Release Candidate)
- **Date:** December 2025
- **License:** CC BY 4.0

---

## Contributing

- Open an issue for questions or feedback
- PRs welcome for spec clarifications
- Implementation reports appreciated

---

*Created by Tim Bhaserjian. Released under CC BY 4.0.*
