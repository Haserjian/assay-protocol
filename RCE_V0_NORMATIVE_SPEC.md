# Replay-Constrained Episode (RCE) — Normative Specification v0

**Status:** DRAFT — PR A READY (semantics accepted 2026-04-06)
**Date:** 2026-04-06
**Author:** Tim B. Haserjian
**Scope:** Episode v0 schema, ReplayScript v0, receipt types, verdict semantics, boundary rules
**Doctrine tag:** `[DESIGNED]` — not yet `[IMPLEMENTED]`
**Implementation authority:** `RCE_PROFILE.md` in `Haserjian/assay-protocol` (PR #5) is the canonical implementation surface. This spec is the design provenance document. Where they diverge, the profile wins.
**Appendices:** `RCE_BOUNDARY_AMENDMENT_V0.md` (runtime boundary law: read/write boundaries, undeclared-read violation receipts, supersession state machine — `[DESIGNED]`, paper-only, 2026-06-11). Tier language defers to `docs/agents/TIER_ROSETTA.md`.

---

## 0. Conventions

### 0.1 Hash Encoding

All hash fields in this spec use the prefixed format `sha256:<64-char-lowercase-hex>`. Verifiers MUST compare hashes as exact string equality on the prefixed form.

### 0.2 Pinned Invariants

**Episodes are the truth-bearing work unit. Proof packs are the compiled evidence artifact.**

**Do not create two Episode truths.** AgentMesh owns episode identity and provenance. Assay owns replay contracts, receipts, and proof compilation.

---

## 1. Identity Triangle

An RCE system distinguishes three identities that MUST NOT be conflated:

| Identity | Owner | Semantics | Mutable? |
|----------|-------|-----------|----------|
| `episode_id` | AgentMesh | Operational runtime handle. AgentMesh-native time-sortable identifier (`ep_` prefix + 48-bit ms timestamp + 48-bit random). Used for lifecycle binding, task correlation, and transport. Not a standard ULID — do not assume ULID semantics. | No (assigned at episode start, never reassigned) |
| `episode_spec_hash` | Assay (RCE module) | SHA-256 of JCS-canonicalized **replay-normative view** of the Episode Contract (§2.1). This is the *replay identity*: the immutable fingerprint of what was supposed to run. Excludes descriptive metadata that must not affect replay identity. | No (computed once from frozen contract) |
| `pack_root_sha256` | Assay (proof pack) | SHA-256 of the compiled pack manifest attestation block. This is the *evidence identity*: the fingerprint of what was actually produced. | No (computed once at pack seal) |

**Rationale:** `episode_id` identifies *the thing that ran*. `episode_spec_hash` identifies *the thing that was supposed to run*. `pack_root_sha256` identifies *the artifact compiled from the run*. These are not the same object.

**Compatibility:** `episode_id` format is unchanged from AgentMesh `episodes.py::generate_episode_id()`. `pack_root_sha256` format is unchanged from existing `pack_manifest.json`. Only `episode_spec_hash` is new.

---

## 2. Episode Contract v0

The Episode Contract is the replay-relevant subset of an episode's specification. It is the input to `episode_spec_hash`.

```json
{
  "schema_version": "rce/0.1",
  "episode_id": "ep_019d07dfe648e3636b986339",
  "objective": "Analyze loan application and produce structured decision with adverse action explanation",
  "inputs": [
    {
      "ref": "loan_application_data",
      "hash": "sha256:a3f2...9e01",
      "media_type": "application/json"
    }
  ],
  "replay_script": {
    "schema_version": "replay_script/0.1",
    "steps": [
      {
        "step_id": "s01",
        "opcode": "LOAD_INPUT",
        "params": { "ref": "loan_application_data" },
        "depends_on": []
      },
      {
        "step_id": "s02",
        "opcode": "APPLY_TRANSFORM",
        "params": {
          "transform": "loan_analysis",
          "provider": "anthropic",
          "model_id": "claude-sonnet-4-20250514",
          "config_hash": "sha256:b4e1...0c22"
        },
        "depends_on": ["s01"],
        "output_schema": { "$ref": "#/definitions/loan_analysis_result" }
      },
      {
        "step_id": "s03",
        "opcode": "ASSERT_HASH",
        "params": {
          "target": "s02.output",
          "expected_hash": "sha256:d7f3...8a91"
        },
        "depends_on": ["s02"]
      },
      {
        "step_id": "s04",
        "opcode": "EMIT_OUTPUT",
        "params": {
          "claim_type": "loan_decision",
          "output_ref": "s02.output"
        },
        "depends_on": ["s03"]
      }
    ]
  },
  "replay_policy": {
    "replay_basis": "recorded_trace",
    "comparator_tier": "A",
    "comparator_tiers_by_step": {
      "s01": "A",
      "s02": "A",
      "s03": "A",
      "s04": "A"
    }
  },
  "environment": {
    "env_fingerprint_hash": "sha256:c9d2...1f44",
    "provider": "anthropic",
    "model_id": "claude-sonnet-4-20250514",
    "model_version_hint": null,
    "system_fingerprint": null,
    "tool_versions": {
      "assay": "1.15.1",
      "agentmesh": "0.9.0"
    },
    "container_digest": null
  }
}
```

> **Note:** `env_fingerprint_hash` is a derived field whose normative computation is defined in §2.3. It MUST be recomputed and verified, not trusted from the contract.

### 2.1 Hash computation — replay-normative view

`episode_spec_hash` is computed over the **replay-normative subset** of the Episode Contract, excluding descriptive metadata that must not affect replay identity.

The replay-normative view includes exactly these top-level keys:

- `inputs`
- `replay_script`
- `replay_policy`
- `environment` (identity-bearing subset only; see below and §2.3)

The replay-normative view **excludes**:

- `schema_version` (envelope, not identity)
- `episode_id` (runtime handle, not specification)
- `objective` (descriptive — see §2.2)
- `environment.env_fingerprint_hash` (derived cross-check, not a direct identity input)
- `environment.model_version_hint` (advisory, not identity)
- `environment.system_fingerprint` (runtime audit field, not identity)

```
replay_normative_environment = {
  "provider":         episode_contract["environment"]["provider"],
  "model_id":         episode_contract["environment"]["model_id"],
  "tool_versions":    episode_contract["environment"]["tool_versions"],
  "container_digest": episode_contract["environment"]["container_digest"]
}

replay_normative_view = {
    "inputs":         episode_contract["inputs"],
    "replay_script":  episode_contract["replay_script"],
    "replay_policy":  episode_contract["replay_policy"],
    "environment":    replay_normative_environment
}

episode_spec_hash = SHA256( JCS( replay_normative_view ) )
```

JCS canonicalization per RFC 8785. This matches the existing Assay canonicalization regime (`canon_version: "jcs-rfc8785"`).

**Consequence:** Two Episode Contracts with different `objective` text but identical inputs, script, policy, and identity-bearing environment fields produce the **same** `episode_spec_hash`. This is intentional — the objective is for humans and audit trails, not for replay identity. Likewise, differing `model_version_hint` or `system_fingerprint` values alone do **not** change `episode_spec_hash`.

### 2.2 Descriptive fields are not dispatch inputs and not identity inputs

Per Assay doctrine: `objective` is descriptive. It MUST NOT be used as a dispatch input by the replay verifier and MUST NOT affect `episode_spec_hash`. It is carried in the Episode Contract and in `episode_open.v0` receipts for human context and audit provenance only.

Only `inputs`, `replay_script`, `replay_policy`, and the identity-bearing subset of `environment` defined in §2.1/§2.3 are mechanically and identity-relevant.

### 2.3 `env_fingerprint_hash` computation

`env_fingerprint_hash` is a **derived digest** of the identity-bearing subset of `environment`. The replay-normative view hashes the source fields directly (§2.1), while `env_fingerprint_hash` is carried in the contract and receipts as a verifier cross-check. Its computation MUST therefore be normatively defined.

**v0 rule:** `env_fingerprint_hash` is the SHA-256 of the JCS-canonicalized JSON object containing exactly these fields from the `environment` block, in this order after JCS canonicalization:

- `provider` (string, required)
- `model_id` (string, required)
- `tool_versions` (object mapping tool name → semver string, required — may be empty `{}`)
- `container_digest` (string or null, required)

**Excluded from fingerprint computation:**

- `env_fingerprint_hash` itself (circular)
- `model_version_hint` (advisory, not identity — providers do not guarantee version stability)
- `system_fingerprint` (runtime-reported, not pre-declarable — recorded for audit but not identity)

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

### 2.4 Derived hash fields — normative computation rules

Several hash fields appear in receipts as binding digests. The hashes that bind the original Episode Contract and its step outputs MUST be recomputable by a second implementation from the contract, receipt set, and replay artifacts alone. No such cross-verifiable hash may depend on implementation-private state.

**Episode-level derived hashes** (appear in `episode_open.v0` and `episode_close.v0`):

| Field | Derivation | Appears in |
|-------|-----------|------------|
| `inputs_hash` | `SHA256( JCS( episode_contract["inputs"] ) )` — canonical hash of the full `inputs` array from the Episode Contract. | `episode_open.v0` |
| `script_hash` | `SHA256( JCS( episode_contract["replay_script"] ) )` — canonical hash of the full `replay_script` object from the Episode Contract. | `episode_open.v0`, `replay_result.v0` |
| `outputs_hash` | `SHA256( JCS( outputs_manifest ) )` where `outputs_manifest` is a JSON array of `{"step_id": "<id>", "output_hash": "<hash>"}` objects, one per `EMIT_OUTPUT` step **with `step_status: PASS`** (excludes SKIPPED/FAIL), sorted lexicographically by `step_id`. Each `output_hash` value is the step-level `output_hash` from that step's `episode_step.v0` receipt. | `episode_close.v0` |

**Step-level derived hashes** (appear in every `episode_step.v0`):

| Field | Derivation |
|-------|-----------|
| `output_hash` | `SHA256( JCS( step_output ) )` where `step_output` is the JSON output produced by the step. For `LOAD_INPUT`: the loaded input data. For `APPLY_TRANSFORM`: the transform's structured output. For `ASSERT_HASH`: `{"assertion_passed": true}` or `{"assertion_passed": false}`. For `EMIT_OUTPUT`: the emitted claim object. **When `step_status` is `SKIPPED`: `output_hash` MUST be `null`.** |
| `input_hashes` | Array of `output_hash` values from the step's direct dependencies, in the order those dependencies appear in the step's `depends_on` array. For root steps (empty `depends_on`), this is `[]`. |

**Local attestation hashes** (carried for audit, not part of cross-verifiable replay identity):

| Field | Semantics | Where |
|-------|-----------|-------|
| `config_hash` | Opaque digest of the transform configuration used by the original executor (e.g., prompt template, tool config). Provided in `APPLY_TRANSFORM` step params. The replay verifier records it but does not recompute it in v0 — it is an executor attestation. A future version may define normative config canonicalization. | Step `params` |
| `verifier_env_hash` | Self-attested digest of the replay verifier's own environment snapshot. It is computed as `SHA256( JCS( verifier_env ) )` where `verifier_env` contains the verifier's own `provider`, `model_id` (if applicable), `tool_versions`, and `container_digest`, using the same canonicalization pattern as `env_fingerprint_hash` (§2.3). Because v0 carries only the digest and not the full `verifier_env` object, downstream consumers do **not** recompute this field; it is audit metadata, not a replay-identity input. | `replay_result.v0` |

**Dispute payload hashes** (`expected_output_hash`, `observed_output_hash` in §5.5): these are copied from the original step receipt's `output_hash` and the replayer's recomputed `output_hash` respectively. They use the same derivation as step-level `output_hash` above.

**Verification rule:** A verifier MUST recompute `inputs_hash` and `script_hash` from the Episode Contract and reject the pack if the values in the `episode_open.v0` receipt do not match. A verifier MUST recompute `outputs_hash` from the step receipts and reject the pack if the value in the `episode_close.v0` receipt does not match. Step-level `output_hash` and `input_hashes` are verified transitively during replay comparison (§6.2 Phase 4). `config_hash` and `verifier_env_hash` are not replay-identity checks in v0.

---

## 3. ReplayScript v0 — Opcode Set

v0 is deliberately minimal. Opcodes are typed steps in a DAG.

| Opcode | Semantics | Required params | Produces |
|--------|-----------|-----------------|----------|
| `LOAD_INPUT` | Load an immutable input by reference. Verifier checks `ref` resolves and hash matches. | `ref` | Loaded data available to downstream steps |
| `ASSERT_HASH` | **Verifier assertion, not an execution transform.** Checks that a prior step's output matches an expected SHA-256 digest. Does not produce new data or perform computation — it binds a prior artifact to an expected digest. Duration is verification overhead, not work. See §3.3 for failure semantics. | `target`, `expected_hash` | Boolean pass/fail |
| `APPLY_TRANSFORM` | Apply a named transform to upstream step outputs. For v0: recorded-trace only — verifier replays from recorded evidence, not live execution. | `transform`, plus provider/model/config metadata | Structured output |
| `EMIT_OUTPUT` | Emit a final structured claim into the Episode outputs. Verifier checks schema validity against `output_schema` if declared on the referenced step. See §3.3 for failure semantics. | `claim_type`, `output_ref` | Claim in episode output set |

### 3.1 What is NOT in v0

These opcodes are explicitly deferred to v0.1+:

- `LLM_CALL` as a live-execution opcode (v0 treats LLM interactions as `APPLY_TRANSFORM` over recorded traces)
- `TOOL_CALL` as a live-execution opcode (same treatment)
- `COMPARE_SEMANTIC` (requires judge consensus — Tier C territory)
- `ANCHOR` (requires witness layer — deferred to time-anchoring work)
- `FETCH` (network I/O during replay — v0 is fully offline)

### 3.2 Step DAG rules

- Each step MUST declare `depends_on` (array of step_ids, may be empty for root steps).
- Cycles are forbidden. A verifier MUST reject a script containing cycles.
- Steps with no downstream dependents are terminal. At least one terminal step MUST be `EMIT_OUTPUT`.

### 3.3 Step status model

Every `episode_step.v0` receipt MUST include a `step_status` field in its payload. Legal values:

| Status | Meaning |
|--------|---------|
| `PASS` | Step completed successfully. For `ASSERT_HASH`: digest matched. For `EMIT_OUTPUT`: output conforms to declared schema (or no schema declared). For `LOAD_INPUT` and `APPLY_TRANSFORM`: ref resolved / transform completed without error. |
| `FAIL` | Step completed but produced a negative result during the original episode execution. For `ASSERT_HASH`: digest did not match. For `EMIT_OUTPUT`: output does not conform to declared `output_schema`. For `LOAD_INPUT`: the executor could not resolve the declared input or the loaded bytes failed the declared input hash check. For `APPLY_TRANSFORM`: the transform errored or emitted a malformed step artifact. |
| `SKIPPED` | Step was not executed because a dependency had `step_status: FAIL`. |

**Opcode-specific fields:**

- `ASSERT_HASH` steps MUST include `assertion_passed: true | false` in their payload. This is redundant with `step_status` by design — it makes assertions greppable without interpreting the status enum.
- `EMIT_OUTPUT` steps with a schema violation MUST include `schema_validation_error: "<message>"` in their payload.
- Replay-time absence of `episode_contract.json`, referenced input artifacts, or recorded trace artifacts is **not** a step-level `FAIL`. These are verifier evidence-completeness failures and MUST surface as `INTEGRITY_FAIL` under §6.2.

### 3.4 Step failure propagation

**Dependency blocking:** A step with `step_status: FAIL` blocks all direct and transitive dependents. Blocked steps MUST be emitted as `episode_step.v0` receipts with `step_status: SKIPPED`. A verifier MUST NOT silently omit skipped steps — every step in the script produces exactly one step receipt.

**Episode-level propagation:** If any step has `step_status: FAIL` or `step_status: SKIPPED`, the `episode_close.v0` receipt MUST set `all_steps_passed: false`. This causes the **pack-level** `claim_check` to be `FAIL` while `receipt_integrity` remains `PASS` (the evidence chain is intact; the claims did not hold). This maps to exit 1 / HONEST FAIL.

**Important:** `claim_check` is a pack-level and episode-level verdict axis — it does NOT appear on individual step receipts. Individual steps report `step_status`. The propagation rule is: any step `FAIL` → episode `all_steps_passed: false` → pack `claim_check: FAIL`.

---

## 4. Comparator Tiers

| Tier | Name | Comparison method | When to use | v0 support |
|------|------|-------------------|-------------|------------|
| A | Canonical cryptographic match | `SHA256(JCS(output_a)) == SHA256(JCS(output_b))` — both sides are JCS-canonicalized before hashing, so whitespace and key-ordering differences are absorbed. | Structured data, deterministic transforms, any output representable as canonical JSON | YES — sole tier in v0 |
| C | Semantic equivalence | Bounded judge prompt with recorded evidence, quorum required | LLM outputs where wording differs but meaning is preserved | NO — explicitly deferred |
| D | Predictive falsification | Output produces testable future predictions; verified by later evidence | Forecasts, commitments | NO — explicitly deferred |

**Why there is no Tier B in v0:** An earlier draft defined Tier B as "JCS normalization then byte compare without hashing." Because Tier A already canonicalizes via JCS before hashing, the two tiers were operationally indistinguishable for collision-resistant purposes. A future version may introduce a Tier B for non-JSON outputs (e.g., binary blobs compared by raw SHA-256 without canonicalization), but v0 handles only JSON-representable outputs, making a separate tier unnecessary.

### 4.1 replay_basis

The `replay_basis` field in `replay_policy` declares what kind of replay is being performed:

| Value | Meaning | v0? |
|-------|---------|-----|
| `recorded_trace` | Replay compares against recorded step outputs from the original run. No live execution. | YES — only value in v0 |
| `live_reexecution` | Replay re-executes steps against live providers and compares outputs. | NO — deferred |

**This distinction is a replay mode, not an implementation detail.** `replay_basis` and `comparator_tier` are independent axes — do not conflate them. A claim verified under `recorded_trace` replay MUST NOT be presented as equivalent to a claim verified under `live_reexecution`.

---

## 5. Receipt Types

All four receipt types emit into the existing `receipt_pack.jsonl` stream. They follow CRS v0.1 envelope conventions (§3 of Constitutional Receipt Standard): `receipt_id`, `receipt_type`, `ts`, `payload`, `receipt_hash`, `parent_hashes`, `proof_tier`, `schema_version`.

They also carry the Assay-native fields needed for pack compatibility: `_trace_id`, `_stored_at`, `seq`, `schema_version: "3.0"`.

**Two version strata — do not conflate:**

| Stratum | Field | Example | Semantics |
|---------|-------|---------|-----------|
| **Protocol type version** | `receipt_type` | `rce.episode_open/v0` | Identifies the receipt kind and its schema generation. The `/v0` suffix is the RCE protocol version. |
| **Container/envelope version** | `schema_version` | `"3.0"` | Identifies the Assay receipt pack envelope format. All receipt types (RCE and non-RCE) in the same pack share this version. |

These are independent version axes. `schema_version: "3.0"` does not conflict with `/v0` in `receipt_type` — one versions the container, the other versions the payload contract.

### 5.1 `episode_open.v0`

Emitted once at episode start. Binds the runtime handle to the replay contract.

```json
{
  "receipt_id": "r_ep_open_a1b2c3d4e5f6",
  "receipt_type": "rce.episode_open/v0",
  "ts": "2026-03-07T06:08:31.483376+00:00",
  "_trace_id": "trace_20260307T060831_9f640976",
  "_stored_at": "2026-03-07T06:08:31.483376+00:00",
  "seq": 0,
  "schema_version": "3.0",

  "payload": {
    "episode_id": "ep_019d07dfe648e3636b986339",
    "episode_spec_hash": "sha256:e4a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
    "objective": "Analyze loan application and produce structured decision",
    "inputs_hash": "sha256:a3f2...9e01",
    "script_hash": "sha256:7c88...3df2",
    "env_fingerprint_hash": "sha256:c9d2...1f44",
    "replay_basis": "recorded_trace",
    "comparator_tier": "A",
    "n_steps": 4
  },

  "parent_hashes": [],
  "proof_tier": "core",
  "receipt_hash": "sha256:..."
}
```

### 5.2 `episode_step.v0`

Emitted once per step execution. Records inputs, outputs, timing, and step-level hashes.

```json
{
  "receipt_id": "r_ep_step_b2c3d4e5f6a7",
  "receipt_type": "rce.episode_step/v0",
  "ts": "2026-03-07T06:08:31.483500+00:00",
  "_trace_id": "trace_20260307T060831_9f640976",
  "_stored_at": "2026-03-07T06:08:31.483500+00:00",
  "seq": 1,
  "schema_version": "3.0",

  "payload": {
    "episode_id": "ep_019d07dfe648e3636b986339",
    "step_id": "s02",
    "opcode": "APPLY_TRANSFORM",
    "step_status": "PASS",
    "input_hashes": ["sha256:a3f2...9e01"],
    "output_hash": "sha256:d7f3...8a91",
    "output_size_bytes": 2048,
    "duration_ms": 1203,
    "provider": "anthropic",
    "model_id": "claude-sonnet-4-20250514",
    "system_fingerprint": null,
    "comparator_tier": "A"
  },

  "parent_hashes": ["sha256:<episode_open receipt_hash>"],
  "proof_tier": "core",
  "receipt_hash": "sha256:..."
}
```

### 5.3 `episode_close.v0`

Emitted once at episode completion. Binds final outputs and declares the episode contract fulfilled (or not).

```json
{
  "receipt_id": "r_ep_close_c3d4e5f6a7b8",
  "receipt_type": "rce.episode_close/v0",
  "ts": "2026-03-07T06:08:31.483800+00:00",
  "_trace_id": "trace_20260307T060831_9f640976",
  "_stored_at": "2026-03-07T06:08:31.483800+00:00",
  "seq": 5,
  "schema_version": "3.0",

  "payload": {
    "episode_id": "ep_019d07dfe648e3636b986339",
    "episode_spec_hash": "sha256:e4a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
    "outputs_hash": "sha256:f1e2...a3b4",
    "n_steps_executed": 4,
    "n_steps_passed": 4,
    "all_steps_passed": true,
    "replay_basis": "recorded_trace",
    "comparator_tier": "A"
  },

  "parent_hashes": ["sha256:<last step receipt_hash>"],
  "proof_tier": "core",
  "receipt_hash": "sha256:..."
}
```

### 5.4 `replay_result.v0`

Emitted by a replay verifier (not the original executor). This is the receipt that makes RCE a protocol, not just a format.

**Parent binding rule:** `replay_result.v0.parent_hashes` MUST contain exactly one entry: the `receipt_hash` of the original `episode_close.v0` receipt from the pack under verification. The verifier MUST recompute this hash from the validated original receipt data — it MUST NOT copy the hash from an unverified source. If the original pack fails integrity validation before the `episode_close.v0` receipt can be verified, the verifier MUST emit `verdict: INTEGRITY_FAIL` with `parent_hashes: []` (no trusted parent exists).

```json
{
  "receipt_id": "r_replay_d4e5f6a7b8c9",
  "receipt_type": "rce.replay_result/v0",
  "ts": "2026-04-06T14:22:00.000000+00:00",
  "_trace_id": "trace_20260406T142200_replay_01",
  "_stored_at": "2026-04-06T14:22:00.000000+00:00",
  "seq": 0,
  "schema_version": "3.0",

  "payload": {
    "episode_id": "ep_019d07dfe648e3636b986339",
    "episode_spec_hash": "sha256:e4a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
    "original_pack_root_sha256": "sha256:6e6b...ebc8",

    "verdict": "MATCH",
    "receipt_integrity": "PASS",
    "claim_check": "PASS",

    "replay_basis": "recorded_trace",
    "comparator_tier": "A",
    "script_hash": "sha256:7c88...3df2",

    "steps_replayed": 4,
    "steps_matched": 4,
    "steps_diverged": 0,
    "divergent_step_ids": [],

    "verifier_id": "assay-replay-verify-py",
    "verifier_version": "0.1.0",
    "verifier_env_hash": "sha256:aa11...bb22",

    "dispute": null
  },

  "parent_hashes": ["sha256:<recomputed episode_close receipt_hash>"],
  "proof_tier": "core",
  "receipt_hash": "sha256:..."
}
```

### 5.5 Dispute payload (when verdict is DIVERGE)

When `verdict` is `DIVERGE`, the `dispute` field MUST be populated. The following constraints are normative:

- `dispute.divergent_steps` MUST contain **at least one entry**. A `DIVERGE` verdict with an empty `divergent_steps` array is a protocol violation.
- **Collection policy (v0): exhaust all steps.** The verifier MUST complete integrity validation and then replay **all** steps before emitting a verdict. It MUST NOT stop on the first divergence. This ensures the dispute payload is complete — a consumer can see all divergent steps, not just the first one encountered. (This policy may change in future versions for performance, but v0 prioritizes completeness over short-circuiting.)
- `replay_pack_root_sha256` MUST reference the pack produced by the replay verifier containing this `replay_result.v0` receipt.

```json
{
  "dispute": {
    "divergent_steps": [
      {
        "step_id": "s02",
        "expected_output_hash": "sha256:d7f3...8a91",
        "observed_output_hash": "sha256:ee44...cc55",
        "comparator_tier": "A",
        "comparator_detail": "JCS hash mismatch"
      }
    ],
    "replay_pack_root_sha256": "sha256:1234...5678"
  }
}
```

---

## 6. Verdict Semantics

RCE verdicts map onto the existing Assay two-axis contract (`receipt_integrity` × `claim_check`) to preserve Gallery, CI, and Ledger compatibility.

| RCE Verdict | `receipt_integrity` | `claim_check` | Assay exit code | Gallery label | Meaning |
|-------------|--------------------|--------------:|:---------------:|:-------------:|---------|
| `MATCH` | `PASS` | `PASS` | 0 | **PASS** | Replay succeeded. All step outputs match under declared comparator tier. Evidence is intact and claims hold. |
| `DIVERGE` | `PASS` | `FAIL` | 1 | **HONEST FAIL** | Replay evidence is intact (not tampered), but one or more step outputs diverged from the original under the declared comparator. Dispute payload identifies which steps and how. |
| `INTEGRITY_FAIL` | `FAIL` | `null` | 2 | **TAMPERED** | Evidence integrity check failed before replay could complete. Hash mismatch, missing receipts, broken chain, or signature failure. `claim_check` is `null` because comparison was not reached. |

### 6.1 Verdict precedence

`INTEGRITY_FAIL` takes precedence over `DIVERGE`. If evidence integrity fails, the verifier MUST NOT attempt replay comparison — the data cannot be trusted.

### 6.2 Mandatory verification order

A conforming verifier MUST execute these phases in this exact order. No phase may begin until the prior phase completes successfully. If any phase fails, the verifier MUST emit the appropriate verdict and stop.

| Phase | What it does | Failure verdict |
|-------|-------------|-----------------|
| **1. Script validation** | Parse the Episode Contract. Validate `replay_script` structure: all step_ids unique, all `depends_on` references resolve, no cycles, at least one terminal `EMIT_OUTPUT`. | `INTEGRITY_FAIL` — malformed contract |
| **2. Pack integrity** | Verify the original proof pack using the standard Assay verification flow: file hashes, receipt chain, signature checks, attestation block. This is the existing mechanical verification, not RCE-specific. | `INTEGRITY_FAIL` — evidence integrity broken |
| **3. Replay input and receipt completeness** | Confirm the verifier has the artifacts required to attempt replay: the Episode Contract, every referenced input artifact, and one recorded trace artifact per non-SKIPPED step. Confirm the pack contains exactly one `episode_open.v0`, one `episode_step.v0` per script step (including SKIPPED), and one `episode_close.v0`. Recompute from the Episode Contract: `episode_spec_hash` (§2.1), `env_fingerprint_hash` (§2.3), `inputs_hash`, `script_hash` (§2.4). Recompute `outputs_hash` (§2.4) from `episode_step.v0` receipt `output_hash` values for PASS EMIT_OUTPUT steps — using **receipt payload values**, not replay artifacts. Reject if any recomputed hash does not match. | `INTEGRITY_FAIL` — replay artifact set incomplete, receipt set incomplete, or derived hash mismatch |
| **4. Replay comparison** | For each step in DAG order: skip steps with `step_status: SKIPPED` (no replay artifact exists). For non-SKIPPED steps: verify `input_hashes` against dependency `output_hash` values in `depends_on` order; recompute step output hash from the recorded trace artifact; compare against the step receipt's `output_hash` under the step's declared comparator tier (use `replay_policy.comparator_tiers_by_step[step_id]` if present, otherwise `replay_policy.comparator_tier`). Collect all divergences (§5.5 collection policy). | `DIVERGE` if any step mismatches; `MATCH` if all pass |

**Consequence:** Two conforming verifiers given the same pack and contract MUST produce the same verdict. The fixed phase order eliminates implementation-dependent races between `INTEGRITY_FAIL` and `DIVERGE`.

### 6.3 What each verdict proves and does not prove

| Verdict | Proves | Does NOT prove |
|---------|--------|----------------|
| `MATCH` | Step outputs are consistent with the recorded trace under the declared comparator tier. Evidence chain is intact. | That the original execution was correct. That the episode objective was achieved. That live re-execution would produce the same result. |
| `DIVERGE` | Evidence chain is intact. At least one step output differs from the recorded trace. The specific divergent steps are identified. | Why the divergence occurred. Whether the divergence matters semantically (that requires Tier C). |
| `INTEGRITY_FAIL` | Something is wrong with the evidence. | What specifically was tampered with (beyond what the hash check identifies). |

---

## 7. Boundary Rules

### 7.1 Repo ownership

| Repo | Owns | Does NOT own |
|------|------|-------------|
| **AgentMesh** | `episode_id` generation and lifecycle. Episode provenance (weave chain). EpisodeRef in transport envelopes. `EPISODE_START` / `EPISODE_END` events. | Replay contracts. Replay verification. Receipt compilation into proof packs. |
| **Assay** (new `rce/` module) | Episode Contract schema. ReplayScript v0 DSL. Four receipt types. Replay verifier. `episode_spec_hash` computation. Pack compilation from episode receipts. | `episode_id` generation. Episode lifecycle management. Provenance/lineage. |
| **assay-protocol** | Normative RCE profile (sibling to tool-safety profile, NOT a chapter inside it). Comparator tier definitions. Dispute packet schema. | Implementation code. Runtime behavior. |
| **assay-proof-gallery** | RCE demo scenarios (replay match, replay divergence, tampered replay). | Protocol definitions. |
| **assay-verify-action** | CI-mode replay verification. | Normative schema. |
| **assay-verify-ts** | Independent TS replay verifier (second implementation). | Python implementation details. |
| **Loom/CCIO** | Consuming RCE evidence for policy gating and claim promotion. | Producing or defining replay contracts. |

### 7.2 What is NOT in scope for v0

- Quorum settlement (`quorum_settlement.v0` receipt — deferred)
- Live provider re-execution (`replay_basis: "live_reexecution"` — deferred)
- Semantic comparison (Tier C — deferred)
- Time anchoring (RFC 3161 / Rekor — parallel work, not blocking)
- `EpisodeRef` in AgentMesh transport (added only after pack + verifier exist)
- Cross-repo governance semantics
- Rich judge consensus
- `episode_checkpoint.v0` for long episodes

### 7.3 Compatibility constraints

- Episode receipts MUST emit into existing `receipt_pack.jsonl` format (JSONL, one object per line).
- Episode receipts MUST be hashable under JCS (RFC 8785) using the same algorithm as existing receipts.
- Episode receipts MUST be signable under Ed25519 (RFC 8032) when `proof_tier` is `court`.
- Pack manifests containing episode receipts MUST include `receipt_integrity` and `claim_check` in the attestation block, preserving exit code semantics.
- The `_trace_id` field MUST correlate episode receipts with existing receipt types in the same pack (model_call, guardian_verdict, capability_use, etc.).

---

## 8. PR Sequence

Narrowest safe rollout, in order:

| PR | Repo | Scope | Depends on |
|----|------|-------|------------|
| **A** | assay-protocol | New RCE profile: Episode Contract v0 schema, ReplayScript v0 schema, comparator tier definitions, receipt type schemas, verdict semantics, dispute packet schema. Sibling to existing tool-safety profile. | Nothing |
| **B** | assay | New `rce/` module: Episode Contract parser, `episode_spec_hash` computation, ReplayScript v0 interpreter (recorded-trace mode), replay verifier, receipt emitters for 4 types. CLI: `assay episode run` + `assay episode verify`. Tests. | PR A (schema) |
| **C** | assay-proof-gallery | Two new scenarios: "RCE Replay Match" (exit 0) and "RCE Replay Divergence" (exit 1). Optionally: "RCE Tampered Replay" (exit 2). | PR B (implementation) |
| **D** | assay-verify-ts | Extend TS verifier to validate episode receipt types and replay_result verdicts. | PR A (schema) |
| **E** | assay-verify-action | Add `replay_mode` input. When enabled, run replay verification on CI and report verdict. | PR B + PR D |
| **F** | agentmesh | Add `EpisodeRef` type binding `episode_id` → `episode_spec_hash` + `pack_root_sha256`. Add `replay_of`, `derived_from`, `witnessed_by` edge types to weave/event model. | PR B (pack + verifier must exist first) |

---

## 9. Golden-Path Fixture

One complete recorded-trace episode demonstrating the full lifecycle.

### 9.1 Scenario: Loan Application Analysis

**Objective:** Analyze a loan application, query credit bureau, synthesize decision, write output, explain adverse action.

**Steps:**
1. `LOAD_INPUT` — load loan application JSON
2. `APPLY_TRANSFORM` — analyze application (recorded model_call trace)
3. `ASSERT_HASH` — verify analysis output hash
4. `EMIT_OUTPUT` — emit loan_decision claim

**Expected pack contents:**
```
golden_rce_fixture/
├── proof_pack/
│   ├── receipt_pack.jsonl          # episode_open + 4× episode_step + episode_close
│   ├── pack_manifest.json          # standard manifest with receipt_integrity + claim_check
│   ├── verify_report.json          # standard verify report
│   ├── verify_transcript.md        # human-readable verification log
│   └── pack_signature.sig          # Ed25519 signature
├── episode_contract.json           # the Episode Contract (input to episode_spec_hash)
├── recorded_traces/
│   ├── s01_output.json             # recorded LOAD_INPUT output
│   ├── s02_output.json             # recorded APPLY_TRANSFORM output
│   ├── s03_output.json             # recorded ASSERT_HASH output (pass/fail)
│   └── s04_output.json             # recorded EMIT_OUTPUT output
└── replay_results/
    ├── replay_01/
    │   ├── receipt_pack.jsonl      # replay_result.v0 receipt
    │   └── pack_manifest.json      # replay pack manifest (verdict: MATCH)
    └── replay_02_diverge/
        ├── receipt_pack.jsonl      # replay_result.v0 receipt (verdict: DIVERGE)
        └── pack_manifest.json      # replay pack manifest (claim_check: FAIL)
```

### 9.2 Verification flow

1. **Original run:** Episode opens → steps execute → receipts emit → pack seals → `receipt_integrity: PASS`, `claim_check: PASS` → exit 0.
2. **Replay (match):** Second machine loads `episode_contract.json` + `recorded_traces/` + `proof_pack/`. Replays each step by comparing recorded trace outputs against receipt hashes. All match → `replay_result.v0` with `verdict: MATCH` → exit 0.
3. **Replay (diverge):** The `replay_02_diverge/` fixture ships an **alternate recorded trace file** (`s02_output.json`) whose content differs from the original. This simulates the scenario where a second recorded execution produced different output for the same step. The verifier compares the alternate trace against the original pack's step receipt hashes, finds a mismatch at step s02 → `verdict: DIVERGE` with dispute payload → exit 1. No live re-execution occurs — both sides are recorded artifacts.
4. **Replay (tampered):** `receipt_pack.jsonl` has been modified. Integrity check fails before replay begins → `verdict: INTEGRITY_FAIL` → exit 2.

---

## 10. Open Questions (Parked, Not Blocked)

These are real design questions that v0 intentionally does not answer:

1. **~~Should `episode_spec_hash` include `environment`?~~** RESOLVED in v0 tightening pass: `episode_spec_hash` is computed over the replay-normative view (§2.1), which **includes** `environment`. Same script + different model version = different spec hash. `objective`, `schema_version`, and `episode_id` are excluded. The remaining open question is whether `environment` should move out of identity in a future version to support cross-provider replay portability testing.

2. **How does Tier C (semantic equivalence) interact with the existing CRS `proof_tier` ladder?** Likely: Tier C results are `proof_tier: "claim"` (C-tier in Loom terms) until judge evidence is independently verified. But this needs alignment with Loom doctrine.

3. **Should `episode_checkpoint.v0` exist for long-running episodes?** Probably yes, but not until there's a real episode that needs it.

4. **How do multiple `replay_result.v0` receipts compose into a quorum?** The `quorum_settlement.v0` receipt type is designed for this. It aggregates N replay results and declares a threshold. Deferred.

5. **Should the normative RCE profile in assay-protocol be a separate document or a separate section within SPEC.md?** Current recommendation: separate document (`RCE_PROFILE.md`), because the current SPEC.md is explicitly an MCP gateway tool-safety conformance surface. Mixing would confuse scope.

---

## Appendix A: Compatibility Matrix

| Existing surface | RCE impact | Breaking? |
|-----------------|------------|-----------|
| `receipt_pack.jsonl` format | New receipt types added to stream | NO — additive |
| `pack_manifest.json` schema | `receipt_integrity` / `claim_check` axes preserved | NO — same contract |
| `pack_signature.sig` | Same Ed25519 signing | NO |
| CRS v0.1 receipt envelope | Episode receipts conform to CRS envelope | NO — additive types |
| AgentMesh `episode_id` format | Unchanged — referenced, not redefined | NO |
| AgentMesh `generate_episode_id()` | Unchanged — Assay imports or references, does not reimplement | NO |
| AgentMesh Event log | New `EventKind` values may be added for episode-replay events | NO — additive enum |
| AgentMesh CCOI envelope | `episode_spec_hash` can be added as an optional field | NO — additive |
| Gallery exit codes | 0/1/2 mapping preserved | NO |
| Verify Action | New `replay_mode` input — existing modes unchanged | NO |
| Ledger | Episode packs anchored via existing `pack_root_sha256` | NO |
| Loom proof tiers | RCE receipts map to existing C/B/A tiers | NO — consumption only |

---

## Appendix B: What This Proves and Does Not Prove

**v0 proves:**
- A second machine can independently verify that an episode's recorded outputs are consistent with its declared inputs, script, and evidence chain.
- Tampered evidence is mechanically detected (INTEGRITY_FAIL).
- Honest divergence (e.g., provider nondeterminism in recorded traces) is mechanically distinguished from tampering (DIVERGE vs INTEGRITY_FAIL).
- Episode receipts compile into existing proof packs without breaking the pack contract.

**v0 does NOT prove:**
- That live re-execution would produce the same result (that's `replay_basis: "live_reexecution"`).
- That semantically different outputs are actually equivalent (that's Tier C).
- That a quorum of verifiers agrees (that's `quorum_settlement.v0`).
- That the evidence is time-anchored to an external authority (that's T1 witness work).
- That the episode's objective was correctly achieved (that requires domain-specific claim validation).

---

## Appendix C: Deterministic Derivation Inventory

Every hash field in the RCE v0 receipt set, with exact inputs, canonicalization, ordering, and verifiability classification.

### Cross-verifiable hashes

A second implementation MUST produce identical values from the same Episode Contract, receipt set, and recorded traces.

| Field | Input object | Canonicalization | Ordering rule | Defined in |
|-------|-------------|-----------------|---------------|------------|
| `episode_spec_hash` | `{inputs, replay_script, replay_policy, replay_normative_environment}` | JCS (RFC 8785) → SHA-256 | JCS deterministic key sort | §2.1 |
| `env_fingerprint_hash` | `{provider, model_id, tool_versions, container_digest}` | JCS (RFC 8785) → SHA-256 | JCS deterministic key sort | §2.3 |
| `inputs_hash` | `episode_contract["inputs"]` (full array) | JCS (RFC 8785) → SHA-256 | Array order from contract | §2.4 |
| `script_hash` | `episode_contract["replay_script"]` (full object) | JCS (RFC 8785) → SHA-256 | JCS deterministic key sort | §2.4 |
| `outputs_hash` | Array of `{"step_id", "output_hash"}` per EMIT_OUTPUT step | JCS (RFC 8785) → SHA-256 | Lexicographic sort by `step_id` | §2.4 |
| `output_hash` (step) | Step output JSON (opcode-specific; see §2.4) | JCS (RFC 8785) → SHA-256 | Single object, no ordering ambiguity | §2.4 |
| `input_hashes` (step) | `output_hash` values from direct dependencies | None (array of pre-computed hashes) | `depends_on` declaration order | §2.4 |
| `expected_output_hash` | Original step receipt `output_hash` | Copied verbatim | N/A | §2.4 |
| `observed_output_hash` | Replayer's recomputed `output_hash` | Same derivation as step `output_hash` | N/A | §2.4 |
| `original_pack_root_sha256` | Original pack manifest attestation block | Pre-existing Assay pack contract | N/A | Pre-existing |
| `replay_pack_root_sha256` | Replayer's own pack manifest attestation block | Pre-existing Assay pack contract | N/A | §5.5 |
| `receipt_hash` | Full receipt object (minus `receipt_hash` itself) | CRS v0.1 envelope convention | N/A | Pre-existing |

### Local attestation hashes

Carried for audit provenance. A downstream consumer does NOT recompute these — the underlying source data is not exposed in the v0 receipt schema.

| Field | Input object | Canonicalization | Defined in | Why not cross-verifiable |
|-------|-------------|-----------------|------------|--------------------------|
| `config_hash` | Transform configuration (e.g., prompt template) | Implementation-defined (executor attestation) | §2.4 | Source config not carried in receipts or traces |
| `verifier_env_hash` | Verifier's own `{provider, model_id, tool_versions, container_digest}` | JCS (RFC 8785) → SHA-256 (same pattern as §2.3) | §2.4 | Full verifier env object not exposed in v0 receipt; only digest carried |
