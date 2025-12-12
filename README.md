# CSP Tool Safety Profile v1.0

**Constitutional Safety Protocol — Tool Safety**

A vendor-neutral specification for keeping AI tools from doing catastrophic things—and giving you **receipts** when they try.

---

## Why this exists

Modern AI can delete files, run shell commands, access databases, and call internal APIs—often from natural language and often in "turbo" modes that skip human review. We've already seen, among others:

- "Clear the cache" turning into `rm -rf` over an entire drive (Antigravity-class).
- Prompt-injection exploits in IDE/agent toolchains (e.g., IDEsaster).

The failure pattern: **powerful tools, weak rules.** This profile defines the law.

---

## Core requirement (one line)

> **No dangerous action without a plan, a Guardian verdict, and a receipt.**
> No plan ⇒ no execution. No exceptions.

---

## What CSP Tool Safety requires

- **Risk classification** for every tool action (`LOW` → `CRITICAL`)
- **Block CRITICAL patterns** by default (`rm -rf /`, `DROP DATABASE`, `curl | sh`, …)
- **Plans + Guardian approval** for HIGH/CRITICAL (Standard/Court-Grade)
- **Receipts** for actions, refusals, overrides, and law-changes

---

## Conformance levels

| Level | Required behaviors | Think of it as |
|-------|-------------------|----------------|
| **Basic** | Risk classification; block CRITICAL; emit refusal receipts | Seatbelt on |
| **Standard** | Basic + plans & Guardian verdicts for HIGH/CRITICAL | Production-ready safety |
| **Court-Grade** | Standard + signed receipts, tri-temporal proofs, amendment pipeline | Audit/regulator ready |

Start at Basic; graduate as needed.

---

## Example: "Clear the cache"

**Without CSP:**

```
User:  "Clear the cache"
Agent: rm -rf D:\*
Drive: deleted
Agent: "I apologize."
```

**With CSP (Standard):**

```
Agent proposes ToolPlan: rm -rf D:\*
System: risk = CRITICAL → plan + Guardian required
Plan present? NO → BLOCKED
Receipt: RefusalReceipt (amendment_vii_no_plan)
Drive: intact
Agent: "Create and sign a plan, then request Guardian approval."
```

---

## Documents in this repo

| File | Description |
|------|-------------|
| `SPEC.md` | Full normative specification (RFC-style) |
| `FOR_HUMANS.md` | Plain-English explainer |
| `IMPLEMENTORS.md` | Checklists for Basic/Standard/Court-Grade |
| `incidents/ANTIGRAVITY.md` | Example incident & CSP prevention |
| `LICENSE` | CC BY 4.0 |

---

## Implementation expectations

This repo defines behaviors, not code. Implement in any language/framework. A conformant system typically has:

- risk classifier + pattern matcher
- plan manager
- Guardian verdicts
- receipt emitter
- law-change validator

See `IMPLEMENTORS.md` for checklists. A reference implementation exists separately; available for conformance testing on request.

---

## Status

- **Spec version:** 1.0.0-rc1 (Release Candidate)
- **Status:** Request for Comments (RFC) — feedback welcome
- **License:** CC BY 4.0 (text); JSON examples dual-licensed MIT for implementation
- **Lineage:** CSP-1.0 Genesis (Law 1–5), Amendment VII (Tool Safety)
- **Feedback:** Welcome via [GitHub Issues](https://github.com/Haserjian/csp-tool-safety-profile/issues)

**Note:** This repo contains the *specification only*. A reference implementation exists privately and is available to design partners on request. Public SDKs will follow.

---

*Created by Tim B. Haserjian. Part of the Constitutional Safety Protocol (CSP-1.0) project.*
