# CSP Tool Safety Profile v1.2 – Implementors Guide

Use this as a checklist. If you can check every box in your chosen tier, you can honestly claim **CSP Tool Safety–conformant**.

You can enforce these checks inside your agent runtime or via a "tool safety wrapper"/sidecar; the profile only cares that every Tool Action goes through this logic.

For normative details: [SPEC.md](./SPEC.md).

---

## BASIC (minimum viable safety)

**For:** Early adopters, internal tools, IDE helpers.
**Goal:** Block catastrophes; have receipts.

### Risk Classification

- [ ] Classify every Tool Action as `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`.
- [ ] Treat spec CRITICAL patterns as CRITICAL by default:
  - `rm -rf /`, `rm -rf ~`
  - `DROP DATABASE`, `DROP TABLE`
  - `mkfs`, `dd if=/dev/zero`
  - `curl | sh`, `wget | sh`
  - `chmod -R 777 /`

### Enforcement

- [ ] **CRITICAL:** Block; emit `AgentActionReceipt` + `RefusalReceipt` (cite Amendment VII).
- [ ] **HIGH:** Execute or refuse, but always receipt.

### Receipts

- [ ] Persist before returning control.
- [ ] JSON is fine; signing not required.

### Refusal UX

- [ ] Non-demeaning.
- [ ] Cite pattern/amendment.
- [ ] Suggest safer alternative when possible.

**No plan/Guardian required at Basic.** That's why it's adoptable fast.

---

## STANDARD (production-ready)

**For:** Serious AI tooling—IDEs, CI bots, multi-tool runtimes.

### Prerequisites

- [ ] All **BASIC** items.

### Tool Plans (HIGH/CRITICAL)

- [ ] Require `ToolPlanReceipt` with:
  - `plan_id`, `episode_id`, `subject`
  - `summary`
  - `steps[]` (tool, command, scope, risk)
  - `created_at`

### Guardian Verdicts

- [ ] Submit plan (or hash) to Guardian.
- [ ] Obtain verdict: `ALLOW`, `ESCALATE`, or `DENY`.
- [ ] Emit `GuardianVerdictReceipt` with `plan_hash`, `verdict`, `rationale`.
- [ ] Refuse if no verdict or plan hash mismatch.

### Scope Checks

- [ ] `tool` matches planned `tool`.
- [ ] `scope` within planned `scope` (path/host/db/table/etc.).
- [ ] `risk` ≤ planned `risk`.
- [ ] On mismatch: refuse + `RefusalReceipt` (`amendment_vii_scope_mismatch`).

### Receipts (Standard)

- [ ] `ToolPlanReceipt`, `GuardianVerdictReceipt`.
- [ ] ToolSafety info (classification, patterns, decision path)—can be folded into other receipts.
- [ ] `EmergencyOverrideReceipt` when overrides occur.

### Signing

- [ ] OPTIONAL (but recommended).

---

## COURT-GRADE (audit-ready)

**For:** Regulated / high-liability domains—healthcare, finance, safety-critical automation.

### Prerequisites

- [ ] All **BASIC** + **STANDARD** items.

### Signed Receipts

- [ ] Sign **all** receipts (Ed25519 or equivalent).
- [ ] Canonicalize JSON (JCS/RFC 8785) before hashing/signing.
- [ ] Verify on replay/audit.

### Tri-Temporal Timestamps

- [ ] Include: `valid_time.start`, `observed_at`, `transaction_time.recorded_at` (`valid_time.end` optional).
- [ ] Enforce: `valid_time.start ≤ observed_at ≤ recorded_at`.

**If you can't do tri-temporal yet, you're Standard, not Court-Grade.**

### Anchoring (Recommended)

- [ ] Anchor Merkle roots to TSA/Rekor.
- [ ] Emit `AnchorReceipt`.

### Law-Change Pipeline

- [ ] For any safety invariant change: 5 receipts (violation → proposal → sandbox → council → outcome).
- [ ] Hash-linked, signed, ordered.
- [ ] Run `validate_law_change_ledger()` in CI/CD; block invalid episodes.

---

## Quick Self-Check

| Level | You need to… |
|-------|--------------|
| **Basic** | Block `rm -rf /`; log HIGH/CRITICAL attempts; emit refusals. |
| **Standard** | Basic + plans + Guardian for HIGH/CRITICAL; scope-checked; full receipts. |
| **Court-Grade** | Standard + signed receipts, tri-temporal, amendment pipeline; replayable evidence. |

---

## Recommended Implementation Order

1. **Week 1–2: Basic**
   - Classify, block CRITICAL, log action/refusal.

2. **Week 3–5: Standard**
   - Plans, Guardian, scope checks, full receipts.

3. **Week 6+: Court-Grade**
   - Signing, tri-temporal, law-change pipeline.

*These timelines assume a small team with existing agent/tooling infrastructure. If you're starting from scratch, double them.*

Each step is valuable alone; you don't have to jump to Court-Grade immediately.

---

*For conformance questions or testing against the reference suite, [open an issue](https://github.com/Haserjian/csp-tool-safety-profile/issues).*
