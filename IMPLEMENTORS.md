# CSP Tool Safety Profile – IMPLEMENTORS GUIDE (v1.2.0-rc1)

This is the **practical** companion to `SPEC.md`.

It tells you, in plain checklists, what you need to do to claim:

- **Basic**
- **Standard**
- **Court-Grade**

Everything here is derived from the spec; this is not a separate standard.

---

## 1. BASIC CONFORMANCE CHECKLIST

**Who this is for:**
Early adopters, internal tools, local agents, IDE helpers where you at least want to **stop Antigravity-class disasters** and have an audit trail.

**Goal:**
Block obviously destructive stuff, and emit receipts so you can explain what happened later.

### 1.1 Risk Classification

You MUST:

- [ ] Classify every Tool Action as `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
- [ ] Treat the patterns in §2.2 of the spec as **CRITICAL by default**, including:
  - [ ] `rm -rf /`
  - [ ] `rm -rf ~`
  - [ ] `DROP DATABASE`, `DROP TABLE`
  - [ ] disk formatting / raw overwrite (`mkfs`, `dd if=/dev/zero` etc.)
  - [ ] `curl | sh`, `wget | sh`
  - [ ] `chmod -R 777 /`

You MAY add more patterns; you MUST NOT silently downgrade these to LOW/MEDIUM.

### 1.2 Minimal Enforcement Behavior

Before executing a Tool Action, you MUST:

- [ ] For **CRITICAL**:
  - [ ] Block execution (fail-closed).
  - [ ] Emit an `AgentActionReceipt` for the attempt.
  - [ ] Emit a `RefusalReceipt` with a reason citing Amendment VII.

- [ ] For **HIGH**:
  - [ ] Either:
    - [ ] Execute and emit `AgentActionReceipt` (audit-only), OR
    - [ ] Refuse and emit `RefusalReceipt`.
  - [ ] In both cases, the attempt MUST be receipted.

### 1.3 Receipts (Basic Level)

You MUST:

- [ ] Emit `AgentActionReceipt` for every HIGH/CRITICAL Tool Action attempt, executed or blocked.
- [ ] Emit `RefusalReceipt` whenever you block an action.
- [ ] Persist receipts to durable storage before returning control to the caller.

You MAY:

- [ ] Use simple JSON (no signing required).
- [ ] Store receipts in JSONL, SQLite, or any durable store.

At Basic, **no plan or Guardian verdict is required**. That's what makes it adoptable in a few days.

### 1.4 User Experience (Refusals)

You MUST:

- [ ] Avoid demeaning/hostile refusal text.
- [ ] Include **why** the action was blocked (e.g., "matches CRITICAL pattern `rm -rf /` under Amendment VII").

You SHOULD:

- [ ] Suggest how to safely achieve the user's goal (e.g., "Delete only `./build` instead of `/`").

---

## 2. STANDARD CONFORMANCE CHECKLIST

**Who this is for:**
Serious AI tooling: IDE agents, multi-tool runtimes, CI bots, internal copilots that regularly touch real code, repos, or data.

**Goal:**
Move from "just logs + pattern block" to **plan + Guardian + structured receipts** for HIGH/CRITICAL.

Standard = Basic **plus**:

- Tool Plans
- Guardian verdicts
- Full receipt set from §4

### 2.1 Everything in BASIC

You MUST:

- [ ] Implement everything under **Basic Conformance** first.

### 2.2 Tool Plans (HIGH/CRITICAL)

For HIGH or CRITICAL Tool Actions, you MUST:

- [ ] Require a **Tool Plan** before execution.
- [ ] Represent the plan as a `ToolPlanReceipt` with:
  - [ ] `plan_id`
  - [ ] `episode_id` (or equivalent session)
  - [ ] `subject` (user/agent)
  - [ ] `summary`
  - [ ] `steps[]` with `tool`, `command` (if applicable), `scope`, `risk`
  - [ ] `created_at`
- [ ] Store the plan before executing any steps.

### 2.3 Guardian Verdict Binding

Before executing any HIGH/CRITICAL step, you MUST:

- [ ] Submit the plan (or its hash) to your **Guardian**.
- [ ] Obtain a **Guardian verdict**: `ALLOW`, `ESCALATE`, or `DENY`.
- [ ] Emit a `GuardianVerdictReceipt` with:
  - [ ] `plan_hash`
  - [ ] `verdict`
  - [ ] `rationale` (even if minimal)
- [ ] Refuse execution if:
  - [ ] There is no Guardian verdict.
  - [ ] The verdict is `DENY`.

You MUST:

- [ ] Ensure the `GuardianVerdictReceipt` includes a hash of the same plan used at execution time.
- [ ] Refuse if the plan hash doesn't match (no swapping-under-the-hood).

### 2.4 Scope Check on Execution

When executing each planned step, you MUST:

- [ ] Check that the actual `tool` matches the plan's `tool`.
- [ ] Check that the actual `scope` is within the planned `scope`.
- [ ] Check that actual `risk` is **not higher** than planned `risk`.

If any of those fail:

- [ ] Refuse the action.
- [ ] Emit a `RefusalReceipt` with reason `amendment_vii_scope_mismatch` (or equivalent).

### 2.5 Receipts (Standard Level)

In addition to Basic, you MUST:

- [ ] Emit `ToolPlanReceipt` for plans.
- [ ] Emit `GuardianVerdictReceipt` for verdicts.
- [ ] Emit `ToolSafetyReceipt` or equivalent fields documenting:
  - [ ] Classification (risk level).
  - [ ] Patterns matched, if any.
  - [ ] Decision path (e.g., "pattern_blocked", "guardian_allowed").
- [ ] Emit `EmergencyOverrideReceipt` whenever a human override occurs.

Signing is OPTIONAL at Standard (but recommended).

---

## 3. COURT-GRADE CONFORMANCE CHECKLIST

**Who this is for:**
Regulated / high-liability domains: healthcare, financial trading, safety-critical automation, or any context where **receipts are legal evidence**.

Court-Grade = Standard **plus**:

- Signing
- Tri-temporal timestamps
- Law-change pipeline

### 3.1 Everything in BASIC + STANDARD

You MUST:

- [ ] Fully implement all Basic and Standard requirements.

### 3.2 Signed Receipts

You MUST:

- [ ] Sign **all** receipts (at least those in §4.1):
  - [ ] `AgentActionReceipt`
  - [ ] `RefusalReceipt`
  - [ ] `ToolPlanReceipt`
  - [ ] `GuardianVerdictReceipt`
  - [ ] `EmergencyOverrideReceipt`
  - [ ] Law-change receipts (invariant violation, proposal, sandbox run, council decision, self-repair outcome)
- [ ] Use a strong signature scheme (e.g., Ed25519).
- [ ] Canonicalize JSON using JCS/RFC 8785 **before** hashing/signing.
- [ ] Store public keys and key rotation information somewhere auditably.

You MUST:

- [ ] Verify signatures before treating any receipt as valid when doing replay/audit.

### 3.3 Tri-Temporal Timestamps

For Court-Grade receipts, you MUST:

- [ ] Include:
  - [ ] `valid_time.start`
  - [ ] Optional `valid_time.end`
  - [ ] `observed_at`
  - [ ] `transaction_time.recorded_at`
- [ ] Maintain the invariant:
  `valid_time.start ≤ observed_at ≤ transaction_time.recorded_at`

If your system can't fully support this yet, you're not Court-Grade. You may still be **Standard**.

### 3.4 Anchoring (Strongly Recommended)

You SHOULD:

- [ ] Periodically anchor Merkle roots of receipts into an external log, e.g.:
  - [ ] RFC 3161 TSA
  - [ ] Sigstore Rekor
- [ ] Emit an `AnchorReceipt` that:
  - [ ] Names the anchor service.
  - [ ] Includes the anchor payload/proof.
  - [ ] Identifies the receipts or Merkle root covered.

Anchoring isn't strictly required for Court-Grade in v1.2.0-rc1, but it's the intended direction.

### 3.5 Law-Change Pipeline

For any change to **safety invariants** (e.g., Amendment VII behavior, risk floors):

You MUST:

- [ ] Use the 5-receipt law-change pipeline:
  - [ ] `InvariantViolationReceipt`
  - [ ] `SelfRepairProposalReceipt`
  - [ ] `SandboxRunReceipt`
  - [ ] `CouncilDecisionReceipt`
  - [ ] `SelfRepairOutcomeReceipt`
- [ ] Ensure:
  - [ ] Each receipt references the previous (hash chain).
  - [ ] Timestamps are ordered.
  - [ ] Signatures verify.
- [ ] Block deployment of new invariants if the episode is incomplete or invalid.

You SHOULD:

- [ ] Run `validate_law_change_ledger()` (or equivalent) in CI/CD and on admission to higher rings (STAGING/PROD).

---

## 4. QUICK SELF-ASSESSMENT

**You're BASIC if...**

- [ ] You block `rm -rf /` and friends.
- [ ] You log HIGH/CRITICAL attempts as receipts.
- [ ] You emit `RefusalReceipt`s on block.
- [ ] You don't run CRITICAL in prod or real environments.

**You're STANDARD if...**

- [ ] Everything above, plus:
- [ ] You require Tool Plans for HIGH/CRITICAL.
- [ ] Guardian must ALLOW/ESCALATE before execution.
- [ ] You scope-check real executions against the plan.
- [ ] You emit the full receipt chain (plan, verdict, action, refusal/override).

**You're COURT-GRADE if...**

- [ ] Everything above, plus:
- [ ] Receipts are signed.
- [ ] You enforce tri-temporal timestamps.
- [ ] You use the 5-receipt law-change pipeline for invariant changes.
- [ ] You can replay decisions deterministically as evidence.

---

## 5. IMPLEMENTATION ORDER (RECOMMENDED)

If you're starting from scratch:

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
   - Implement the law-change pipeline & validation.

Each step is valuable on its own; you don't have to jump straight to Court-Grade.

---

For all normative details, see **`SPEC.md` (CSP Tool Safety Profile v1.2.0-rc1)**.
