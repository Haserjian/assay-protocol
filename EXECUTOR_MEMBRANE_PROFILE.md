# Assay Protocol — Executor Membrane Profile v0.1

**Status:** Draft companion to SPEC.md
**Version:** 0.1.0
**Date:** 2026-04-08
**Author:** Tim B. Haserjian
**Scope:** Public warrant contract for the boundary between policy reasoning and resource execution
**Grounded in:** Constitutional Receipt Standard (CRS) v0.1, RFC 8785 (JCS), RFC 8032 (Ed25519), RFC 2119

---

## Abstract

This profile defines the **Executor Membrane**: the public boundary at which a short-lived **Settlement Credential** is mechanically verified before any effect is produced against a protected resource.

The membrane exists to prevent execution on narrative authority alone. No transcript, reasoning prose, prior approval, or issuer assertion is sufficient. Effects require a credential whose execution-relevant claims are canonically encoded, cryptographically bound to the intended action, and locally verified at the executor.

This is a companion to [SPEC.md](./SPEC.md) and [RCE_PROFILE.md](./RCE_PROFILE.md), not a replacement. It defines a different seam: SPEC governs MCP gateway tool safety, RCE governs replay verification of work units, and this profile governs the conditions under which an executor may legitimately produce an effect.

> **The public artifact is the warrant contract — schema, semantics, reason codes, and conformance behavior. It is NOT any concrete executor.** Concrete executors and the issuers that mint warrants for them are intentionally out of scope here.

---

## 0. Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

### 0.1 Hash Encoding

All hash fields in this profile use bare lowercase hex (`^[a-f0-9]{64}$`). Verifiers MUST compare hashes as exact string equality. This differs from the RCE prefix convention by design: settlement credentials are minted by a private issuer surface and the verifier never accepts cross-format hashes.

### 0.2 Pinned Invariants

> **Tier 0 and Tier 1 prove bounded authorization integrity, not truth.**

This sentence is normative. It MUST appear verbatim in any conforming downstream specification that publishes membrane-tier claims. Independence of evidence, honesty of issuer reasoning, and corroboration by external witnesses are NOT established at these tiers and MUST NOT be implied by them.

### 0.3 Canonicalization

Settlement credentials are signed under [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) JSON Canonicalization Scheme (JCS). Issuers and verifiers MUST agree on the byte string under signature. Any divergence between issuer and verifier canonicalization will silently break signature verification.

> **The Python reference verifier in `reference/python_membrane/` ships with a prototype JCS approximation only. It is non-normative and MUST NOT be used in production until replaced with a fully RFC 8785-conformant canonicalizer.** This warning is repeated in the package README and in the verifier module docstring. Implementers building production verifiers MUST select a JCS-conformant canonicalizer and pin cross-language test vectors before deploying.

---

## 1. Terminology [Normative]

| Term | Definition |
|------|-----------|
| **Decision Receipt** | Durable record of policy reasoning and evidence assessment. Produced by the issuer. NOT presented to the executor. Out of scope for this profile. |
| **Settlement Credential** | Short-lived execution warrant derived from a Decision Receipt. Carries only execution-relevant claims. Defined by [`schemas/settlement_credential.schema.json`](./schemas/settlement_credential.schema.json). |
| **Executor Membrane** | The boundary at which warrants are mechanically verified before effects occur. Implemented by a verifier conforming to this profile. |
| **Verifier** | An implementation that consumes a Settlement Credential and an inbound request and emits `ACCEPT` or a structured refusal with a reason code from [`MEMBRANE_REASON_CODES.md`](./MEMBRANE_REASON_CODES.md). |
| **Independent Anchor** | A trust-bearing input not originating solely from the issuer's administrative boundary. Reserved for higher tiers. NOT verifiable at Tier 0 or Tier 1. |
| **Action Digest** | SHA-256 of the JCS-canonicalized inbound request payload envelope. The cryptographic binding between credential and effect. |
| **Proof Tier** | A claim a credential makes about what it proves. See §4. Reserved tiers (T2, T3) are declared in the schema but their verification semantics are out of scope here. |

These seven terms are normative. Implementers MUST NOT introduce synonyms in conforming documentation.

---

## 2. Trust Boundary [Normative]

```
  +---------------------------+   settlement   +---------------------------+
  | Issuer / Policy           |   credential   | Verifier / Executor       |
  | (private; deliberation)   | -------------> | (public; mechanical)      |
  | produces decision receipt |                | produces effect or refusal|
  +---------------------------+                +---------------------------+
```

The Settlement Credential is the only object that crosses the boundary. The Decision Receipt does NOT cross. The verifier MUST NOT parse, fetch, infer, or reconstruct issuer reasoning.

### 2.1 Issuer Responsibilities

The issuer is responsible for all cognitive work that precedes credential minting. The verifier does not see, validate, or replicate any of it. Issuer responsibilities include but are not limited to:

- policy lifecycle gating
- provenance gating (signer authority, trust tier, identity mode)
- attestation gating (corroboration required at the issuer's declared tier)
- evidence gating (integrity, claims, decision receipt presence)
- admissibility (action class, confidence floors, notional limits)
- velocity governance (rate limits, lockouts)
- obligation assignment
- canonical encoding of the credential under `canon_version`
- signing of the credential with a settlement authority key

Issuer internals are intentionally out of scope. This profile does not specify how the issuer reaches its decision.

### 2.2 Verifier Responsibilities

A conformant verifier MUST perform all of the following, in the order given, for every request. Steps 1 and 2 are jointly referred to as **Phase 1** in conformance and reason-code documentation, with their sub-step labels **1a** (version pinning) and **1b** (JSON Schema validation). Other documents in this profile MAY refer to "step 1a" / "phase 1a" and "step 1b" / "phase 1b" interchangeably with "step 1" and "step 2" here.

1. **Version pinning** (also known as **phase 1a**). `schema_version` and `canon_version` MUST match values supported by the verifier. This check runs first because it emits the most actionable refusal codes (`UNSUPPORTED_SCHEMA`, `UNSUPPORTED_CANON`) instead of being absorbed into a generic `MALFORMED` from the schema's `const` rules.
2. **JSON Schema validation** (also known as **phase 1b**) against `schemas/settlement_credential.schema.json`. The verifier MUST run a real Draft 2020-12 validator and MUST emit `MALFORMED` on any structural violation, including violations of `additionalProperties: false`, missing required fields, type errors, pattern failures, and the tier-conditional rules in §3.4 and §3.5.
3. **Tier recognition.** `proof_tier` MUST be a tier the verifier supports. A T0/T1 verifier MUST refuse `T2` or `T3` credentials.
4. **Anchor refusal at supported tiers.** At T0 and T1, `external_anchors` MUST be an empty array. A non-empty array at these tiers MUST be refused regardless of anchor origin or content. See §3.5.
5. **Self-binding.** `credential_id` MUST equal SHA-256 of the JCS-canonicalized credential with `signature` and `credential_id` removed.
6. **Signature scope and algorithm.** The `signature` block MUST declare a supported algorithm and the constant `signature_scope` defined by this profile.
7. **Trusted key resolution.** The verifier MUST resolve the signer public key via `(key_id, issuer.signer_pubkey_sha256)` from a trusted key store. The returned key bytes MUST hash to the asserted fingerprint.
8. **Signature verification** over the JCS-canonicalized credential with `signature` removed.
9. **Time window.** `issued_at < valid_until`, `issued_at ≤ now + skew`, `now < valid_until`. The verifier MAY apply a configured clock skew but MUST document it.
10. **Request binding.** `audience`, `executor_id`, `resource_uri`, `http_method`, and `action_digest` MUST each match the inbound request exactly. See §3.3.1 for the canonical envelope responsibility split on `action_digest`.
11. **Tier 1 extras.** At T1, `receipt_ref.decision_receipt_id` and `evidence_manifest_sha256` MUST be present and non-empty. (Schema validation in step 2 already enforces presence at T1 via §3.4; this step enforces non-emptiness as a defense-in-depth.)
12. **Replay defense.** `single_use_nonce` MUST be consumed atomically. This step MUST run last so that nonces are never burned on structural failures.

Only if all checks pass MAY the verifier return `ACCEPT`. Any failure MUST emit a structured refusal containing a single reason code from [`MEMBRANE_REASON_CODES.md`](./MEMBRANE_REASON_CODES.md).

#### 2.2.1 Earliest Detected Conformant Refusal

Several phases overlap by design: JSON Schema validation in step 2 already enforces some invariants (e.g., the tier-conditional rules in §3.4 and §3.5) that the verifier's explicit checks in steps 3, 4, and 11 also enforce as defense-in-depth. When multiple refusal conditions apply to the same credential, an implementation **MAY emit the earliest detected conformant reason code from the allowed overlap set for that violation**, as enumerated in [`conformance/executor_membrane.md`](./conformance/executor_membrane.md) §"Reason Code Overlap Matrix".

This carveout is intentionally finite. It exists to acknowledge that schema-first detection and explicit-check detection are both legitimate paths to the same refusal, NOT to permit reason-code drift. New overlaps require an entry in the matrix; an implementation MUST NOT introduce new overlap cases without specification.

What is NOT permitted under this clause:

- silent acceptance of a credential that any phase would refuse
- coercion of an unknown reason code into an existing one
- emitting a refusal code outside the allowed overlap set for that violation
- expanding the overlap set without amending the matrix in a profile revision

### 2.3 What the Verifier Must Not Trust

A conformant verifier MUST NOT:

- parse, interpret, or load the Decision Receipt
- fetch policy context, attestations, or anchors at execution time
- recompute or second-guess issuer policy decisions
- accept a credential because the issuer "looked correct" without signature verification
- upgrade trust based on the presence, content, or signer of any anchor at T0/T1
- retry, fall back, or escalate on its own behalf past the nonce commit
- treat unknown or reserved proof tiers as equivalent to a known tier
- treat unknown top-level fields as benign — `additionalProperties: false` is normative

---

## 3. Settlement Credential [Normative]

The wire format is defined by [`schemas/settlement_credential.schema.json`](./schemas/settlement_credential.schema.json). This section defines field semantics and required derivations.

### 3.1 Identity Fields

| Field | Semantics |
|-------|-----------|
| `credential_id` | SHA-256 of the JCS-canonicalized credential with `signature` and `credential_id` removed. The verifier MUST recompute this and reject on mismatch. |
| `schema_version` | Pinned to `"0.1.0"` for this profile. |
| `canon_version` | Pinned to `"jcs-rfc8785"` for this profile. |
| `issuer.authority_id` | Free-form issuer identifier. Audit field. NOT authoritative. |
| `issuer.signer_pubkey_sha256` | SHA-256 fingerprint of the Ed25519 public key. Authoritative for signer identity. |
| `issuer.trust_tier` | Issuer's declared trust tier. Audit field at T0/T1. The verifier MAY use it to refuse below a configured floor but MUST NOT use it to upgrade. |
| `key_id` | Verifier key selection hint. NOT authoritative — the fingerprint is. |

### 3.2 Time Fields

| Field | Semantics |
|-------|-----------|
| `issued_at` | RFC 3339 UTC timestamp at which the issuer minted the credential. |
| `valid_until` | RFC 3339 UTC timestamp at which the credential expires. MUST be strictly greater than `issued_at`. The verifier MUST refuse credentials whose validity window exceeds local policy. |
| `single_use_nonce` | Opaque random token of at least 16 characters. Consumed atomically by the verifier. The store MUST retain consumed nonces for at least the duration of `valid_until + skew`. |

### 3.3 Binding Fields

| Field | Semantics |
|-------|-----------|
| `audience` | Intended verifying domain. Prevents cross-audience replay. |
| `executor_id` | The exact executor identity authorized to act. |
| `subject` | Acting principal. Audit field. NOT authoritative for routing. |
| `purpose` | Short audit tag. Non-authoritative. |
| `resource_uri` | The exact path the credential authorizes, beginning with `/`. |
| `http_method` | One of `GET`, `POST`, `PUT`, `PATCH`, `DELETE`. |
| `action_digest` | SHA-256 of the canonical envelope of the inbound request payload (see §3.3.1). The verifier MUST compare this against the digest carried in the inbound request structure and reject on mismatch. |

#### 3.3.1 Canonical Request Envelope

The verifier compares `action_digest` from the credential against a digest carried in the inbound request structure. **The embedding layer is responsible for computing that digest from the actual inbound payload using the canonical envelope defined here.** The verifier itself does NOT access raw request bytes, and a v0.1 verifier MUST NOT be presumed to have validated the embedding layer's canonicalization.

This split is intentional. It keeps the verifier narrow and deterministic, and it makes the canonicalization responsibility legible at the boundary instead of hidden inside the verifier.

For JSON payloads, the canonical envelope is:

```
action_digest = sha256_hex( jcs_canonicalize( payload ) )
```

where `payload` is the structured request body and `jcs_canonicalize` is [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) JSON Canonicalization Scheme. A reference implementation of this envelope is exported as `compute_action_digest` from the membrane reference package; the embedding layer MAY use it directly or substitute an equivalent canonical envelope.

For non-JSON payloads, the canonical envelope is OUT OF SCOPE for v0.1. A future profile version may either define additional envelopes or move digest computation inside the verifier.

> **What the membrane proves:** the credential is bound to a specific `action_digest`, and the embedding layer asserts that the inbound bytes hash to that digest under the canonical envelope.
>
> **What the membrane does NOT prove at v0.1:**
>
> - that the embedding layer applied the canonical envelope correctly
> - that the digest carried in the inbound request structure was computed from the original raw bytes
> - **byte-identity between the original inbound request and any later representation of it**
>
> A matching `action_digest` demonstrates equivalence under the canonicalization contract. It does NOT demonstrate that the bytes the verifier saw downstream are the same bytes a client sent upstream. Downstream consumers MUST NOT smuggle stronger claims (e.g., "the original payload was X" or "the request was tamper-evident end-to-end") on top of a successful verification. Conformance for the embedding layer — including how it acquires raw bytes, normalizes them, and computes the digest — is OUT OF SCOPE for this profile.

### 3.4 Tier-Conditional Fields

`receipt_ref` and `evidence_manifest_sha256` are mandatory ONLY at Tier 1.

| Field | T0 | T1 |
|-------|:--:|:--:|
| `receipt_ref` | Optional (MAY be absent or set to a Tier 0 audit value) | **Required**, with non-empty `decision_receipt_id` |
| `evidence_manifest_sha256` | Optional | **Required** |

The schema enforces this conditionally: a credential declaring `proof_tier: "T1"` that omits either field MUST fail JSON Schema validation. A T0 credential MAY carry these fields, but the verifier does not enforce their presence at T0.

### 3.5 Anchors

| Field | Semantics |
|-------|-----------|
| `external_anchors` | Array of references to independent anchors. **At T0 and T1 this array MUST be empty.** The verifier MUST refuse any non-empty value at these tiers, regardless of `anchor_type`, `anchor_id`, or signer. The field is reserved so credentials can carry anchors when higher-tier verifiers are introduced; it does not grant trust at this tier. |

The reason this is a hard refusal rather than a silent skip: a verifier that quietly ignores anchors will eventually be assumed by some downstream consumer to have validated them. Refusing at the schema boundary makes the missing semantics observable.

### 3.6 Risk Budget and Obligations

| Field | Semantics |
|-------|-----------|
| `risk_budget` | Issuer-asserted bound on the action (`units`, `magnitude`, `scope`). Audit and forensic field at T0/T1. The verifier MAY enforce a local ceiling but MUST NOT relax issuer values. |
| `obligations.post_execution.require_receipt` | Issuer assertion that a post-execution receipt MUST be emitted. Receipt emission is the executor's responsibility, not the verifier's. |
| `obligations.post_execution.require_ledger_anchor` | Issuer assertion that the post-execution receipt MUST be ledger-anchored. |
| `obligations.post_execution.deadline_seconds` | Maximum time after `valid_until` within which the obligation MUST be fulfilled. |

The verifier emits `ACCEPT` solely on the basis of the verification algorithm in §2.2. Obligations are forwarded to the executor; the verifier does not enforce them.

### 3.7 Signature

| Field | Semantics |
|-------|-----------|
| `signature.algorithm` | `"Ed25519"` in v0.1. No algorithm agility. |
| `signature.signature_scope` | Pinned to `"jcs_rfc8785_without_signature"` in v0.1. |
| `signature.value` | Base64 Ed25519 signature over `JCS(credential)` with `signature` removed and `credential_id` present. |

---

## 4. Tier Model [Normative]

Proof tiers describe what a credential's claims prove. They do NOT describe how much effort the issuer expended.

| Tier | Name | Status in v0.1 |
|------|------|----------------|
| **T0** | Bounded authorization integrity | **Supported** |
| **T1** | T0 + local replay protection + receipt/evidence anchoring | **Supported** |
| **T2** | T1 + external time or transparency anchoring | **Reserved** |
| **T3** | T2 + runtime attestation or dual-control witness | **Reserved** |

A T0/T1 verifier MUST refuse `T2` and `T3` credentials with `UNSUPPORTED_TIER`. A future profile may introduce verifier semantics for the reserved tiers; this profile does not.

### 4.1 What Tier 0 Proves

- The credential came from a trusted settlement authority key.
- The credential bytes were not mutated after signing.
- The credential is within its validity window.
- The credential is bound to this exact audience, executor, resource, method, and payload.
- The credential has not been replayed.

### 4.2 What Tier 0 Does Not Prove

- That the issuer's evidence was genuine.
- That the issuer's clock was honest.
- That the issuer's reasoning was sound.
- That any independent party corroborates the issuer's claims.
- That the world state at execution time matches the world state at decision time.

> **Tier 0 and Tier 1 prove bounded authorization integrity, not truth.**

### 4.3 Tier 1 Additions

Tier 1 adds, on top of Tier 0:

- mandatory `receipt_ref.decision_receipt_id`
- mandatory `evidence_manifest_sha256`
- a nonce store with durable consume semantics (an in-memory set is acceptable for testing only)
- explicit refusal on missing or empty `receipt_ref.decision_receipt_id`

Tier 1 still proves only bounded authorization integrity. The additional fields make after-the-fact forensic joins possible. They do not establish independent truth.

### 4.4 Reserved Tiers

The following mechanisms are declared but out of scope for v0.1:

- external time anchoring (RFC 3161 or equivalent)
- transparency log inclusion (SCITT-style)
- remote runtime attestation (RATS)
- dual-control human witness
- online introspection or revocation

Conforming verifiers MUST refuse reserved tiers rather than partially implementing them.

---

## 5. Reason Codes [Normative]

Every refusal MUST emit exactly one reason code from [`MEMBRANE_REASON_CODES.md`](./MEMBRANE_REASON_CODES.md). The reason-code surface for this profile is intentionally separate from the gateway reason codes in [`REASON_CODES.md`](./REASON_CODES.md) to prevent collision and to make the membrane contract independently versionable.

---

## 6. Conformance [Normative]

Conformance behavior, test IDs, and required adversarial cases are defined in [`conformance/executor_membrane.md`](./conformance/executor_membrane.md). Every MUST and MUST NOT in this profile maps to at least one conformance test.

A reference implementation lives at [`reference/python_membrane/`](./reference/python_membrane/). It is **non-normative** and **prototype-only**. See its README for the full warning.

---

## 7. Compatibility [Informative]

| Existing Surface | Membrane Impact | Breaking? |
|-----------------|-----------------|:---------:|
| `REASON_CODES.md` | Untouched. Membrane reason codes live in a separate file. | No |
| `SPEC.md` | Untouched. The membrane is a different boundary from MCP gateway tool safety. | No |
| `RCE_PROFILE.md` | Untouched. RCE governs replay; the membrane governs effect authorization. | No |
| Reference gateway | Untouched. The membrane reference is a sibling package. | No |
| Makefile | Adds membrane-specific targets. Existing gateway targets preserved. | No |

---

## 8. Scope Boundaries [Informative]

### 8.1 In Scope for v0.1

- Settlement credential schema (Tier 0 / Tier 1)
- Verifier algorithm contract
- Reason-code surface
- Conformance behavior with adversarial test matrix
- Non-normative Python reference verifier

### 8.2 Explicitly Out of Scope

- Concrete executor implementations
- Issuer implementations
- Decision receipt format
- Policy card format
- Provenance and attestation evaluation
- Trust store implementations
- Key rotation, compromise, or retirement protocols
- Tier 2 and Tier 3 verification semantics
- Online revocation or introspection
- Sender constraint mechanisms (DPoP-style)
- TOCTOU precondition binding
- Velocity / rate-limit governance
- Production-grade JCS canonicalization

---

## 9. Open Questions [Informative]

Tracked, not blocking. None of these affect Tier 0 / Tier 1 conformance.

1. Revocation before expiry: status list, online introspection, or both?
2. Authoritative clock model and external time anchor threshold.
3. Sender constraint at higher tiers (bearer vs. key-bound).
4. Nonce store semantics across clustered verifiers and retries.
5. TOCTOU preconditions encoded in the credential.
6. Per-tier degraded-mode policy.
7. Obligation enforcement protocol.
8. Normative definition of "independent" for T2+ anchors.
9. Key lifecycle and algorithm agility.
10. Cross-language JCS test vectors.

---

## 10. Relationship to Other Documents

| This Document | Other Document |
|---------------|---------------|
| Settlement credential schema and verifier contract | [SPEC.md](./SPEC.md) — MCP gateway tool safety enforcement |
| Effect authorization boundary | [RCE_PROFILE.md](./RCE_PROFILE.md) — replay verification of work units |
| Reason-code surface | [REASON_CODES.md](./REASON_CODES.md) — gateway reason codes (separate surface) |
| Receipt envelope (informative) | [CRS v0.1](./CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md) — receipt format |

A system that issues settlement credentials for MCP tool calls SHOULD satisfy this profile, the MCP Minimum Profile, and the Constitutional Receipt Standard. A system that uses this membrane to gate effects on replay-verified episodes SHOULD also satisfy the RCE Profile.

---

*Assay Protocol — Executor Membrane Profile v0.1*
*Companion to SPEC.md v1.0.0-rc1 and RCE_PROFILE.md v0.1*
