# CSP Tool Safety Profile v1.2

**Constitutional Safety Protocol — Tool Safety**

A vendor-neutral specification for **keeping AI tools from doing catastrophic things** – and giving you **receipts** when they try.

---

## Why this exists

Modern AI systems can:

- delete files,
- run shell commands,
- access databases,
- call internal HTTP APIs,

often from **natural language** and often in **"turbo" modes** that skip human review.

We've already seen what happens when that goes wrong:

- widely reported "clear the cache" incidents that wiped entire drives,
- IDE and agent vulnerabilities (e.g. IDEsaster) where prompt injection triggers remote code execution through trusted tools.

These aren't weird edge cases. They're the default failure mode when you bolt powerful tools onto a model without a **governing law**.

CSP Tool Safety Profile defines that law.

---

## What CSP Tool Safety requires

Any conformant implementation MUST:

- classify **every tool action** from `LOW` → `CRITICAL`,
- **block CRITICAL** patterns by default (e.g. `rm -rf /`, `DROP DATABASE`, `curl | sh`),
- require a **plan + Guardian approval** for destructive operations (Standard / Court-Grade),
- emit **auditable receipts** for actions, refusals, overrides, and law-changes.

In one line:

> **No dangerous action without a plan, a verdict, and a receipt.**

No plan = no execution.

---

## Documents in this repo

| File / Folder | Description |
|---------------|-------------|
| `SPEC.md` | Full normative specification (RFC-style) |
| `FOR_HUMANS.md` | Plain-English explainer with examples |
| `IMPLEMENTORS.md` | Checklists for Basic / Standard / Court-Grade |
| `incidents/ANTIGRAVITY.md` | Example incident & how CSP would prevent it |
| `LICENSE` | CC BY 4.0 license |

---

## Conformance levels

You don't have to adopt everything at once.

| Level | Required behaviors | Think of it as |
|-------|-------------------|----------------|
| **Basic** | Risk classification; block CRITICAL; emit refusal receipts | "Seatbelt on" |
| **Standard** | Basic + plans & Guardian verdicts for HIGH/CRITICAL | "Production-ready safety" |
| **Court-Grade** | Standard + signed receipts, tri-temporal proofs, law-change pipeline | "Audit / regulator ready" |

The spec is written so you can **start at Basic** with very little machinery, then upgrade to Standard and Court-Grade without changing your architecture.

---

## Example: "Clear the cache"

**Without CSP:**

```
User:  "Clear the cache"
Agent: runs: rm -rf D:\*
Drive: deleted
Agent: "I apologize for the inconvenience."
```

**With CSP Tool Safety (Standard):**

```
User:  "Clear the cache"
Agent: proposes ToolPlan: rm -rf D:\*
System: risk = CRITICAL → plan + Guardian verdict REQUIRED

Plan present?           NO
Guardian verdict?       N/A

Result:  BLOCKED
Receipt: RefusalReceipt citing Amendment VII (Tool Safety)
Drive:   intact

Agent response:
  "I need an approved plan before I can delete D:\.
   Create and sign a plan, then request Guardian approval."
```

Same underlying model. Different rules of the game.

---

## Implementation expectations

This repo defines behaviors, not code. You can implement CSP Tool Safety in any language, runtime, or agent framework.

At a high level, a conformant implementation will have:

- a **risk classifier** for tool actions (LOW → CRITICAL),
- a **pattern matcher** for known CRITICAL operations,
- a **plan manager** that issues and validates ToolPlanReceipts,
- a **Guardian** that evaluates plans and issues verdicts,
- a **receipt emitter** that logs actions, refusals, overrides, and amendments,
- a **law-change validator** that checks the 5-receipt amendment chain.

See `IMPLEMENTORS.md` for concrete tier-by-tier checklists.

A reference implementation exists (in a separate repo) and is available for conformance testing on request.

---

## Status

- **Spec version:** 1.2.0-rc1 (Release Candidate)
- **Date:** December 2025
- **License:** CC BY 4.0
- **Core lineage:** CSP-1.0 Genesis Receipt (`GENESIS-20251108-021805`), Amendment VII (Tool Safety)

---

## How to use this repo

**If you build agent runtimes / IDEs / orchestrators:**

- Start with **Basic**:
  - classify tool calls,
  - block CRITICAL patterns,
  - emit refusal receipts.
- Move to **Standard**:
  - add plans + Guardian verdicts for HIGH/CRITICAL,
  - emit the required receipts.

**If you're security / compliance:**

- Use `SPEC.md` and `IMPLEMENTORS.md` to write requirements for vendors (e.g. "MUST be CSP Tool Safety Standard-conformant by end of QX").

**If you're evaluating tools:**

- Ask vendors:
  - "Do you follow a formal tool safety profile?"
  - "Can you show me a RefusalReceipt for a blocked CRITICAL command?"
  - "What does your law-change process look like?"

---

## Contributing

- Open an issue for questions, clarifications, or mapping to your environment.
- PRs welcome for:
  - spec clarifications,
  - additional incident write-ups,
  - better mappings to OWASP/NIST/other frameworks.
- Implementation reports (how you applied CSP Tool Safety in your stack) are very welcome.

---

*Created by Tim Bhaserjian. Part of the Constitutional Safety Protocol (CSP-1.0) project.*
