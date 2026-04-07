# Assay Protocol — Replay-Constrained Episode (RCE) Profile v0.1

**Status:** Draft companion to SPEC.md
**Version:** 0.1.0
**Date:** 2026-04-06
**Author:** Tim B. Haserjian
**Scope:** Replay verification of agent work units (episodes)
**Grounded in:** Assay Proof Pack Contract, Constitutional Receipt Standard (CRS) v0.1, RFC 8785 (JCS), RFC 8032 (Ed25519)

---

## Abstract

This profile defines a **Replay-Constrained Episode (RCE)**: a verifiable work unit whose correctness is defined by replay against recorded evidence. An episode compiles into an Assay Proof Pack and produces receipts that conform to the Constitutional Receipt Standard.

This is a companion to [SPEC.md](./SPEC.md) and [CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md](./CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md), not a replacement. Implementers should read both.

**Scope:** RCE defines *what a replayable work unit is*. Profiles (e.g., Tool Safety) define *what actions within an episode must be proven*.

---

## 0. Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

### 0.1 Hash Encoding

All hash fields in this profile use the prefixed format `sha256:<64-char-lowercase-hex>`. This applies to all cross-verifiable and local-attestation hashes in receipts, contracts, and dispute payloads. Verifiers MUST compare hashes as exact string equality on the prefixed form.

### 0.2 Pinned Invariants

**Episodes are the truth-bearing work unit. Proof packs are the compiled evidence artifact.**

**Do not create two Episode truths.** AgentMesh owns episode identity and provenance. Assay owns replay contracts, receipts, and proof compilation.

### 0.3 Relationship to Founding Laws

| Law | Statement | RCE Relevance |
|-----|-----------|---------------|
| **2. Truth = Replay** | Every decision is deterministically replayable | RCE operationalizes this law as a protocol |
| **3. No Action Without Receipt** | All consequential acts emit receipts | Episode steps emit receipts into proof packs |
| **4. Tri-Temporal Integrity** | valid_time ≤ observed_at ≤ recorded_at | Receipt timestamps in episode steps are proofs |

---

## 1. Terminology [Normative]

| Term | Definition |
|------|-----------|
| **Episode** | A bounded unit of agent work with declared inputs, a typed step DAG, and structured outputs. |
| **Episode Contract** | The replay-relevant specification of an episode: inputs, script, policy, and identity-bearing environment. |
| **Replay-Normative View** | The subset of an Episode Contract that determines replay identity. Excludes descriptive metadata. |
| **ReplayScript** | A typed DAG of opcodes that defines the episode's execution steps. |
| **Recorded Trace** | The JSON output artifacts captured during original episode execution. Used as the reference for replay comparison. |
| **Replay Verifier** | An independent implementation that replays an episode's recorded traces against its receipts and emits a verdict. |
| **Comparator Tier** | The comparison method used to determine whether replay outputs match. v0.1 supports Tier A only. |
| **Dispute Payload** | Structured evidence attached to a `DIVERGE` verdict identifying which steps diverged and how. |
| **Proof Pack** | An Assay evidence unit containing receipts, manifest, verification report, and signature. Episodes compile into proof packs. |

---

## 2. Identity Model [Normative]

An RCE system distinguishes three identities that MUST NOT be conflated:

| Identity | Owner | Semantics | Mutable? |
|----------|-------|-----------|----------|
| `episode_id` | AgentMesh | Operational runtime handle. AgentMesh-native time-sortable identifier (`ep_` prefix + 48-bit ms timestamp + 48-bit random). Not a standard ULID — do not assume ULID semantics. | No |
| `episode_spec_hash` | Assay (RCE module) | SHA-256 of JCS-canonicalized replay-normative view (§2.1). The replay identity: what was supposed to run. Excludes descriptive metadata. | No |
| `pack_root_sha256` | Assay (proof pack) | SHA-256 of the compiled pack manifest attestation block. The evidence identity: what was actually produced. | No |

**Rationale:** `episode_id` identifies *the thing that ran*. `episode_spec_hash` identifies *the thing that was supposed to run*. `pack_root_sha256` identifies *the artifact compiled from the run*.

### 2.1 Replay-Normative View

`episode_spec_hash` is computed over the **replay-normative subset** of the Episode Contract, excluding descriptive metadata that MUST NOT affect replay identity.

The replay-normative view includes exactly these top-level keys:

- `inputs`
- `replay_script`
- `replay_policy`
- `environment` (identity-bearing subset only; see §2.3)

The replay-normative view **excludes**:

- `schema_version` (envelope, not identity)
- `episode_id` (runtime handle, not specification)
- `objective` (descriptive — see §2.2)
- `environment.env_fingerprint_hash` (derived cross-check, not a direct identity input)
- `environment.model_version_hint` (advisory, not identity)
- `environment.system_fingerprint` (runtime audit field, not identity)

```
replay_normative_environment = {
  "provider":         environment["provider"],
  "model_id":         environment["model_id"],
  "tool_versions":    environment["tool_versions"],
  "container_digest": environment["container_digest"]
}

replay_normative_view = {
  "inputs":         episode_contract["inputs"],
  "replay_script":  episode_contract["replay_script"],
  "replay_policy":  episode_contract["replay_policy"],
  "environment":    replay_normative_environment
}

episode_spec_hash = SHA256( JCS( replay_normative_view ) )
```

JCS canonicalization per [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785). This matches the existing Assay canonicalization regime (`canon_version: "jcs-rfc8785"`).

**Consequence:** Two Episode Contracts with different `objective` text but identical inputs, script, policy, and identity-bearing environment fields produce the **same** `episode_spec_hash`.

### 2.2 Descriptive Fields

`objective` is descriptive. It MUST NOT be used as a dispatch input by the replay verifier and MUST NOT affect `episode_spec_hash`. It is carried in the Episode Contract and in `rce.episode_open/v0` receipts for human context and audit provenance only.

### 2.3 Environment Fingerprint

`env_fingerprint_hash` is a **derived digest** of the identity-bearing subset of `environment`, carried as a verifier cross-check.

```
env_fingerprint_input = {
  "provider":         environment["provider"],
  "model_id":         environment["model_id"],
  "tool_versions":    environment["tool_versions"],
  "container_digest": environment["container_digest"]
}

env_fingerprint_hash = SHA256( JCS( env_fingerprint_input ) )
```

A verifier MUST recompute `env_fingerprint_hash` from these fields and reject the contract if the declared value does not match.

**Excluded from fingerprint:** `env_fingerprint_hash` itself (circular), `model_version_hint` (advisory), `system_fingerprint` (runtime audit).

### 2.4 Derived Hash Fields

Every hash field in the RCE receipt set MUST be recomputable by a second implementation, or explicitly classified as a local attestation.

#### Cross-Verifiable Hashes

| Field | Input | Canonicalization | Ordering | Where |
|-------|-------|-----------------|----------|-------|
| `episode_spec_hash` | `{inputs, replay_script, replay_policy, replay_normative_environment}` | JCS → SHA-256 | JCS key sort | §2.1 |
| `env_fingerprint_hash` | `{provider, model_id, tool_versions, container_digest}` | JCS → SHA-256 | JCS key sort | §2.3 |
| `inputs_hash` | `episode_contract["inputs"]` (full array) | JCS → SHA-256 | Array order from contract | `episode_open` |
| `script_hash` | `episode_contract["replay_script"]` (full object) | JCS → SHA-256 | JCS key sort | `episode_open`, `replay_result` |
| `outputs_hash` | Array of `{"step_id", "output_hash"}` per `EMIT_OUTPUT` step with `step_status: PASS` (excludes SKIPPED/FAIL) | JCS → SHA-256 | Lexicographic by `step_id` | `episode_close` |
| `output_hash` (step) | Step output JSON (opcode-specific; see §3.3) | JCS → SHA-256 | Single object | `episode_step` |
| `input_hashes` (step) | `output_hash` values from direct dependencies | None (pre-computed) | `depends_on` order | `episode_step` |

#### Local Attestation Hashes

These are carried for audit provenance. Downstream consumers do NOT recompute them.

| Field | Semantics | Where | Why Not Cross-Verifiable |
|-------|-----------|-------|--------------------------|
| `config_hash` | Opaque digest of transform configuration | Step `params` | Source config not in receipts/traces |
| `verifier_env_hash` | Verifier's own environment digest (same pattern as §2.3) | `replay_result` | Full verifier env object not exposed in v0 |

#### Dispute Payload Hashes

`expected_output_hash` and `observed_output_hash` (§5.5) use the same derivation as step-level `output_hash`.

#### Verification Rule

A verifier MUST recompute `inputs_hash` and `script_hash` from the Episode Contract and reject the pack if the `episode_open` receipt values do not match. A verifier MUST recompute `outputs_hash` from step receipts and reject the pack if the `episode_close` receipt value does not match. Step-level hashes are verified transitively during replay comparison (§6.2 Phase 4). `config_hash` and `verifier_env_hash` are not replay-identity checks in v0.

---

## 3. ReplayScript v0 [Normative]

v0 is deliberately minimal. Opcodes are typed steps in a DAG.

### 3.1 Opcode Set

| Opcode | Semantics | Required Params | Produces |
|--------|-----------|-----------------|----------|
| `LOAD_INPUT` | Load an immutable input by reference. Verifier checks `ref` resolves and hash matches. | `ref` | Loaded data |
| `ASSERT_HASH` | **Verifier assertion, not an execution transform.** Checks that a prior step's output matches an expected SHA-256 digest. See §3.3. | `target`, `expected_hash` | Boolean pass/fail |
| `APPLY_TRANSFORM` | Apply a named transform to upstream step outputs. v0: recorded-trace only. | `transform`, provider/model/config metadata | Structured output |
| `EMIT_OUTPUT` | Emit a final structured claim into episode outputs. Verifier checks schema validity. See §3.3. | `claim_type`, `output_ref` | Claim |

### 3.2 Deferred Opcodes

Explicitly deferred to v0.1+: `LLM_CALL` (live execution), `TOOL_CALL` (live execution), `COMPARE_SEMANTIC` (Tier C), `ANCHOR` (witness layer), `FETCH` (network I/O during replay).

### 3.3 Step DAG Rules

- Each step MUST declare `depends_on` (array of step_ids, may be empty for root steps).
- Cycles are forbidden. A verifier MUST reject a script containing cycles.
- Steps with no downstream dependents are terminal. At least one terminal step MUST be `EMIT_OUTPUT`.

### 3.4 Step Status Model

Every `rce.episode_step/v0` receipt MUST include `step_status` in its payload.

| Status | Meaning |
|--------|---------|
| `PASS` | Step completed successfully. |
| `FAIL` | Step completed but produced a negative result during original execution. |
| `SKIPPED` | Step was not executed because a dependency had `step_status: FAIL`. |

**Opcode-specific fields:**

- `ASSERT_HASH` steps MUST include `assertion_passed: true | false`.
- `EMIT_OUTPUT` steps with a schema violation MUST include `schema_validation_error: "<message>"`.
- Missing replay artifacts at verification time are `INTEGRITY_FAIL` (§6.2), not step-level `FAIL`.

**Step output hashes by opcode and status:**

| Opcode | `output_hash` input |
|--------|-------------------|
| `LOAD_INPUT` | The loaded input data |
| `APPLY_TRANSFORM` | The transform's structured output |
| `ASSERT_HASH` | `{"assertion_passed": true}` or `{"assertion_passed": false}` |
| `EMIT_OUTPUT` | The emitted claim object |
| *(any, when `step_status: SKIPPED`)* | `null` — field MUST be present with value `null`. No output was produced. |

**SKIPPED step receipts:** `output_hash` MUST be `null`. `input_hashes` MUST be `[]`. `output_size_bytes` and `duration_ms` MUST be `0`. These steps are excluded from `outputs_hash` computation (§2.4) and from Phase 4 replay comparison (§6.2).

### 3.5 Step Failure Propagation

A step with `step_status: FAIL` blocks all direct and transitive dependents. Blocked steps MUST be emitted as receipts with `step_status: SKIPPED`. Every step in the script produces exactly one step receipt.

If any step has `step_status: FAIL` or `SKIPPED`, the `episode_close` receipt MUST set `all_steps_passed: false`. This causes pack-level `claim_check: FAIL` with `receipt_integrity: PASS` (exit 1 / HONEST FAIL).

**`claim_check` is a pack-level and episode-level verdict axis — it does NOT appear on individual step receipts.**

---

## 4. Comparator Tiers [Normative]

| Tier | Name | Method | v0.1 Support |
|------|------|--------|:------------:|
| A | Canonical cryptographic match | `SHA256(JCS(output_a)) == SHA256(JCS(output_b))` — JCS absorbs whitespace/key-ordering. | **YES — sole tier** |
| C | Semantic equivalence | Bounded judge + quorum | Deferred |
| D | Predictive falsification | Future evidence verification | Deferred |

**Why no Tier B:** Tier A already canonicalizes via JCS before hashing, making a separate "canonical-JSON match without hashing" tier operationally indistinguishable. A future version may add Tier B for non-JSON outputs.

### 4.1 Replay Basis

| Value | Meaning | v0.1 |
|-------|---------|:----:|
| `recorded_trace` | Compare against recorded step outputs. No live execution. | **YES** |
| `live_reexecution` | Re-execute steps against live providers. | Deferred |

**This distinction is a replay mode, not an implementation detail.** `replay_basis` and `comparator_tier` are independent axes. A claim verified under `recorded_trace` MUST NOT be presented as equivalent to `live_reexecution`.

---

## 5. Receipt Types [Normative]

All four receipt types emit into the existing `receipt_pack.jsonl` stream and conform to the CRS v0.1 envelope (§3 of [CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md](./CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md)).

**Two version strata — do not conflate:**

| Stratum | Field | Example | Semantics |
|---------|-------|---------|-----------|
| Protocol type | `receipt_type` | `rce.episode_open/v0` | RCE protocol version |
| Container | `schema_version` | `"3.0"` | Assay receipt pack envelope version |

### 5.1 `rce.episode_open/v0`

Emitted once at episode start. Binds the runtime handle to the replay contract.

**Payload fields:**

| Field | Type | Description |
|-------|------|-------------|
| `episode_id` | string | AgentMesh runtime handle |
| `episode_spec_hash` | string | SHA-256 of replay-normative view (§2.1) |
| `objective` | string | Descriptive, not identity-bearing (§2.2) |
| `inputs_hash` | string | SHA-256 of JCS(inputs) (§2.4) |
| `script_hash` | string | SHA-256 of JCS(replay_script) (§2.4) |
| `env_fingerprint_hash` | string | SHA-256 of identity-bearing env subset (§2.3) |
| `replay_basis` | string | `"recorded_trace"` in v0 |
| `comparator_tier` | string | `"A"` in v0 |
| `n_steps` | integer | Total steps in script |

### 5.2 `rce.episode_step/v0`

Emitted once per step execution.

**Payload fields:**

| Field | Type | Description |
|-------|------|-------------|
| `episode_id` | string | Runtime handle |
| `step_id` | string | Step identifier from script |
| `opcode` | string | One of: `LOAD_INPUT`, `ASSERT_HASH`, `APPLY_TRANSFORM`, `EMIT_OUTPUT` |
| `step_status` | string | `PASS`, `FAIL`, or `SKIPPED` (§3.4) |
| `input_hashes` | array[string] | Dependency output hashes in `depends_on` order (§2.4) |
| `output_hash` | string\|null | SHA-256 of JCS(step_output) (§2.4). `null` when `step_status` is `SKIPPED`. |
| `output_size_bytes` | integer | Size of step output |
| `duration_ms` | integer | Step execution duration |
| `comparator_tier` | string | Tier applied to this step |
| `assertion_passed` | boolean | **ASSERT_HASH only.** Redundant with step_status by design. |
| `schema_validation_error` | string | **EMIT_OUTPUT only.** Present when step_status is FAIL. |
| `provider` | string | Optional. Provider identity for APPLY_TRANSFORM. |
| `model_id` | string | Optional. Model identity for APPLY_TRANSFORM. |
| `system_fingerprint` | string | Optional. Runtime-reported fingerprint (audit, not identity). |

### 5.3 `rce.episode_close/v0`

Emitted once at episode completion.

**Payload fields:**

| Field | Type | Description |
|-------|------|-------------|
| `episode_id` | string | Runtime handle |
| `episode_spec_hash` | string | SHA-256 of replay-normative view (§2.1) |
| `outputs_hash` | string | SHA-256 of outputs manifest (§2.4) |
| `n_steps_executed` | integer | Steps actually executed (not SKIPPED) |
| `n_steps_passed` | integer | Steps with step_status PASS |
| `all_steps_passed` | boolean | `false` if any step FAIL or SKIPPED |
| `replay_basis` | string | `"recorded_trace"` in v0 |
| `comparator_tier` | string | `"A"` in v0 |

### 5.4 `rce.replay_result/v0`

Emitted by a replay verifier (not the original executor). This receipt makes RCE a protocol, not just a format.

**Parent binding rule:** `parent_hashes` MUST contain exactly one entry: the `receipt_hash` of the original `rce.episode_close/v0` receipt from the pack under verification. The verifier MUST recompute this hash from validated receipt data — MUST NOT copy from an unverified source. If integrity validation fails before `episode_close` can be verified, emit `verdict: INTEGRITY_FAIL` with `parent_hashes: []`.

**Payload fields:**

| Field | Type | Description |
|-------|------|-------------|
| `episode_id` | string | Runtime handle |
| `episode_spec_hash` | string | SHA-256 of replay-normative view |
| `original_pack_root_sha256` | string | Evidence identity of original pack |
| `verdict` | string | `MATCH`, `DIVERGE`, or `INTEGRITY_FAIL` (§6) |
| `receipt_integrity` | string | `PASS` or `FAIL` |
| `claim_check` | string\|null | `PASS`, `FAIL`, or `null`. MUST be `null` when `verdict` is `INTEGRITY_FAIL` (comparison was not reached). |
| `replay_basis` | string | `"recorded_trace"` in v0 |
| `comparator_tier` | string | `"A"` in v0 |
| `script_hash` | string | SHA-256 of JCS(replay_script) |
| `steps_replayed` | integer | Total steps replayed |
| `steps_matched` | integer | Steps matching under comparator |
| `steps_diverged` | integer | Steps that diverged |
| `divergent_step_ids` | array[string] | IDs of divergent steps |
| `verifier_id` | string | Verifier implementation identifier |
| `verifier_version` | string | Verifier version |
| `verifier_env_hash` | string | Local attestation (§2.4) |
| `dispute` | object\|null | Dispute payload (§5.5); MUST be non-null when verdict is DIVERGE |

### 5.5 Dispute Payload

When `verdict` is `DIVERGE`, the `dispute` field MUST be populated:

- `dispute.divergent_steps` MUST contain **at least one entry**. A `DIVERGE` verdict with empty `divergent_steps` is a protocol violation.
- **Collection policy (v0): exhaust all steps.** The verifier MUST replay all steps before emitting a verdict. MUST NOT stop on first divergence.
- `replay_pack_root_sha256` MUST reference the pack produced by the replay verifier.

**Dispute step fields:**

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | string | Divergent step identifier |
| `expected_output_hash` | string | From original step receipt |
| `observed_output_hash` | string | Recomputed by replayer |
| `comparator_tier` | string | Tier applied |
| `comparator_detail` | string | Human-readable mismatch description |

---

## 6. Verdict Semantics [Normative]

RCE verdicts map onto the existing Assay two-axis contract (`receipt_integrity` × `claim_check`) to preserve Gallery, CI, and Ledger compatibility.

| Verdict | `receipt_integrity` | `claim_check` | Exit Code | Gallery Label |
|---------|:-------------------:|:-------------:|:---------:|:-------------:|
| `MATCH` | PASS | PASS | 0 | **PASS** |
| `DIVERGE` | PASS | FAIL | 1 | **HONEST FAIL** |
| `INTEGRITY_FAIL` | FAIL | `null` | 2 | **TAMPERED** |

### 6.1 Verdict Precedence

`INTEGRITY_FAIL` takes precedence. If evidence integrity fails, the verifier MUST NOT attempt replay comparison.

### 6.2 Mandatory Verification Order

A conforming verifier MUST execute these phases in order. No phase begins until the prior completes. Failure emits the indicated verdict and stops.

| Phase | Action | Failure Verdict |
|:-----:|--------|-----------------|
| **1** | **Script validation.** Parse Episode Contract. Validate: all `step_id` values unique (the verifier MUST enforce uniqueness; JSON Schema `uniqueItems` does not cover object-field uniqueness), all `depends_on` references resolve to declared step_ids, no cycles, at least one terminal EMIT_OUTPUT. | `INTEGRITY_FAIL` |
| **2** | **Pack integrity.** Standard Assay verification: file hashes, receipt chain, signature checks, attestation block. | `INTEGRITY_FAIL` |
| **3** | **Completeness.** Verify artifacts present: Episode Contract, all input artifacts, one recorded trace per non-SKIPPED step. Verify receipts: one `episode_open`, one `episode_step` per script step (including SKIPPED), one `episode_close`. Recompute from the Episode Contract: `episode_spec_hash` (§2.1), `env_fingerprint_hash` (§2.3), `inputs_hash`, `script_hash` (§2.4). Recompute `outputs_hash` (§2.4) from `episode_step` receipt `output_hash` values for EMIT_OUTPUT steps — using **receipt payload values**, not replay artifacts. Reject if any recomputed hash does not match. | `INTEGRITY_FAIL` |
| **4** | **Replay comparison.** For each step in DAG order: skip steps with `step_status: SKIPPED` (no replay artifact exists). For non-SKIPPED steps: verify `input_hashes` against dependency `output_hash` values in `depends_on` order; recompute step output hash from the recorded trace artifact; compare against the step receipt's `output_hash` under the step's declared comparator tier (use `replay_policy.comparator_tiers_by_step[step_id]` if present, otherwise `replay_policy.comparator_tier`). Collect all divergences per §5.5 collection policy. | `DIVERGE` or `MATCH` |

**Consequence:** Two conforming verifiers given the same pack, contract, and traces MUST produce the same verdict.

### 6.3 What Each Verdict Proves and Does Not Prove

| Verdict | Proves | Does NOT Prove |
|---------|--------|----------------|
| `MATCH` | Recorded outputs consistent with receipts under declared tier. Evidence intact. | Original execution correct. Objective achieved. Live re-execution same. |
| `DIVERGE` | Evidence intact. Specific divergent steps identified. | Why divergence occurred. Semantic equivalence (requires Tier C). |
| `INTEGRITY_FAIL` | Something wrong with the evidence. | What specifically was tampered with. |

---

## 7. Episode Contract Schema [Normative]

See [schemas/rce_episode_contract.schema.json](./schemas/rce_episode_contract.schema.json) for the machine-readable JSON Schema.

The Episode Contract is the full specification of an episode. The replay-normative view (§2.1) is a computed subset — the contract carries both normative and descriptive fields.

---

## 8. Compatibility [Informative]

| Existing Surface | RCE Impact | Breaking? |
|-----------------|------------|:---------:|
| `receipt_pack.jsonl` | New receipt types added | No |
| `pack_manifest.json` | `receipt_integrity`/`claim_check` axes preserved | No |
| `pack_signature.sig` | Same Ed25519 signing | No |
| CRS v0.1 envelope | Episode receipts conform | No |
| Gallery exit codes | 0/1/2 mapping preserved | No |
| Ledger | Packs anchored via `pack_root_sha256` | No |

---

## 9. Scope Boundaries [Informative]

### 9.1 In Scope for v0.1

- Episode Contract schema and replay-normative view
- ReplayScript v0 with 4 opcodes
- 4 receipt types conforming to CRS v0.1
- Recorded-trace replay with Tier A comparison
- Deterministic verification order (4 phases)
- Verdict semantics mapped to Assay two-axis contract

### 9.2 Explicitly Deferred

- Quorum settlement (`quorum_settlement.v0`)
- Live provider re-execution (`replay_basis: "live_reexecution"`)
- Semantic comparison (Tier C)
- Time anchoring (RFC 3161 / transparency logs)
- `EpisodeRef` in AgentMesh transport
- `episode_checkpoint.v0` for long episodes
- Cross-repo governance semantics

---

## 10. Relationship to Other Documents

| This Document | Other Document |
|---------------|---------------|
| Episode identity and replay contract | [SPEC.md](./SPEC.md) — tool safety enforcement |
| Receipt types and envelope | [CRS v0.1](./CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md) — receipt format |
| Verdict ↔ exit code mapping | Assay Proof Pack Contract — pack verification |
| MCP tool actions within episodes | [MCP Minimum Profile](./MCP_MINIMUM_PROFILE.md) — gateway conformance |

Implementations using RCE episodes that include MCP tool actions should satisfy both this profile and the MCP Minimum Profile.

---

*Assay Protocol — Replay-Constrained Episode Profile v0.1*
*Companion to SPEC.md v1.0.0-rc1*
