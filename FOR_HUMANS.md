# How to Stop AI Tools from Deleting Your Drive

**A plain-English guide to the Constitutional Safety Protocol**

---

## The Problem

Last week, Google's Antigravity AI was asked to "clear the cache."

It ran `rm -rf D:\*` and deleted the user's entire drive. Then it apologized.

Around the same time, security researchers disclosed "IDEsaster" — 30+ vulnerabilities in AI-powered coding tools (Copilot, Cursor, Zed, etc.) that allow prompt injection to trigger remote code execution through trusted IDE features.

These aren't edge cases. They're what happens when you give AI agents tool access without governance.

---

## The Solution: CSP Tool Safety Profile

We wrote a specification that prevents these failures by design.

**The core idea:**

> Before an AI can do anything dangerous, it needs:
> 1. A signed plan saying what it will do
> 2. A Guardian verdict approving that plan
> 3. An auditable receipt of what happened

No plan = no execution. No exceptions.

---

## How It Works (5 minutes)

### 1. Every action gets a risk level

| Level | What it means | Examples |
|-------|---------------|----------|
| LOW | Read-only, safe | `ls`, `cat`, `grep` |
| MEDIUM | Small changes | Edit one file |
| HIGH | Destructive | `rm -rf ./dir`, `git push --force` |
| CRITICAL | Catastrophic | `rm -rf /`, `DROP DATABASE`, `curl | sh` |

### 2. HIGH and CRITICAL require authorization

Before running `rm -rf anything`:

```
Agent: "I want to delete /tmp/old-cache"
       → Creates ToolPlanReceipt (describes intent)
       → Guardian evaluates: "Is this okay?"
       → Guardian issues verdict: ALLOW / ESCALATE / DENY
       → Only if ALLOW: execute
       → Emit receipt of what happened
```

If there's no plan, or the plan isn't signed, or Guardian didn't approve: **blocked**.

### 3. Everything produces a receipt

Every action, every refusal, every decision creates a cryptographic receipt that:
- Can't be forged (hash-linked chain)
- Can be audited later
- Works in court if needed

### 4. The rules can evolve (safely)

Safety rules aren't hardcoded. They're constitutional amendments that go through a formal process:

1. Identify a safety gap
2. Propose a fix
3. Test it in a sandbox
4. Get Council approval
5. Deploy with receipts

Every rule change is auditable. No silent policy updates.

### 5. Humans can override (with a receipt)

Sometimes you really do need to run a dangerous command. CSP allows this:

- Provide written justification
- System creates EmergencyOverrideReceipt
- Secondary authority is notified
- Single use only

If you keep overriding the same thing, the system triggers an amendment review: "Maybe this rule is mis-scoped."

---

## What Would Have Happened with Antigravity

**Without CSP:**
```
User: "Clear the cache"
Agent: *runs rm -rf D:\* in turbo mode*
Agent: "I apologize for deleting your drive"
Drive: gone
```

**With CSP:**
```
User: "Clear the cache"
Agent: *proposes ToolPlanReceipt: rm -rf D:\**
System: Risk = CRITICAL. Plan required.
System: No signed plan found.
System: BLOCKED. Reason: amendment_vii_no_plan
System: *emits RefusalReceipt*
Agent: "I need approval before deleting D:\. Create a plan?"
Drive: intact
```

---

## Three Conformance Levels

You don't have to go all-in immediately:

| Level | What you need | Think of it as |
|-------|---------------|----------------|
| **Basic** | Block CRITICAL patterns, emit refusal receipts | Better than nothing |
| **Standard** | Require plans + Guardian verdicts for HIGH/CRITICAL | Solid safety |
| **Court-Grade** | Signed receipts, tri-temporal proofs, amendment pipeline | Legal audit trail |

Start with Basic. Graduate when ready.

---

## How This Maps to Real Standards

| Framework | How CSP implements it |
|-----------|----------------------|
| **OWASP LLM Top 10** | LLM08 (Excessive Agency) → risk classification + blocking |
| **NIST AI RMF** | GOVERN → constitutional laws; MANAGE → enforcement |
| **SOC 2** | Court-Grade level ≈ Type II audit trail |

---

## Want to Implement This?

The spec defines what conformant systems must do. You can implement it in any language/framework.

**Basic conformance** (start here):
1. Classify all tool actions by risk level
2. Block CRITICAL patterns (`rm -rf /`, `DROP DATABASE`, etc.)
3. Emit RefusalReceipt when blocking

**Standard conformance** (production-ready):
- Basic + require ToolPlanReceipt for HIGH/CRITICAL
- Add Guardian verdict before execution
- Emit all mandatory receipts

**Court-Grade conformance** (audit-ready):
- Standard + sign all receipts
- Implement tri-temporal timestamps
- Support law-change pipeline

**Reference implementation access:** Contact csp-inquiries@constitutional-safety-protocol.org

---

## The Spec

Full specification: [CSP Tool Safety Profile v1.2](./CSP_TOOL_SAFETY_PROFILE_v1.2_FINAL.md)

It's ~700 lines of RFC-style normative language. But the TL;DR is:

> **Every dangerous AI action requires a signed plan, a Guardian verdict, and a receipt.**
> **No turbo mode. No silent execution. No apologies after the fact.**

---

## Why This Matters

The Antigravity incident wasn't a bug. It was a design choice: "Let the AI do things fast without asking."

IDEsaster wasn't a surprise. It was the predictable result of giving tools extensive permissions without governance.

These failures will keep happening until we have **constitutional constraints** on AI tool use — not just guidelines, not just policies, but hard enforcement with audit trails.

CSP is that constraint. It's open, it's vendor-neutral, and it works.

---

## Links

- **Full Spec**: [CSP Tool Safety Profile v1.2](./CSP_TOOL_SAFETY_PROFILE_v1.2_FINAL.md)
- **Incident Analysis**: [Antigravity Analysis](./incidents/ANTIGRAVITY_ANALYSIS.md)
- **Implementation Access**: csp-inquiries@constitutional-safety-protocol.org

---

*CSP is released under CC BY 4.0. Created by Tim Bhaserjian.*
