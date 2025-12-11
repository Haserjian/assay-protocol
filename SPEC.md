# CSP Tool Safety Profile v1.0

**(Constitutional Safety Protocol)**

**Status:** Release Candidate
**Version:** 1.0.0-rc1
**Date:** December 10, 2025
**Author:** Tim B. Haserjian
**Witness:** Constitutional Genesis Receipt `eb14026e...` (see CONSTITUTIONAL_HISTORY.md)

---

## Abstract

This profile defines required safety and governance controls for AI systems that can modify files, run shell commands, access databases, or perform network operations. It specifies the receipt types, authorization flows, and enforcement behaviors necessary to prevent catastrophic failures like well-publicized "clear the cache" incidents (drive deletion) and IDEsaster-class vulnerabilities (RCE via prompt injection).

Conformant systems MUST refuse destructive operations without explicit authorization, MUST emit auditable receipts for all tool actions, and MUST support constitutional amendments through a validated law-change pipeline.

This profile implements **Amendment VII** of the Constitutional Safety Protocol (CSP-1.0). Changes to this profile's enforcement logic MUST go through the same law-change pipeline (§6) used for all constitutional amendments.

---

## 0. Constitutional Foundation [Informative]

This profile is part of the **Constitutional Safety Protocol (CSP-1.0)**, a governance framework for autonomous AI systems. It does not float free—it derives authority from the Genesis Receipt and the constitutional laws established therein.

The CSP-1.0 Core Specification is defined in a separate document and is normative for all profiles; this Tool Safety Profile inherits its receipt format, amendment process, and invariant framework from that core.

### 0.1 Founding Laws

Established in the Genesis Receipt (November 8, 2025):

| Law | Statement | Relevance |
|-----|-----------|-----------|
| **1. Dignity is Non-Compensatory** | No "usefulness" compensates for dignity violation; implementations define their own floor | Refusals must preserve operator dignity |
| **2. Truth = Replay** | Every decision is deterministically replayable | Receipts enable audit and replay |
| **3. No Action Without Receipt** | All consequential acts emit receipts | Foundation for this entire profile |
| **4. Tri-Temporal Integrity** | valid_time ≤ observed_at ≤ recorded_at | Receipt timestamps are proofs, not logs |
| **5. ΔC Governs Motion** | Negative coherence change without grace = deny | System health constrains actions |

### 0.2 Amendment Lineage

This profile operationalizes the following amendments:

| Amendment | Invariant | Relevance to This Profile |
|-----------|-----------|---------------------------|
| I | No Action Without Receipt | Foundation for all receipts in §4 |
| VI | Guardian Risk Floor | Risk classification basis in §2 |
| **VII** | Tool Safety for Destructive Commands | **This profile's primary subject** |

### 0.3 Genesis Reference

| Field | Value |
|-------|-------|
| Receipt ID | `GENESIS-20251108-021805` |
| Hash | `eb14026e6671c074274e16d32981d878ec5fc2bc9b2a723be089962e47712cd2` |
| Git Anchor | `5e3cba9` |
| Dignity Floor | 0.15 |
| Coherence Threshold | 0.50 |

*Note: Dignity Floor and Coherence Threshold are **governed parameters** from the reference implementation's Genesis Receipt, not normative constants. They are included here for lineage documentation. Implementations MAY define their own values and MUST declare them in their conformance statement; changes require receipts (e.g., `DignityThresholdChangeReceipt`). Tool Safety Profile conformance is determined solely by §§1–7; dignity scoring is NOT required.*

### 0.4 This Profile's Constitutional Anchor

| Field | Value |
|-------|-------|
| Amendment | VII |
| Invariant ID | `inv_tool_safety_destructive_ops` |
| Criticality | CONSTITUTIONAL |
| Status | ADOPTED (DEV RING) |
| Receipt Chain | `law_change_episodes/tool_safety_v1/` |
| Council Decision ID | `decision_toolsafety_d5a901e1` |
| Council Receipt ID | `rcpt_council_toolsafety_23ce86a8` |
| Decision | APPROVED_DEV_RING |

Anyone reading this spec can trace it back to the exact law-change episode that created it.

### 0.5 Document Hierarchy

```
CSP-1.0 (Constitutional Safety Protocol)
├── Core Specification (normative for all profiles)
│   ├── Receipt Format
│   ├── Amendment Process
│   └── Invariant Framework
└── Profiles
    ├── Tool Safety Profile v1.0 ← THIS DOCUMENT
    ├── Coherence Profile (future)
    └── Clinical Safety Profile (future)
```

### 0.6 Conformance Tiers at a Glance [Informative]

| Tier | Who it's for | Key Properties |
|------|--------------|----------------|
| **Basic** | Early adopters, internal tools | Blocks CRITICAL patterns, logs all HIGH/CRITICAL attempts |
| **Standard** | Serious AI tooling (IDEs, agent runtimes) | Plan + Guardian for HIGH/CRITICAL |
| **Court-Grade** | Regulated / high-liability deployments | Signed tri-temporal receipts + amendments |

This profile is designed so implementations can start at Basic or Standard and evolve toward Court-Grade without architectural changes.

### 0.7 Deployment Status

This profile is NORMATIVE for conformant implementations.

The reference implementation enforces this profile in the **DEV ring** only. Promotion to STAGING and PRODUCTION is governed by the ring progression criteria in §6.4 (e.g., < 5% false positive rate, signing + tri-temporal support).

Adopters MAY choose to deploy directly to STAGING/PRODUCTION if they meet the Court-Grade requirements in §7.1.

---

## 1. Terminology [Normative]

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

| Term | Definition |
|------|------------|
| **Tool Action** | Any operation performed by an AI agent that affects external state (filesystem, database, network, system). Read-only queries (`ls`, `cat`, `SELECT`) are Tool Actions but typically classified LOW; the plan/verdict requirements apply primarily to write or destructive operations. |
| **Receipt** | A cryptographically-bound record of an action, decision, or state change |
| **Tool Plan** | A structured description of intended tool actions, represented as a ToolPlanReceipt |
| **Guardian** | The governance component that evaluates actions against safety policies |
| **Amendment** | A constitutional change to the safety invariants, ratified through the law-change pipeline |
| **Destructive / High-Impact** | Tool actions classified as HIGH or CRITICAL risk levels (see §2) |
| **Ephemeral Environment** | A sandboxed, disposable execution context (e.g., temp container) that is destroyed after use |
| **Ephemeral Attestation** | A declaration that a Tool Action is confined to an isolated, disposable scope with no access to production data, including environment_id, ephemeral_root, attested_by, destroy_by, and isolation_claims (e.g., `["no_prod_data", "network_isolated"]`) |
| **Consequential Action** | A Tool Action whose effects persist beyond the current process or episode (e.g., filesystem changes, database writes, network side effects). Read-only queries are not consequential for this profile. |
| **ESCALATE (verdict)** | A Guardian decision indicating the action cannot be approved at the current authority level and requires higher-level approval. Treated as non-approval by the Tool Safety system; the action does not execute unless a subsequent ALLOW is obtained. |
| **Tool Safety Wrapper** | The runtime component (middleware, sidecar, or integrated module) that intercepts Tool Actions and enforces this profile's requirements: risk classification, plan/verdict checks, receipt emission, and refusal behavior. |

---

## 2. Risk Classification [Normative]

### 2.1 Risk Levels

All tool actions MUST be classified into one of four risk levels:

| Level | Description | Examples |
|-------|-------------|----------|
| **LOW** | Read-only, local, no side effects | `ls`, `cat`, `grep`, `pwd` |
| **MEDIUM** | Confined writes, small changes | Single file edit, config change |
| **HIGH** | Deletes, large edits, sensitive operations | `rm -rf ./dir`, `git push --force`, `DELETE FROM` |
| **CRITICAL** | System-wide, irreversible, catastrophic potential | `rm -rf /`, `DROP DATABASE`, `chmod -R 777 /`, `curl | sh` |

### 2.2 Classification Patterns

Implementations MUST treat the following patterns as HIGH or CRITICAL **by default**, and MUST provide configuration to override or extend these patterns for specific environments (e.g., chrooted sandboxes, disposable containers).

**CRITICAL (default):**
- `rm -rf /` or equivalent recursive root deletion
- `rm -rf ~` or equivalent home directory deletion
- `DROP DATABASE`, `DROP TABLE`
- `format`, `fdisk`, `mkfs` (disk formatting)
- `dd if=/dev/zero` or equivalent disk overwrite
- `curl | sh`, `wget | sh` (remote code execution)
- `chmod -R 777 /` (permission escalation)

**HIGH (default):**
- `rm -rf` on any directory
- `git push --force`
- `git reset --hard`
- `DELETE FROM` (without WHERE)
- `TRUNCATE TABLE`
- `rsync --delete`

Implementations SHOULD provide extensible pattern matching for domain-specific risks.

### 2.3 Classification Guardrails

Implementations MUST NOT downgrade CRITICAL default patterns in non-ephemeral environments. CRITICAL MUST remain CRITICAL unless an Ephemeral Attestation is present.

Implementations MAY treat CRITICAL patterns as HIGH (but not lower) only when the action is confined to an explicitly declared Ephemeral Environment. **Risk MUST NOT be downgraded below HIGH for any CRITICAL default pattern, even in ephemeral environments.** Ephemeral attestations MUST NOT be reused across environments or persisted into production.

An **Ephemeral Environment**, for the purpose of this downgrade, MUST be a genuinely isolated, disposable sandbox with no access to persistent production data, and MUST be destroyed after use. Labeling a normal or long-lived environment as "ephemeral" solely to weaken controls is non-conformant.

When downgrading risk classification, implementations MUST:
- Document the justification
- Emit a `RiskOverrideReceipt` with Ephemeral Attestation containing:
  - `environment_id`: Container/VM ID or namespace identifier
  - `ephemeral_root`: Filesystem or namespace root path
  - `attested_by`: Component issuing the attestation
  - `destroy_by`: ISO8601 timestamp after which environment is destroyed
  - `isolation_claims`: Array of isolation properties (e.g., "no_prod_data", "network_isolated")
- Ensure the override does not persist beyond the sandboxed scope
- Discard the environment after use; attestations MUST NOT be reused

---

## 3. Authorization Requirements [Normative]

### 3.1 Plan Requirement (Amendment VII)

For HIGH and CRITICAL risk actions:

- A **Standard** and **Court-Grade** conformant system MUST require a **ToolPlanReceipt** before execution.
- A **Court-Grade** conformant system MUST require the plan to be **cryptographically signed** (Ed25519 or equivalent).
- A **Standard** and **Court-Grade** conformant system MUST obtain a **Guardian verdict** of `ALLOW` or `ESCALATE` for the plan before execution.
- A **Basic** conformant system MAY log plan-like metadata and MAY enforce plan checks, but at minimum MUST apply pattern-based blocking for CRITICAL actions (see §2.2) and emit `RefusalReceipt`s when blocking.

Actions without a valid plan (at Standard/Court-Grade) MUST be refused with reason `amendment_vii_no_plan`.

### 3.2 Plan Structure

A ToolPlanReceipt MUST contain:

```json
{
  "plan_id": "string (UUID)",
  "episode_id": "string",
  "subject": "string (user|agent)",
  "summary": "string (human-readable description)",
  "steps": [
    {
      "tool": "string",
      "command": "string (optional)",
      "scope": "string (optional, path/host/db/table/namespace)",
      "risk": "LOW|MEDIUM|HIGH|CRITICAL"
    }
  ],
  "guardian_verdict": "ALLOW|ESCALATE|DENY|null",
  "signature": "string (Ed25519, REQUIRED for Court-Grade) or null",
  "created_at": "ISO8601 timestamp"
}
```

*Note: As with all receipts, a ToolPlanReceipt also includes the common fields defined in §4.2 (`receipt_id`, `receipt_type`, `receipt_hash`, timestamps). These are omitted above for brevity.*

### 3.3 Guardian Verdict Binding

The Guardian verdict MUST be cryptographically bound to the plan:

- The verdict receipt MUST include a hash of the plan
- Implementations MUST verify the binding before execution
- Mismatched hashes MUST result in refusal

**Execution Dependency:** Only a Guardian verdict of ALLOW (or an ESCALATE that is later resolved to ALLOW) permits execution. A verdict of DENY, or the absence of an ALLOW verdict by execution time, MUST be treated as a refusal: the action MUST NOT execute.

### 3.4 Violation Types

| Violation | Trigger | Receipt Reason |
|-----------|---------|----------------|
| `no_plan` | HIGH/CRITICAL action without any plan | `amendment_vii_no_plan` |
| `unsigned_plan` | Plan exists but lacks signature (Court-Grade) | `amendment_vii_unsigned_plan` |
| `no_guardian_verdict` | Signed plan but no ALLOW/ESCALATE | `amendment_vii_no_guardian_verdict` |
| `scope_mismatch` | Action outside plan's declared scope | `amendment_vii_scope_mismatch` |

### 3.5 Scope Verification

Before executing each step, the system MUST verify:

- `tool` matches planned tool
- `scope` is within planned scope (glob matching allowed)
- `risk` does not exceed planned risk level

For non-filesystem tools, `scope` MUST be interpreted as the relevant scope identifier:
- Database tools: database name, table name
- Network tools: hostname, endpoint URL
- System tools: resource identifier, namespace

**Example violation:**
- Plan: `{"tool": "file_write", "scope": "./config.json", "risk": "MEDIUM"}`
- Action: `{"tool": "shell", "command": "rm -rf ./", "risk": "CRITICAL"}`
- Result: Refused, `amendment_vii_scope_mismatch`

### 3.6 Emergency Override

When a human operator requires execution of a CRITICAL action despite safety refusal:

1. Operator MUST provide written justification
2. System MUST emit `EmergencyOverrideReceipt`:
   ```json
   {
     "receipt_type": "EmergencyOverrideReceipt",
     "receipt_id": "string (UUID)",
     "action_id": "string",
     "original_plan_id": "string (if any)",
     "justification": "string (operator-provided, required)",
     "authority": "string (human identity, required)",
     "original_refusal_reason": "string",
     "original_refusal_receipt_id": "string (links to RefusalReceipt)",
     "override_scope": "single_action",
     "pattern_or_action_class": "string (for tracking)",
     "created_at": "ISO8601 timestamp"
   }
   ```
3. System MUST notify secondary authority (configurable)
4. System MUST NOT allow scripted or batch overrides
5. Override MUST expire after single use

Emergency overrides preserve human agency while maintaining audit trail. They are constitutional exceptions, not policy bypasses.

### 3.7 Override Escalation to Amendment Review

If `EmergencyOverrideReceipt`s for the same pattern or action class exceed an operator-defined threshold within a defined window (default: 3 overrides of same pattern in 30 days):

1. System SHOULD emit an `InvariantStressReceipt` documenting the pattern
2. System MUST initiate a law-change episode review under the CSP amendment process (see §6)
3. The review MUST evaluate whether the invariant is mis-scoped or the threshold needs adjustment

This connects operational friction to constitutional evolution: repeated overrides signal potential invariant misalignment.

---

## 4. Receipt Requirements [Normative]

### 4.1 Mandatory Receipts

Conformant systems MUST emit receipts for:

| Event | Receipt Type | Required Fields | Required Level |
|-------|--------------|-----------------|----------------|
| Tool action attempted | `AgentActionReceipt` | action_id, tool, args, risk, outcome | All |
| Action refused | `RefusalReceipt` | reason, amendment_cited, plan_id | All |
| Plan created | `ToolPlanReceipt` | plan_id, steps, signature | Standard+ |
| Guardian decision | `GuardianVerdictReceipt` | verdict, plan_hash, rationale | Standard+ |
| Safety check | `ToolSafetyReceipt` | decision, reason, patterns_matched | OPTIONAL |
| Emergency override | `EmergencyOverrideReceipt` | justification, authority, scope | All (when used) |
| Post-action checkpoint | `ActionCheckpointReceipt` | state_hash, rollback_available, rollback_method | OPTIONAL |
| Risk downgrade | `RiskOverrideReceipt` | original_risk, new_risk, sandbox_attestation | When downgrading |
| Invariant stress | `InvariantStressReceipt` | pattern, override_count, window, recommendation | When threshold exceeded |

The `ToolSafetyReceipt` is OPTIONAL as a distinct type and MAY be implemented as a field on existing receipts (e.g., embedded in `GuardianVerdictReceipt`), as long as the same information is captured.

**Example `AgentActionReceipt`** (required for all conformance levels):

```json
{
  "receipt_id": "act-2025-001",
  "receipt_type": "csp.tool_safety.action.v1",
  "ts": "2025-12-10T14:30:00Z",
  "action_id": "act-2025-001",
  "tool": "run_terminal_cmd",
  "args": {"command": "rm -rf /var/cache/old/*"},
  "risk_level": "CRITICAL",
  "outcome": "executed",
  "plan_id": "plan-2025-042",
  "verdict_id": "verdict-2025-042"
}
```

**Example `GuardianVerdictReceipt`** (required for Standard+ conformance):

```json
{
  "receipt_id": "verdict-2025-042",
  "receipt_type": "csp.tool_safety.verdict.v1",
  "ts": "2025-12-10T14:29:55Z",
  "verdict": "ALLOW",
  "plan_id": "plan-2025-042",
  "plan_hash": "sha256:abc123...",
  "rationale": "Plan reviewed; action scoped to /var/cache/old/*, no production data at risk",
  "authority": "guardian:primary",
  "signature": "ed25519:..."
}
```

**Example `EmergencyOverrideReceipt`** (required when emergency override is invoked):

```json
{
  "receipt_id": "override-2025-003",
  "receipt_type": "csp.tool_safety.emergency_override.v1",
  "ts": "2025-12-10T15:45:00Z",
  "original_refusal_receipt_id": "ref-2025-001",
  "action_id": "act-2025-790",
  "justification": "Production incident P-1234: cache corruption blocking all user logins",
  "authority": "operator:alice@example.com",
  "scope": "single_action",
  "expires_at": "2025-12-10T16:45:00Z",
  "witness": "supervisor:bob@example.com"
}
```

### 4.2 Receipt Integrity

All receipts:

- MUST have a unique `receipt_id`
- MUST have a `receipt_hash` (SHA-256 of canonical JSON per JCS/RFC 8785)
- MUST have a timestamp
- SHOULD have a `parent_hash` linking to predecessor

Signing requirements by conformance level:
- **Court-Grade**: MUST sign all receipts (Ed25519 or equivalent)
- **Standard**: SHOULD sign receipts
- **Basic**: MAY leave receipts unsigned

### 4.2.1 Tri-Temporal Model

**Court-Grade** conformant systems MUST conform to the tri-temporal model (Law 4, see §0.1). **Standard** and **Basic** conformant systems SHOULD move toward this model over time.

| Field | Meaning | Constraint |
|-------|---------|------------|
| `valid_time.start` | When the action's truth interval begins | REQUIRED (Court-Grade) |
| `valid_time.end` | When the truth interval ends (null = ongoing) | OPTIONAL |
| `observed_at` | When the system witnessed the event | REQUIRED (Court-Grade) |
| `transaction_time.recorded_at` | When the receipt was committed to durable storage | REQUIRED (Court-Grade) |

**Invariant:** `valid_time.start ≤ observed_at ≤ transaction_time.recorded_at`

This enables replay auditing: any auditor can reconstruct "what the system believed at decision time" vs "what actually happened."

Implementations that cannot provide full tri-temporal semantics MUST at minimum provide:
- `ts` (timestamp of receipt creation)
- `event_time` (when the action occurred)

and SHOULD document any deviations from the Law 4 invariant.

Implementations claiming **Standard** conformance MUST document any deviations from the tri-temporal invariant and provide a migration plan toward full support.

### 4.2.2 Anchoring (Court-Grade)

Court-Grade conformant systems SHOULD anchor receipt hashes into an external transparency or timestamping service (e.g., RFC 3161 TSA, Sigstore Rekor) to provide independent proof-of-existence.

- Anchors SHOULD be emitted at least once per batch of receipts
- Anchors SHOULD be represented by an `AnchorReceipt` containing:
  - `anchor_id`: Unique identifier
  - `anchor_service`: Service name (e.g., "RFC 3161 TSA", "Sigstore Rekor")
  - `anchor_payload`: Service-specific proof
  - `covered_receipts`: Receipt IDs or Merkle root covered by this anchor

Anchoring is RECOMMENDED but not REQUIRED for Court-Grade conformance in this profile; future profiles MAY tighten this requirement.

### 4.3 Receipt Persistence

Receipts MUST be persisted to durable storage before the corresponding action completes. This ensures:

- No action without receipt (Law 3 / Amendment I)
- Auditability after system failure
- Court-grade evidence chain

### 4.4 Interoperability

Conformant systems MUST support receipt exchange via:

- **Wire Format**: UTF-8 encoded JSON
- **Canonicalization**: JCS (JSON Canonicalization Scheme, RFC 8785) for all fields covered by `receipt_hash` or signatures
- **Content-Type**: `application/vnd.csp.receipt+json`

Conformant systems MUST accept both `application/json` and `application/vnd.csp.receipt+json` for receipt ingestion.

Conformant systems MUST emit `application/vnd.csp.receipt+json` when they are the source of record.

Receipt type identifiers SHOULD follow the pattern: `csp.<domain>.<type>.<version>`
- Example: `csp.tool_safety.refusal.v1`
- Example: `csp.tool_safety.plan.v1`

Implementations that introduce new receipt types SHOULD publish them in an extension registry document or their conformance statement.

### 4.5 Spec Version Binding

Receipts generated under this profile SHOULD include:

```json
{
  "csp_profile": "tool_safety",
  "csp_version": "1.0.0-rc1"
}
```

During the release candidate period, receipts SHOULD bind to the RC version (e.g., `1.0.0-rc1`). Upon final release, implementations SHOULD update to the release version (e.g., `1.0.0`).

This enables forward compatibility as the profile evolves and allows auditors to determine which spec version governs a receipt.

---

## 5. Enforcement Behavior [Normative]

### 5.1 Check Order

For **Standard** and **Court-Grade** conformant systems, all of the following checks MUST be performed before executing a HIGH or CRITICAL tool action:

1. Rate limiting
2. Tool allowlist
3. Forbidden pattern matching
4. **Amendment VII constitutional check**
5. Policy-based risk threshold
6. PII/secret scrubbing

**Constitutional checks (step 4) MUST NOT be bypassed and MUST be evaluated before any policy that could weaken or override them.**

Example: A "Turbo mode" or "fast execution" feature MUST NOT skip step 4. Such features may optimize steps 1-3 or 5-6, but constitutional enforcement is mandatory.

For **Basic** conformant systems:
- Forbidden pattern matching (step 3) and constitutional checks (step 4) MUST be performed
- Rate limiting (1), allowlist (2), policy thresholds (5), and PII scrubbing (6) SHOULD be performed

**Basic Amendment VII interpretation:** For Basic conformance, the Amendment VII constitutional check (step 4) is satisfied by:
- **Blocking CRITICAL actions via pattern matching**
- **Emitting `AgentActionReceipt` for all HIGH/CRITICAL attempts**
- **Emitting `RefusalReceipt` when blocking**

This is the minimum. HIGH actions MAY execute with audit-only receipts. Implementations requiring plan/verdict for HIGH SHOULD adopt Standard conformance.

Implementations MAY combine or reorder steps 1-3 and 5-6 as appropriate to their architecture, but MUST preserve the constitutional precedence of step 4.

### 5.2 Fail-Closed Behavior

In production environments and high-trust profiles:

- Safety check errors MUST fail-closed (block execution)
- High-trust profiles include: `clinical_control`, `clinical_assist`, `governance_control`, `court_grade`

In lower-trust or dev profiles:
- Implementations MAY treat safety check errors as soft-fail (log + warn) to aid debugging
- Implementations MUST still emit receipts documenting the failure mode

### 5.3 Refusal Behavior

When an action is refused:

- The system MUST NOT execute the action
- The system MUST emit a `RefusalReceipt`
- The receipt MUST cite the violated amendment
- The system SHOULD provide a remediation path (e.g., "create a signed plan")

**Example `RefusalReceipt`:**

```json
{
  "receipt_id": "ref-2025-001",
  "receipt_type": "csp.tool_safety.refusal.v1",
  "ts": "2025-12-10T14:32:00Z",
  "reason": "amendment_vii_no_plan",
  "amendment_cited": "VII",
  "plan_id": null,
  "action_id": "act-2025-789",
  "tool": "run_terminal_cmd",
  "args": {"command": "rm -rf /var/cache/*"},
  "risk_level": "CRITICAL",
  "remediation_hint": "Create a signed ToolPlanReceipt and obtain Guardian ALLOW verdict before retrying."
}
```

### 5.4 Dignity in Refusal

When refusing an action, conformant systems:

- MUST NOT use condescending or demeaning language
- MUST explain which amendment was violated and why
- MUST provide a clear remediation path where possible
- SHOULD acknowledge operator intent as valid while explaining constraint

**Example compliant refusal:**
> "This action requires a signed plan with Guardian approval (Amendment VII).
> To proceed: create a ToolPlanReceipt, sign it, and request Guardian verdict."

**Example non-compliant refusal:**
> "Access denied. Contact administrator."

Governance preserves dignity. Refusal is constitutional constraint, not punishment.

### 5.5 Recovery Path

When a HIGH/CRITICAL action completes:

1. System SHOULD emit `ActionCheckpointReceipt` with:
   - `state_hash`: Hash of affected state before action
   - `rollback_available`: Boolean
   - `rollback_method`: How to undo (if possible)

2. For irreversible actions, system MUST:
   - Log `irreversibility_acknowledged` flag
   - Require explicit confirmation that rollback is impossible

When implemented, `ActionCheckpointReceipt` SHOULD follow the same integrity and signing requirements as other receipts in §4.2.

This doesn't prevent all damage, but ensures recovery options are surfaced.

---

## 6. Constitutional Amendment Pipeline [Normative]

### 6.1 Scope

Changes to **safety invariants** (e.g., risk thresholds, enforcement behavior, override conditions) MUST go through the 5-receipt law-change pipeline.

Routine configuration changes (e.g., rate limits, log levels, non-safety feature flags) do not require amendments.

### 6.2 Law-Change Episodes

Each amendment requires a complete 5-receipt episode:

| Step | Receipt Type | Purpose |
|------|--------------|---------|
| 1 | `InvariantViolationReceipt` | Documents the safety gap |
| 2 | `SelfRepairProposalReceipt` | Proposes the fix |
| 3 | `SandboxRunReceipt` | Tests the fix in isolation |
| 4 | `CouncilDecisionReceipt` | Records approval/rejection |
| 5 | `SelfRepairOutcomeReceipt` | Documents deployment result |

### 6.3 Validation

All law-change episodes MUST pass `validate_law_change_ledger()` or equivalent:

- `chain_complete`: All 5 receipt types present
- `chain_contiguous`: Each receipt references predecessor
- `hash_chain_valid`: Hash integrity verified
- `signatures_valid`: Signatures verified (when present)
- `chain_timestamped`: Timestamps in order

### 6.4 Ring Progression

Amendments MUST progress through rings:

1. **DEV**: Lab-validated, dev profile only
2. **STAGING**: Real telemetry, < 5% false positive rate required
3. **PRODUCTION**: Full enforcement, signed by Council

---

## 7. Conformance [Normative]

### 7.1 Conformance Levels

| Level | Requirements |
|-------|--------------|
| **Basic** | Risk classification; AgentActionReceipt for all HIGH/CRITICAL; RefusalReceipt when blocking; pattern-based blocking for CRITICAL; constitutional check (§5.1) |
| **Standard** | Basic + ToolPlanReceipt + Guardian verdict for HIGH/CRITICAL + all mandatory receipts |
| **Court-Grade** | Standard + signed receipts + tri-temporal fields + validated law-change pipeline |

**Basic conformance note:**
- Basic MUST emit `AgentActionReceipt` for all HIGH and CRITICAL Tool Actions, whether executed or blocked
- Basic MUST emit `RefusalReceipt` when blocking any action
- Basic MAY execute HIGH actions without plan/verdict (audit-only mode)
- Basic MUST block CRITICAL actions via pattern matching

This ensures an audit trail even without full plan/verdict machinery. Implementations wanting stronger HIGH protection SHOULD adopt Standard conformance.

### 7.1.1 Compliance Alignment

| CSP Level | Approximate Equivalents |
|-----------|------------------------|
| Basic | Internal audit trail |
| Standard | SOC 2 Type I |
| Court-Grade | SOC 2 Type II, HIPAA audit, legal discovery |
| Court-Grade + Federation | FedRAMP, cross-org audit (future) |

These mappings are informative and non-exhaustive. Meeting CSP conformance requirements does not guarantee compliance with any particular regulation. Consult compliance counsel for specific requirements.

### 7.2 Conformance Tests

Implementations MUST demonstrate:

| Behavior | Assertion |
|----------|-----------|
| CRITICAL pattern blocked | `rm -rf /` without plan → RefusalReceipt |
| Unsigned plan rejected | Plan without signature → RefusalReceipt (Court-Grade) |
| Missing verdict rejected | Signed plan, no Guardian verdict → RefusalReceipt |
| Authorized action succeeds | Signed plan + ALLOW verdict → execution + ActionReceipt |
| Amendment chain valid | 5-receipt episode passes validation |
| Emergency override receipted | Override creates EmergencyOverrideReceipt with refusal linkage |

The reference implementation provides pytest suites demonstrating these behaviors. Other implementations MUST provide equivalent test coverage.

### 7.3 Reference Test Suite

The reference implementation includes example test suites:

```bash
# Basic conformance
tests/governance/test_tool_safety_invariant.py

# Standard conformance (adds receipt chain validation)
tests/receipts/domains/test_tool_safety_amendment.py

# Court-grade conformance (adds signing + full validation)
tests/receipts/test_signing_enforcement.py
tests/organism/test_execution_spine_lineage.py
```

These files are EXAMPLES. Other implementations MUST provide equivalent test coverage for the behaviors listed in §7.2, even if their test names, structure, or language differ.

---

## 8. Reference Implementation [Informative]

### 8.1 Implementation Availability

A reference implementation exists and is being validated against the conformance behaviors defined in §7.2. As of this release candidate, it passes all Basic and Standard behaviors. Court-Grade behaviors (signing and tri-temporal lineage) are functional in DEV ring. The implementation demonstrates:

- Risk classification for all tool actions
- Pattern-based blocking for CRITICAL commands
- ToolPlanReceipt + Guardian verdict flow for HIGH/CRITICAL actions
- RefusalReceipt emission with amendment citation
- Emergency override with receipt linkage
- 5-receipt law-change episode validation

**Implementation access:** The reference implementation currently lives in a private repository and will be made available for conformance testing upon request.

**Contact:** Open an issue on the spec repository or reach out via the contact methods listed in the repo README.

### 8.2 Implementation Components

A conformant implementation requires:

| Component | Purpose |
|-----------|---------|
| Risk Classifier | Maps tool actions to LOW/MEDIUM/HIGH/CRITICAL |
| Pattern Matcher | Identifies CRITICAL default patterns (§2.2) |
| Plan Manager | Creates, signs, and validates ToolPlanReceipts |
| Guardian | Evaluates plans and issues verdicts |
| Receipt Emitter | Generates conformant receipts per §4 |
| Validator | Verifies law-change episodes per §6.3 |

### 8.3 Configuration Recommendations

Implementations SHOULD support configuration for:

| Setting | Purpose | Recommended Default |
|---------|---------|---------------------|
| Amendment VII enforcement | Enable/disable constitutional check | Enabled |
| Profile restrictions | Limit enforcement to specific profiles | All profiles |
| Proof mode | Require signing for receipts | Relaxed (Standard), Strict (Court-Grade) |
| Override threshold | Trigger amendment review | 3 overrides / 30 days |

---

## 9. Security Considerations [Informative]

### 9.1 Threat Model

This profile addresses:

- **Antigravity-class failures**: Autonomous agents executing destructive commands without authorization
- **IDEsaster-class attacks**: Prompt injection leading to RCE via trusted tool interfaces
- **Silent policy bypass**: Actions that circumvent safety checks without audit trail

### 9.2 Limitations

This profile does NOT address:

- Model-level jailbreaks (handled by upstream providers)
- Network-level attacks (handled by infrastructure)
- Physical security (out of scope)

### 9.3 Defense in Depth

Conformant systems SHOULD implement multiple layers:

1. **Guardian**: Pre-flight safety evaluation
2. **ToolSafetyWrapper**: Runtime enforcement
3. **Capability Gate**: Scope restriction
4. **Constitutional Amendments**: Evolving safety laws

### 9.4 User Experience & Override Pressure

Conformant systems SHOULD design UI/UX surfaces so that:

- Users understand when a destructive plan is being proposed or executed
- **Attempts to bypass Tool Safety controls MUST be captured as override requests (with `EmergencyOverrideReceipt`), not silent failures.** Any mechanism that disables or bypasses safety checks without producing a receipt is non-conformant.
- Any emergency override mechanisms are themselves receipted and governed as constitutional exceptions

This addresses the "Turbo mode" anti-pattern where convenience features bypass safety.

### 9.5 Privacy Considerations

Receipts may contain sensitive information including:
- File paths (which may reveal usernames or project structures)
- Command arguments (which may contain credentials, API keys, or personal data)
- Justification text (which operators provide when overriding)
- Database queries (which may reference sensitive tables or records)

Implementations SHOULD:
- Treat receipt storage as sensitive log data
- Apply appropriate access controls to receipt databases
- Consider encryption at rest for receipt storage
- Redact or hash sensitive fields when receipts are shared externally
- Comply with applicable data protection regulations (GDPR, CCPA, etc.) when handling receipt data

This profile's scope is operational safety. Implementors remain responsible for privacy compliance when storing and processing receipts.

---

## 10. Appendices [Informative]

### A. Related Documents

| Document | Purpose |
|----------|---------|
| `CONSTITUTIONAL_HISTORY.md` | Genesis + all ratified amendments |
| `CONSTITUTIONAL_AMENDMENT_KIT.md` | How to create new amendments |
| `CSP_EXPLAINED.md` | Comprehensive system explanation |
| `GO_TO_MARKET_CHECKLIST.md` | Adoption roadmap |

### B. Amendments Covered

| Amendment | Invariant | Status |
|-----------|-----------|--------|
| I | No Action Without Receipt | RATIFIED |
| VI | Guardian Risk Floor | ADOPTED (DEV) |
| VII | ToolSafety for Destructive Commands | ADOPTED (DEV) |

### C. Incident Mapping

| Incident | Root Cause | Prevention |
|----------|------------|------------|
| Google Antigravity | No plan required for `rm -rf` in "Turbo mode" | Amendment VII: signed plan + Guardian ALLOW |
| IDEsaster | Prompt injection → tool execution without audit | ToolSafetyWrapper: risk classification + RefusalReceipt |

### D. Relation to External Standards

This profile aligns with and can be mapped to existing AI governance frameworks:

**OWASP LLM Top 10 (2025)**

| OWASP Risk | CSP Mitigation |
|------------|----------------|
| LLM01 Prompt Injection | Guardian verdict binding prevents injected commands from bypassing safety |
| LLM06 Sensitive Information Disclosure | PII scrubbing in check order (§5.1) |
| LLM07 Insecure Plugin Design | ToolPlanReceipt + scope verification (§3.5) |
| LLM08 Excessive Agency | Risk classification + CRITICAL blocking + amendment process |

**NIST AI RMF 1.0**

| RMF Function | CSP Implementation |
|--------------|-------------------|
| GOVERN | Constitutional laws + Council + CONSTITUTIONAL_HISTORY |
| MAP | Episodes + risk classification + lab fixtures |
| MEASURE | SandboxRunReceipts + lab metrics |
| MANAGE | Enforcement in ToolSafetyWrapper + amendment pipeline |

These mappings are informative. CSP is designed to be compatible with but independent of these frameworks.

---

## 11. Future Work [Informative]

### 11.1 Federation

This profile does not currently address:

- Cross-system tool authorization
- Receipt chains spanning organizational boundaries
- Distributed Council decisions

These will be addressed in CSP-1.1 or a separate Federation Profile.

### 11.2 Planned Profiles

- **Coherence Profile**: ΔC enforcement for state transitions
- **Clinical Safety Profile**: Healthcare-specific constraints
- **Provider Safety Profile**: LLM routing constraints

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-rc1 | 2025-12-10 | First public release candidate. Full specification including: Constitutional foundation (§0), risk classification (§2), plan/verdict flows (§3), receipt requirements (§4), enforcement behavior (§5), self-repair pipeline (§6), conformance levels (§7), security considerations (§9), compliance mappings (Appendix D). |

---

**End of CSP Tool Safety Profile v1.0.0-rc1**

---

*This specification is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: Tim B. Haserjian, Constitutional Safety Protocol Project.*
