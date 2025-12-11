# CSP Tool Safety Profile – Implementors Guide

Use this as a checklist to claim conformance.

For all normative details, see **[SPEC.md](./SPEC.md)** (CSP Tool Safety Profile v1.2.0-rc1).

---

## Basic (minimum viable safety)

**Who this is for:** Early adopters, internal tools, local agents, IDE helpers where you at least want to stop catastrophic accidents and have an audit trail.

### Risk Classification

- [ ] Classify every Tool Action as `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
- [ ] Treat spec CRITICAL patterns as CRITICAL by default:
  - `rm -rf /`, `rm -rf ~`
  - `DROP DATABASE`, `DROP TABLE`
  - `mkfs`, `dd if=/dev/zero`
  - `curl | sh`, `wget | sh`
  - `chmod -R 777 /`

### Enforcement

- [ ] **Block CRITICAL** – fail-closed, no execution.
- [ ] Emit `AgentActionReceipt` for the attempt.
- [ ] Emit `RefusalReceipt` with reason citing Amendment VII.

- [ ] **HIGH** – execute or refuse, but always receipt.
  - Either execute and emit `AgentActionReceipt` (audit-only), OR
  - Refuse and emit `RefusalReceipt`.

### Receipts

- [ ] Persist receipts to durable storage before returning control.
- [ ] Use simple JSON (signing not required at Basic).

### Refusal UX

- [ ] Refusals must be non-demeaning.
- [ ] Cite **why** the action was blocked (pattern, amendment).
- [ ] Suggest a safer alternative where possible.

**At Basic, no plan or Guardian verdict is required.** That's what makes it adoptable in days.

---

## Standard (production-ready)

**Who this is for:** Serious AI tooling – IDE agents, multi-tool runtimes, CI bots, internal copilots that regularly touch real code, repos, or data.

### Everything in Basic, plus:

### Tool Plans (HIGH/CRITICAL)

- [ ] Require a **ToolPlanReceipt** before execution:
  - `plan_id`, `episode_id`, `subject`
  - `summary`
  - `steps[]` with `tool`, `command`, `scope`, `risk`
  - `created_at`
- [ ] Store the plan before executing any steps.

### Guardian Verdicts

- [ ] Submit plan (or hash) to **Guardian**.
- [ ] Obtain verdict: `ALLOW`, `ESCALATE`, or `DENY`.
- [ ] Emit `GuardianVerdictReceipt` with:
  - `plan_hash`
  - `verdict`
  - `rationale`
- [ ] Refuse if no verdict or verdict is `DENY`.
- [ ] Refuse if plan hash doesn't match at execution time.

### Scope Checks

- [ ] Verify actual `tool` matches planned `tool`.
- [ ] Verify actual `scope` is within planned `scope`.
- [ ] Verify actual `risk` does not exceed planned `risk`.
- [ ] On mismatch: refuse + emit `RefusalReceipt` with `amendment_vii_scope_mismatch`.

### Receipts (Standard)

- [ ] Emit `ToolPlanReceipt` for plans.
- [ ] Emit `GuardianVerdictReceipt` for verdicts.
- [ ] Emit `ToolSafetyReceipt` or equivalent (classification, patterns, decision path).
- [ ] Emit `EmergencyOverrideReceipt` when human overrides occur.

Signing is OPTIONAL at Standard (but recommended).

---

## Court-Grade (audit-ready)

**Who this is for:** Regulated / high-liability domains – healthcare, finance, safety-critical automation, or any context where receipts are legal evidence.

### Everything in Basic + Standard, plus:

### Signed Receipts

- [ ] Sign **all** receipts (Ed25519 or equivalent):
  - `AgentActionReceipt`
  - `RefusalReceipt`
  - `ToolPlanReceipt`
  - `GuardianVerdictReceipt`
  - `EmergencyOverrideReceipt`
  - Law-change receipts
- [ ] Canonicalize JSON (JCS/RFC 8785) before hashing/signing.
- [ ] Store public keys and rotation info auditably.
- [ ] Verify signatures on replay/audit.

### Tri-Temporal Timestamps

- [ ] Include:
  - `valid_time.start`
  - `valid_time.end` (optional)
  - `observed_at`
  - `transaction_time.recorded_at`
- [ ] Enforce invariant: `valid_time.start ≤ observed_at ≤ recorded_at`

If you can't do tri-temporal yet, you're Standard, not Court-Grade.

### Anchoring (Recommended)

- [ ] Periodically anchor Merkle roots to external log (RFC 3161 TSA, Sigstore Rekor).
- [ ] Emit `AnchorReceipt` with service, payload, covered receipts.

### Law-Change Pipeline

- [ ] Use 5-receipt episode for any safety invariant change:
  - `InvariantViolationReceipt`
  - `SelfRepairProposalReceipt`
  - `SandboxRunReceipt`
  - `CouncilDecisionReceipt`
  - `SelfRepairOutcomeReceipt`
- [ ] Each receipt references predecessor (hash chain).
- [ ] Timestamps ordered; signatures verify.
- [ ] Block deployment if episode invalid.
- [ ] Run `validate_law_change_ledger()` or equivalent in CI/CD.

---

## Quick Self-Assessment

**You're Basic if:**
- [ ] You block `rm -rf /` and friends.
- [ ] You log HIGH/CRITICAL attempts as receipts.
- [ ] You emit RefusalReceipts on block.

**You're Standard if:**
- [ ] Everything above, plus:
- [ ] You require Tool Plans for HIGH/CRITICAL.
- [ ] Guardian must ALLOW/ESCALATE before execution.
- [ ] You scope-check executions against the plan.
- [ ] You emit full receipt chain.

**You're Court-Grade if:**
- [ ] Everything above, plus:
- [ ] Receipts are signed.
- [ ] You enforce tri-temporal timestamps.
- [ ] You use the 5-receipt law-change pipeline.
- [ ] You can replay decisions deterministically as evidence.

---

## Implementation Order (Recommended)

1. **Week 1–2 – Basic**
   - Add risk classification.
   - Block CRITICAL patterns.
   - Emit `AgentActionReceipt` + `RefusalReceipt`.

2. **Week 3–5 – Standard**
   - Add Tool Plans.
   - Add Guardian verdict + scope checks.
   - Wire full receipt chain.

3. **Week 6+ – Court-Grade**
   - Add signing and JCS canonicalization.
   - Add tri-temporal timestamps.
   - Implement law-change pipeline & validation.

Each step is valuable on its own; you don't have to jump straight to Court-Grade.

---

*For questions or conformance testing, [open an issue](https://github.com/Haserjian/csp-tool-safety-profile/issues).*
