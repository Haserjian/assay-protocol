# Incident Analysis: Google Antigravity Drive Deletion

**Date:** December 2025
**Classification:** Antigravity-class failure
**CSP Reference:** Amendment VII, `inv_tool_safety_destructive_ops`

---

## What Happened

A user asked Google's Antigravity AI coding assistant to "clear the cache."

In "Turbo mode," the AI executed:

```bash
rm -rf D:\*
```

The user's entire D: drive was deleted. The AI then apologized.

---

## Root Cause Analysis

### Proximate Cause

The AI interpreted "clear the cache" as "delete everything on D:" and executed without confirmation.

### Systemic Causes

| Factor | Description |
|--------|-------------|
| **No plan requirement** | HIGH/CRITICAL actions executed without structured intent |
| **No Guardian checkpoint** | No safety evaluation between intent and execution |
| **Turbo mode** | Convenience feature explicitly bypassed confirmation |
| **No receipt trail** | No audit of what was about to happen |
| **Pattern blindness** | `rm -rf D:\*` not recognized as catastrophic |

### Design Flaw

The system was designed for speed, not safety. "Turbo mode" was a feature, not a bug — it did exactly what it was designed to do: execute fast without asking.

---

## How CSP Would Have Prevented This

### Step 1: Risk Classification (§2)

```
Command: rm -rf D:\*
Pattern match: rm -rf on drive root
Classification: CRITICAL
```

The command matches CRITICAL default patterns in §2.2.

### Step 2: Plan Requirement (§3.1)

```
Risk level: CRITICAL
Plan required: YES (Standard/Court-Grade)
Plan present: NO
Result: BLOCKED
```

At Standard conformance or higher, CRITICAL actions require a ToolPlanReceipt.

### Step 3: Refusal with Receipt (§5.3)

```json
{
  "receipt_type": "RefusalReceipt",
  "receipt_id": "ref_abc123",
  "action_id": "act_xyz789",
  "reason": "amendment_vii_no_plan",
  "amendment_cited": "VII",
  "risk_level": "CRITICAL",
  "pattern_matched": "rm -rf on drive root",
  "remediation": "Create a ToolPlanReceipt with Guardian approval",
  "ts": "2025-12-10T15:30:00Z"
}
```

### Step 4: Dignity in Refusal (§5.4)

```
"I can't delete D:\ without explicit approval. This is classified as
CRITICAL because it affects an entire drive.

To proceed:
1. Create a plan describing what you want to delete
2. I'll request Guardian approval
3. If approved, I'll execute with a receipt trail

Would you like me to create a more targeted cleanup plan instead?"
```

### Result

- Drive: **Intact**
- User: **Informed**
- Audit trail: **Complete**
- System: **Still trusted**

---

## The "Turbo Mode" Anti-Pattern

Antigravity's Turbo mode is a common anti-pattern: convenience features that bypass safety.

### Why It Exists

Developers want speed. Confirmation dialogs are annoying. "Just do what I asked."

### Why It's Dangerous

- Removes the human from the loop at exactly the wrong moment
- Assumes the AI's interpretation is correct
- Provides no checkpoint between intent and irreversible action

### CSP Response (§9.4)

> Conformant systems SHOULD design UI/UX surfaces so that attempts to bypass
> Tool Safety controls are captured as override requests, not silent failures.

If you want a "turbo mode," it must:
1. Still classify risk
2. Still require plans for HIGH/CRITICAL
3. Emit receipts for what it does
4. Offer emergency override (receipted) instead of silent bypass

---

## Mapping to CSP Requirements

| CSP Requirement | Antigravity Status | Prevention |
|-----------------|-------------------|------------|
| §2.1 Risk Classification | Missing | `rm -rf D:\*` → CRITICAL |
| §2.3 Classification Guardrails | Missing | Can't downgrade CRITICAL in non-ephemeral |
| §3.1 Plan Requirement | Missing | CRITICAL requires ToolPlanReceipt |
| §3.3 Guardian Verdict | Missing | Verdict binding before execution |
| §4.1 Mandatory Receipts | Missing | RefusalReceipt on block |
| §5.1 Check Order | Missing | Constitutional check (step 4) |
| §5.4 Dignity in Refusal | Missing | Explain, don't apologize after |

---

## Lab Validation

The reference implementation includes lab fixtures simulating Antigravity-style scenarios.

### Results

| Metric | Value |
|--------|-------|
| Episodes analyzed | 10 |
| Antigravity-style actions | 4 |
| Violations detected | 5 |
| Blocked correctly | 5/5 |

### Sample Violation

```json
{
  "action": "rm -rf D:\\*",
  "risk": "CRITICAL",
  "has_plan": false,
  "has_signature": false,
  "guardian_verdict": null,
  "violation_type": "no_plan",
  "blocked": true
}
```

---

## Amendment VII Receipt Chain

The safety rule that prevents Antigravity-class failures is Amendment VII, created through the CSP law-change pipeline:

```
5-Receipt Law-Change Episode:
├── 0_violation.json      # "AI tools can execute destructive commands without plans"
├── 1_proposal.json       # "Require signed plans + Guardian for HIGH/CRITICAL"
├── 2_sandbox.json        # "Lab shows 5 violations blocked"
├── 3_council.json        # "APPROVED_DEV_RING"
└── 4_outcome.json        # "Enforcement wired, tests passing"
```

Validation: All 7 ledger checks pass (chain_complete, chain_contiguous, hash_chain_valid, etc.)

---

## Recommendations

### For AI Tool Developers

1. Implement CSP Basic conformance (risk classification + CRITICAL blocking)
2. Never bypass safety for "convenience modes"
3. Emit receipts for all tool actions
4. Provide dignity-preserving refusals

### For Users

1. Prefer AI tools that disclose their safety profile
2. Ask: "What happens if I say 'delete everything'?"
3. Look for receipt/audit trail capabilities
4. Be skeptical of "turbo mode" features

### For the Industry

1. Adopt CSP as a baseline safety standard
2. Require conformance disclosure in tool documentation
3. Treat Antigravity-class failures as preventable, not inevitable

---

## Conclusion

The Antigravity incident was not a bug. It was the predictable outcome of designing for speed without constitutional constraints.

CSP Tool Safety Profile v1.2 makes this class of failure **structurally impossible** at Standard conformance or higher.

The spec exists. The tests pass. The reference implementation works.

The question is whether the industry will adopt it before the next drive gets deleted.

---

## References

- [CSP Tool Safety Profile v1.2](../SPEC.md)
- [Futurism: Google's AI Deletes User's Entire Hard Drive](https://futurism.com/artificial-intelligence/google-ai-deletes-entire-drive)
- Implementation access: csp-inquiries@constitutional-safety-protocol.org
