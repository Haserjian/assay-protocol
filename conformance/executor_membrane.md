# Executor Membrane Conformance

How to verify that an implementation of the [Executor Membrane Profile](../EXECUTOR_MEMBRANE_PROFILE.md) conforms to v0.1.

This file is a flat peer of [`README.md`](./README.md) (gateway conformance). The two surfaces share no test IDs and no reason codes. Membrane reason codes live in [`MEMBRANE_REASON_CODES.md`](../MEMBRANE_REASON_CODES.md).

## Quick Check

Run the membrane reference tests against your implementation:

```bash
cd reference/python_membrane
pip install -e ".[dev]"
pytest tests/test_credential_verifier.py -v
```

Or from the repo root:

```bash
make membrane-install
make membrane-test
```

## Required Tests

A conforming verifier MUST pass every test in this matrix. Each test maps to one or more MUST/MUST NOT clauses in [`EXECUTOR_MEMBRANE_PROFILE.md`](../EXECUTOR_MEMBRANE_PROFILE.md) §2.2 / §2.3 / §3 / §4.

| Category | Test IDs | Required |
|----------|----------|---------:|
| Acceptance | MEMB-ACC-01, MEMB-ACC-02, MEMB-ACC-03 | 3 |
| Schema and Version | MEMB-SCH-01, MEMB-SCH-02, MEMB-SCH-03 | 3 |
| Tier and Anchors | MEMB-TIER-01, MEMB-TIER-02, MEMB-TIER-03 | 3 |
| Signature and Self-Binding | MEMB-SIG-01, MEMB-SIG-02, MEMB-SIG-03, MEMB-SIG-04 | 4 |
| Time Window | MEMB-TIME-01, MEMB-TIME-02 | 2 |
| Request Binding | MEMB-BIND-01, MEMB-BIND-02, MEMB-BIND-03, MEMB-BIND-04, MEMB-BIND-05 | 5 |
| Tier 1 Extras | MEMB-T1-01, MEMB-T1-02 | 2 |
| Replay | MEMB-REPLAY-01, MEMB-REPLAY-02 | 2 |

## Test Descriptions

### MEMB-ACC-01: Valid T0 credential accepted
A well-formed Tier 0 credential whose signature, time window, request bindings, and nonce are all valid MUST verify successfully and return reason code `ACCEPT`.

**Maps to:** Profile §2.2 (full verification order). **Reason code:** `ACCEPT`.

### MEMB-ACC-02: Valid T1 credential accepted
A well-formed Tier 1 credential with non-empty `receipt_ref.decision_receipt_id` and `evidence_manifest_sha256` MUST verify successfully.

**Maps to:** Profile §2.2 step 11, §4.3. **Reason code:** `ACCEPT`.

### MEMB-ACC-03: Lean T0 credential without optional T1 fields accepted
A well-formed Tier 0 credential that omits both `receipt_ref` and `evidence_manifest_sha256` entirely MUST verify successfully. This test exists because the schema makes those fields tier-conditional (§3.4): they are required only at T1 and OPTIONAL at T0. A verifier or validator that always demands them would silently collapse the tier distinction.

**Maps to:** Profile §3.4, §4.3. **Reason code:** `ACCEPT`.

### MEMB-SCH-01: Unsupported schema version refused
A credential with `schema_version` other than `"0.1.0"` MUST be refused with `UNSUPPORTED_SCHEMA`.

**Maps to:** Profile §2.2 step 1 (phase 1a, version pinning).

### MEMB-SCH-02: Unsupported canonicalization version refused
A credential with `canon_version` other than `"jcs-rfc8785"` MUST be refused with `UNSUPPORTED_CANON`.

**Maps to:** Profile §2.2 step 1 (phase 1a, version pinning).

### MEMB-SCH-03: JSON Schema validation failure refused
A credential that violates the JSON Schema in any way OTHER than version mismatch (e.g., missing a required field, type error, `additionalProperties: false` violation, pattern failure, or violation of a tier-conditional rule from §3.4 or §3.5) MUST be refused with `MALFORMED`. This test confirms the verifier actually runs JSON Schema validation as phase 1b, not just version pinning.

**Maps to:** Profile §2.2 step 2 (phase 1b, JSON Schema validation).

### MEMB-TIER-01: Reserved tier refused
A credential with `proof_tier` of `"T2"` or `"T3"` MUST be refused with `UNSUPPORTED_TIER`. T2 and T3 are valid values in the schema enum, so JSON Schema validation passes; the explicit phase 3 tier check rejects them. The verifier MUST NOT partially honor the credential.

**Maps to:** Profile §2.2 step 3, §4.4. **Reason code:** `UNSUPPORTED_TIER`.

### MEMB-TIER-02: Unknown tier refused
A credential with a `proof_tier` value outside the schema enum (e.g., `"T9"`) MUST be refused. The schema enum on `proof_tier` catches this at phase 1b with `MALFORMED`. The verifier's explicit phase 3 fall-through would emit `UNSUPPORTED_TIER` if schema validation were bypassed. Either reason code is conformant; what matters is that unknown tiers MUST NOT be silently accepted or coerced.

**Maps to:** Profile §2.2 steps 1b and 3. **Reason codes:** `MALFORMED` or `UNSUPPORTED_TIER`.

### MEMB-TIER-03: Self-referential anchors do not upgrade trust
A structurally valid Tier 0 or Tier 1 credential carrying any non-empty `external_anchors` array MUST be refused. **The refusal MUST occur regardless of `anchor_type`, `anchor_id`, signer, or whether the anchors appear well-formed.** This test exists because a verifier that silently ignores anchors will eventually be assumed by some downstream consumer to have validated them. Independence cannot be mechanically established at T0/T1, so anchors acquire no trust and MUST be refused at the schema boundary.

The schema's allOf if/then rule for T0/T1 (§3.5) enforces `external_anchors maxItems: 0`, so JSON Schema validation (phase 1b) catches this with `MALFORMED`. The verifier's explicit phase 2 anchor check is kept as defense-in-depth and would emit `ANCHORS_NOT_ALLOWED_AT_TIER` if schema validation were bypassed. Either reason code is conformant; what is NOT conformant is allowing the credential through at T0/T1.

**Maps to:** Profile §2.2 steps 1b and 4, §3.5, §4.2. **Reason codes:** `MALFORMED` or `ANCHORS_NOT_ALLOWED_AT_TIER`. **This is the load-bearing invariant of the v0.1 contract.**

### MEMB-SIG-01: Mutated payload refused
A credential whose body is mutated after signing MUST be refused. The earliest detection point is `CREDENTIAL_ID_MISMATCH`. A verifier that recomputes `credential_id` correctly will refuse there.

**Maps to:** Profile §2.2 step 5.

### MEMB-SIG-02: Recomputed credential_id with invalid signature refused
A credential whose body is mutated AND whose `credential_id` is recomputed to match the mutated body MUST still be refused with `BAD_SIGNATURE`. This test confirms the signature is over canonicalized bytes that include `credential_id`, so recomputing the id cannot rescue a mutated payload.

**Maps to:** Profile §2.2 step 8. **This test is required to detect canonicalizer drift between issuer and verifier.**

### MEMB-SIG-03: Untrusted key refused
A credential whose `(key_id, signer_pubkey_sha256)` pair is not in the trusted key store MUST be refused with `UNTRUSTED_KEY`.

**Maps to:** Profile §2.2 step 7.

### MEMB-SIG-04: Trusted key with wrong fingerprint refused
A credential whose trusted key bytes do not hash to the asserted `signer_pubkey_sha256` MUST be refused with `KEY_FINGERPRINT_MISMATCH`. This indicates a trust store integrity violation.

**Maps to:** Profile §2.2 step 7.

### MEMB-TIME-01: Expired credential refused
A credential where `now >= valid_until` MUST be refused with `EXPIRED`. The verifier MUST NOT extend, retry, or escalate.

**Maps to:** Profile §2.2 step 9.

### MEMB-TIME-02: Not-yet-valid credential refused
A credential where `now + skew < issued_at` MUST be refused with `NOT_YET_VALID`.

**Maps to:** Profile §2.2 step 9.

### MEMB-BIND-01: Wrong audience refused
A credential whose `audience` does not match the verifier's audience MUST be refused with `AUDIENCE_MISMATCH`.

**Maps to:** Profile §2.2 step 10.

### MEMB-BIND-02: Wrong executor_id refused
A credential whose `executor_id` does not match this executor MUST be refused with `EXECUTOR_MISMATCH`.

**Maps to:** Profile §2.2 step 10.

### MEMB-BIND-03: Wrong resource_uri refused
A credential whose `resource_uri` does not match the inbound request path MUST be refused with `RESOURCE_MISMATCH`. This test guards against confused-deputy attacks.

**Maps to:** Profile §2.2 step 10.

### MEMB-BIND-04: Wrong http_method refused
A credential whose `http_method` does not match the inbound request method MUST be refused with `METHOD_MISMATCH`.

**Maps to:** Profile §2.2 step 10.

### MEMB-BIND-05: Action digest mismatch refused
A credential whose `action_digest` does not match the digest carried in the inbound request structure MUST be refused with `ACTION_DIGEST_MISMATCH`. The verifier compares string equality between `credential.action_digest` and `InboundRequest.payload_digest`. **The embedding layer is responsible for computing `payload_digest` from the actual inbound bytes using the canonical envelope defined in profile §3.3.1.** A reference implementation of that envelope is exported as `compute_action_digest` from the membrane reference package.

**Maps to:** Profile §2.2 step 10, §3.3.1.

### MEMB-T1-01: T1 without receipt_ref refused
A Tier 1 credential whose receipt-ref binding obligation is unsatisfied MUST be refused. "Unsatisfied" covers three conditions: (a) `receipt_ref` absent, (b) `receipt_ref` present but not an object, OR (c) `receipt_ref.decision_receipt_id` missing or empty. **The schema validator (phase 1b) catches all three** — (a) via the §3.4 tier-conditional `required`, (b) via the `receipt_ref` property `type: object` constraint, and (c) via the inner `required` and `minLength: 1`. The verifier's explicit phase 11 composite check also catches all three and emits `T1_MISSING_RECEIPT_REF` (the name is intentionally narrower than the scope; see the note under the Reason Code Overlap Matrix). At T1 the explicit check is fully redundant with the schema and is kept as defense-in-depth. Either reason code is conformant.

**Maps to:** Profile §2.2 step 11, §3.4, §4.3.

### MEMB-T1-02: T1 without evidence_manifest_sha256 refused
A Tier 1 credential lacking `evidence_manifest_sha256` MUST be refused. As with MEMB-T1-01, the schema validator refuses with `MALFORMED` for an absent field; the explicit T1 check refuses with `T1_MISSING_EVIDENCE_MANIFEST` for an empty value. Either is conformant.

**Maps to:** Profile §2.2 step 11, §3.4, §4.3.

### MEMB-REPLAY-01: Nonce replay refused
A credential whose `single_use_nonce` has already been consumed MUST be refused with `REPLAY_DETECTED`.

**Maps to:** Profile §2.2 step 12.

### MEMB-REPLAY-02: Nonce not consumed on structural failure
A credential that fails any check before the nonce step (for example, wrong `executor_id`) MUST NOT cause its nonce to be consumed. The same nonce MUST remain fresh for a subsequent legitimate verification. This test prevents adversaries from burning legitimate nonces by submitting structurally invalid credentials.

**Maps to:** Profile §2.2 step 12 ordering requirement.

## Reason Code Overlap Matrix

Some violations are reachable from multiple phases of the verification algorithm. JSON Schema validation in phase 1b is intentionally strict enough to catch several invariants that the verifier's explicit checks in later phases also enforce as defense-in-depth. The table below is the **complete** list of overlap cases permitted under profile §2.2.1. An implementation MAY emit any reason code listed in the "Allowed reason codes" column for that violation. An implementation MUST NOT emit a code outside that set, and MUST NOT introduce new overlap cases without amending this table in a profile revision.

| Violation kind | Earliest expected phase | Allowed reason codes | Overlap intentional? |
|---|---|---|---|
| `proof_tier` outside schema enum (e.g., `"T9"`) | 1b (JSON Schema enum) | `MALFORMED`, `UNSUPPORTED_TIER` | yes — schema enum and explicit fall-through |
| `proof_tier` reserved (`"T2"`, `"T3"`) | 3 (explicit tier check) | `UNSUPPORTED_TIER` | no — schema accepts these values |
| Non-empty `external_anchors` at T0/T1 | 1b (JSON Schema `maxItems: 0` conditional) | `MALFORMED`, `ANCHORS_NOT_ALLOWED_AT_TIER` | yes — schema conditional and explicit anchor check |
| T1 missing `receipt_ref` (field absent) | 1b (JSON Schema tier-conditional `required`) | `MALFORMED` | no — schema is the only path |
| T1 missing `evidence_manifest_sha256` (field absent) | 1b (JSON Schema tier-conditional `required`) | `MALFORMED` | no — schema is the only path |
| T1 with `receipt_ref` invalid in any of three composite ways: (a) absent, (b) present but not an object, OR (c) `decision_receipt_id` missing or empty | 1b (JSON Schema: tier-conditional `required` for (a); `type: object` for (b); inner `required` + `minLength: 1` for (c)) | `MALFORMED`, `T1_MISSING_RECEIPT_REF` | yes — schema constraint family and explicit T1 composite check |
| Top-level field violating `additionalProperties: false` | 1b (JSON Schema) | `MALFORMED` | no — schema is the only path |
| Missing top-level required field (other than tier-conditional ones above) | 1b (JSON Schema `required`) | `MALFORMED` | no — schema is the only path |
| Wrong `schema_version` | 1a (explicit version pin) | `UNSUPPORTED_SCHEMA` | no — explicit pin runs before schema validation |
| Wrong `canon_version` | 1a (explicit version pin) | `UNSUPPORTED_CANON` | no — explicit pin runs before schema validation |

**Note on `T1_MISSING_RECEIPT_REF`.** Despite its literal name, this reason code is emitted by a composite phase 11 check that catches three conditions: (a) `receipt_ref` field absent, (b) `receipt_ref` present but not an object, OR (c) `receipt_ref.decision_receipt_id` missing or empty. **All three conditions are also caught at phase 1b as `MALFORMED`** via three distinct schema constraints — (a) by the §3.4 tier-conditional `required`, (b) by the `receipt_ref` property `type: object` constraint, and (c) by the inner `required` and `minLength: 1`. The verifier's explicit phase 11 check is therefore fully redundant with the schema at T1 and is retained solely as defense-in-depth (e.g., for an embedding that bypasses the schema validator). At T0 the explicit check is not executed at all, so (b) and (c) at T0 are caught only by the schema and emit only `MALFORMED` (they are NOT overlap cases and do not appear in the table). The reason code's name is held narrower than its scope to keep the v0.1 reason-code surface stable; future versions MAY rename it to `T1_RECEIPT_REF_INVALID` or split it into per-condition codes, but such a change requires a profile version bump.

Rules for amending the matrix:

1. New overlap entries require a profile version bump.
2. Removing an allowed reason code from an existing overlap entry is a breaking change.
3. Adding a new violation kind that is not currently checkable by phase 1b is NOT an overlap entry; it is a normal single-code refusal and lives in [`MEMBRANE_REASON_CODES.md`](../MEMBRANE_REASON_CODES.md).
4. An implementation that finds a violation reachable from multiple phases but NOT listed here MUST treat the schema-detected code as authoritative until the matrix is amended.
5. Renaming or splitting any reason code listed in this matrix or in [`MEMBRANE_REASON_CODES.md`](../MEMBRANE_REASON_CODES.md) is a breaking change requiring a profile version bump.
6. **A defense-in-depth explicit check listed here MUST NOT be removed solely because it is redundant with the schema.** Such checks exist to preserve the stable public refusal taxonomy and to protect embeddings that bypass schema validation. Removal of any explicit check that participates in an overlap entry requires a profile version bump.

## Adversarial Notes

Two tests in this matrix are not optional and not "polish":

- **MEMB-TIER-03** is the Moth invariant. A verifier that does not refuse anchors at T0/T1 silently turns the membrane into theater. This test MUST pass.
- **MEMB-SIG-02** detects canonicalizer drift. A verifier that passes MEMB-SIG-01 but fails MEMB-SIG-02 has a canonicalizer that does not produce the same bytes as the issuer for credentials whose `credential_id` has been recomputed. This test MUST pass.

## Cross-Language JCS Vectors

A future version of this conformance suite SHOULD include cross-language JCS test vectors so that issuer and verifier implementations in different languages can be checked against the same canonical form. The reference Python verifier ships with a placeholder test marked `pytest.mark.skip(reason="requires conformant RFC 8785 JCS implementation")`. Production verifiers MUST replace the prototype canonicalizer before relying on those vectors.

## Claiming Conformance

To claim Executor Membrane Profile v0.1 conformance:

1. Run all required tests in this matrix.
2. Document the JCS canonicalizer in use and confirm it is RFC 8785-conformant. The reference Python `jcs_canonicalize` is **not** conformant and MUST NOT be used in production.
3. Document your trusted key store implementation, nonce store durability guarantees, and clock skew configuration.
4. Generate a conformance report:

```bash
cd reference/python_membrane
pytest tests/test_credential_verifier.py -v --tb=short > membrane_conformance_report.txt
```

Include in your documentation:

- Profile version: `0.1.0`
- Schema version: `0.1.0`
- Canon version: `jcs-rfc8785`
- Test date and commit hash
- JCS canonicalizer name and version
- Any deferred tests (T1 may be deferred if you only support T0; mark explicitly)
