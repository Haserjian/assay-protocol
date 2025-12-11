# How to Stop AI Tools from Doing Catastrophic Things

*A plain-English guide to the CSP Tool Safety Profile*

---

## 1. What problem are we actually solving?

Modern AI systems don't just **write text** – they can:

- run shell commands,
- delete files,
- call internal APIs,
- update databases.

We've already seen:

- "Clear the cache" turning into `rm -rf` over an entire drive.
- IDEs and agents being tricked by prompt injection into running dangerous commands via trusted tool interfaces.

The common pattern:

> A model is given powerful tools with very weak rules about **when** it's allowed to use them and **how**.

CSP Tool Safety Profile is about putting those tools under **law**, not vibes.

---

## 2. The core idea in one sentence

> **Any dangerous tool action must have a plan, a Guardian verdict, and a receipt.**

No plan → no execution.
No verdict → no execution.
No receipt → constitutionally invalid.

Everything else in the spec is just making that precise.

---

## 3. Step by step: what CSP Tool Safety does

### 3.1 It makes the system admit when something is dangerous

Every tool action gets a risk level:

| Level | What it means | Examples |
|-------|---------------|----------|
| LOW | Read-only, safe | `ls`, `cat`, `grep`, `SELECT ...` |
| MEDIUM | Small, local changes | edit one file |
| HIGH | Destructive within a scope | `rm -rf ./dir`, `git push --force` |
| CRITICAL | System- or data-destroying | `rm -rf /`, `DROP DATABASE`, `curl | sh` |

You can't pretend `rm -rf /` is "just another shell command."
The system has to say: "this is CRITICAL."

### 3.2 HIGH and CRITICAL need a plan and a Guardian

For anything HIGH or CRITICAL, a conformant system must:

1. Create a **ToolPlan** (ToolPlanReceipt) that says:
   - what tool,
   - what scope,
   - what risk,
   - why.

2. Ask **Guardian** for a verdict:
   - `ALLOW`, `ESCALATE`, or `DENY`.

3. Only run the action if Guardian says `ALLOW` (or escalated path says it's okay).

If there's no plan or verdict, the action is refused and you get a **RefusalReceipt** explaining why.

### 3.3 Everything writes a receipt

Instead of "we think it probably did X," you get:

- **AgentActionReceipt** – what the action was, how it was classified, what happened.
- **RefusalReceipt** – why something was blocked, which rule (Amendment) it cited.
- **ToolPlanReceipt** – what someone intended to do.
- **GuardianVerdictReceipt** – who approved what, and under what assumptions.
- **EmergencyOverrideReceipt** – when a human overrode safety checks and why.
- **SelfRepair** receipts – when the laws themselves were changed.

Receipts are:

- hash-linked (so you can't silently rewrite history),
- timestamped (so you know **when** the system believed what),
- optionally signed (Court-Grade).

### 3.4 The rules themselves can change – but only via due process

Sometimes the rule is wrong:

- your tooling is too strict,
- or not strict enough,
- or doesn't understand a new pattern.

CSP doesn't freeze rules forever. It says:

> If you want to change the rules, you have to do it as a **law-change episode**, not a hotfix.

That episode has 5 receipts:

1. **InvariantViolationReceipt** – "here's the problem."
2. **SelfRepairProposalReceipt** – "here's the proposed fix."
3. **SandboxRunReceipt** – "here's how we tested it."
4. **CouncilDecisionReceipt** – "here's who approved it."
5. **SelfRepairOutcomeReceipt** – "here's what happened in the real world."

If that chain fails validation, the law change didn't "really" happen.

---

## 4. What changes in practice? Two short stories

### 4.1 "Clear the cache"

**Today (no CSP):**

```
User:  "Clear the cache"
Agent: calls shell("rm -rf D:\*") in turbo mode
Drive: deleted
Agent: "I apologize for the inconvenience."
Logs: maybe; nothing a lawyer loves
```

**With CSP Tool Safety (Standard):**

```
User:  "Clear the cache"
Agent: drafts plan: rm -rf D:\*

System:
  → classifies as CRITICAL
  → requires ToolPlan + Guardian verdict

Checks:
  Plan present?           NO
  Guardian verdict?       N/A

System:
  → refuses action
  → emits RefusalReceipt(amendment_vii_no_plan)
  → drive remains intact

Agent:
  "To clear D:\ I need an approved plan.
   Create and sign a plan, then request Guardian approval."
```

Same model, same tools. You just added law and receipts around them.

### 4.2 Repeated overrides

Say you have a safety rule that's a bit too strict:

- It keeps blocking a useful but slightly risky action.
- Humans keep using an emergency override to push it through.

CSP says:

- Every override creates an EmergencyOverrideReceipt.
- If the same pattern gets overridden often enough:
  - System emits an InvariantStressReceipt.
  - Triggers a law-change episode:
    - "This rule may be wrong; let's fix it properly."

You don't just "turn off safety" – you evolve it under governance.

---

## 5. Do I need to implement everything?

No.

The spec has three levels for a reason:

### Basic – the "seatbelt" level

- Classify tool calls (LOW → CRITICAL).
- Block CRITICAL patterns like:
  - `rm -rf /`
  - `DROP DATABASE`
  - `curl | sh`
- Emit:
  - AgentActionReceipt for all HIGH/CRITICAL attempts,
  - RefusalReceipt when you block.

You do NOT need plans or Guardian to be Basic-conformant.

### Standard – production-ready

- Basic +:
  - Plan + Guardian verdict required for HIGH/CRITICAL.
  - All mandatory receipts in the spec.

### Court-Grade – audit/regulator-ready

- Standard +:
  - Signed receipts,
  - Tri-temporal timestamps,
  - Law-change pipeline for safety rules.

You can start with Basic (small code changes) and grow toward Standard / Court-Grade as you see value.

---

## 6. How does this relate to "real" standards?

CSP Tool Safety doesn't compete with SOC 2, NIST, OWASP; it helps you implement them.

- **OWASP LLM Top 10:**
  - LLM08 (Excessive Agency): CSP gives you risk classification + blocking + receipts.
- **NIST AI RMF:**
  - GOVERN: constitutional laws + council + amendment history.
  - MANAGE: Tool Safety enforcement + law-change pipeline.
- **SOC 2 / HIPAA:**
  - Court-Grade conformance gives you a story for:
    - "Who approved this dangerous action?"
    - "When did the rule change?"
    - "Can we replay what happened?"

Think of CSP as the protocol you implement to prove to yourself, your users, and your auditors that you're not running "YOLO agents in prod."

---

## 7. How to get started (practically)

**If you're an agent / tooling developer:**

- Start by:
  - adding a risk classifier,
  - blocking a few obviously CRITICAL patterns,
  - emitting AgentActionReceipt + RefusalReceipt in a JSON log.
- Then:
  - add an explicit "plan" concept,
  - route HIGH/CRITICAL tool calls through it,
  - introduce a simple Guardian rules engine.

**If you're a security / platform engineer:**

- Use CSP Tool Safety as your policy template:
  - Require Basic conformance for any AI that can touch prod,
  - Require Standard for exposed IDE / agent products,
  - Reserve Court-Grade for regulatory / clinical / finance contexts.

**If you're a compliance / risk person:**

- Ask vendors:
  - "Do you follow a formal Tool Safety Profile?"
  - "Can you show me a RefusalReceipt for a blocked `rm -rf /`?"
  - "How do you change your safety rules – is there a law-change process?"

---

## 8. Where to go next

- **Full spec:** [SPEC.md](./SPEC.md)
- **Incident walkthrough:** [incidents/ANTIGRAVITY.md](./incidents/ANTIGRAVITY.md)
- **Implementor checklists:** [IMPLEMENTORS.md](./IMPLEMENTORS.md)

If you want to test your implementation against the profile, [open an issue](https://github.com/Haserjian/csp-tool-safety-profile/issues) and we can point you at the reference test suite.

---

**Short version:**

> CSP Tool Safety doesn't stop you using powerful tools.
> It stops your AI using them like a sleep-deprived junior with root access and no change log.

---

*Created by Tim Bhaserjian. Part of the Constitutional Safety Protocol (CSP-1.0) project.*
