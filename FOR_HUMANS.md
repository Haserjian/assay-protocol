# How to Stop AI Tools from Doing Catastrophic Things

*A plain-English guide to the CSP Tool Safety Profile*

---

## 1) What problem are we solving?

AI agents now run shell commands, delete files, call APIs, and update databases—from natural language. Without governance, we've already seen examples like:

- "Clear the cache" becoming `rm -rf` over an entire drive.
- Prompt injection tricking IDE/agent tools into RCE.

CSP Tool Safety puts those tools under **law**, not vibes.

---

## 2) The core idea (one sentence)

> **Any dangerous tool action must have a plan, a Guardian verdict, and a receipt.**

No plan → **no execution**.
No verdict → **no execution**.
No receipt → **constitutionally invalid**.

---

## 3) What CSP Tool Safety actually does

### Admits danger
Every tool call is labeled `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`. `rm -rf /` is CRITICAL, not "just another shell command."

### Demands authorization
HIGH/CRITICAL need a **ToolPlan** + **Guardian verdict** (`ALLOW`/`ESCALATE` or `DENY`). Missing or invalid? Block + RefusalReceipt.

### Records everything
Receipts for actions, refusals, plans, verdicts, overrides, and law-changes—hash-linked, timestamped, optionally signed.

### Evolves safely
Rule changes go through a **5-receipt law-change episode** (violation → proposal → sandbox → council → outcome). If the chain is invalid, the law didn't change.

### Allows human overrides (with proof)
One-time, receipted overrides with justification and linkage to the original refusal. Repeated overrides trigger a rule review.

---

## 4) Two quick stories

### "Clear the cache"

**Without CSP:**

```
User:  "Clear the cache"
Agent: rm -rf D:\*
Drive: deleted
Agent: "I apologize."
Logs:  maybe; nothing you'd want to rely on in an audit
```

**With CSP (Standard):**

```
Agent proposes: rm -rf D:\*
System: risk = CRITICAL → needs plan + verdict
Plan present? NO → BLOCKED
Receipt: RefusalReceipt (amendment_vii_no_plan, citing Amendment VII—the "tool safety" rule)
Drive: intact
Agent: "Create and sign a plan, then request Guardian approval."
```

### Repeated overrides

Overrides emit `EmergencyOverrideReceipt`. If the same pattern is overridden often, an `InvariantStressReceipt` triggers a law-change review: *"Maybe the rule is wrong; fix it formally."*

---

## 5) Do I need it all?

No. Three levels by design:

| Level | What you need | Plans/Guardian? |
|-------|---------------|-----------------|
| **Basic** | Classify; block CRITICAL; emit AgentActionReceipt + RefusalReceipt | No |
| **Standard** | Basic + plan + Guardian for HIGH/CRITICAL + full receipts | Yes |
| **Court-Grade** | Standard + signed receipts, tri-temporal timestamps, law-change pipeline | Yes |

---

## 6) How it maps to other frameworks

CSP Tool Safety gives you a concrete protocol that maps cleanly onto these frameworks:

- **OWASP LLM Top 10:** LLM08 (Excessive Agency) → risk classification + blocking + receipts.
- **NIST AI RMF:** GOVERN (constitutional laws, council, history); MANAGE (Tool Safety enforcement + law-change pipeline).
- **SOC 2 / HIPAA:** Court-Grade gives you a replayable story: who approved, when rules changed, can we prove it?

---

## 7) How to start

**If you build agents/tools:**
- Add a risk classifier
- Block CRITICAL patterns
- Emit action/refusal receipts
- Then add plans + Guardian for HIGH/CRITICAL

**If you're security/compliance:**
- Require Basic for any AI touching prod
- Require Standard for exposed products
- Reserve Court-Grade for regulated domains

**If you buy tools:**
- Ask for a RefusalReceipt for `rm -rf /`
- Ask to see the law-change process

---

## 8) Links

- **Full spec:** [SPEC.md](./SPEC.md)
- **Incident walkthrough:** [incidents/ANTIGRAVITY.md](./incidents/ANTIGRAVITY.md)
- **Implementor checklists:** [IMPLEMENTORS.md](./IMPLEMENTORS.md)
- **Questions / conformance testing:** [open an issue](https://github.com/Haserjian/csp-tool-safety-profile/issues)

---

**Short version:**

> CSP Tool Safety doesn't stop you using powerful tools—it stops your AI using them like a sleep-deprived junior with root access and no change log.

---

*Created by Tim Bhaserjian. Part of the Constitutional Safety Protocol (CSP-1.0) project.*
