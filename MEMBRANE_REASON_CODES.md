# Executor Membrane Reason Codes

Canonical reason codes for the [Executor Membrane Profile](./EXECUTOR_MEMBRANE_PROFILE.md). Every conforming verifier MUST emit exactly one of these codes on refusal, and every conformance test asserts against this surface.

This file is intentionally separate from [`REASON_CODES.md`](./REASON_CODES.md) (gateway reason codes). The membrane is a different boundary and its codes are versioned independently.

## Acceptance

| Code | Description |
|------|-------------|
| `ACCEPT` | Credential verified. All checks in §2.2 of the profile passed. The verifier MAY now release the request to the executor. |

## Refusal Codes

Refusal codes are partitioned by the verification phase that emits them. A conformant verifier MUST evaluate phases in the order given by §2.2 of the profile and MUST emit the code from the **earliest** phase that fails. Subsequent phases MUST NOT execute on failure.

### Phase 1 — Schema and Version

The verifier runs version pinning before JSON Schema validation so that mismatched versions emit specific reason codes instead of being absorbed into a generic `MALFORMED` from the schema's `const` rules.

| Code | Severity | Description | Operator Action |
|------|----------|-------------|-----------------|
| `UNSUPPORTED_SCHEMA` | high | `schema_version` is not a value the verifier supports. Emitted before JSON Schema validation. | Upgrade verifier or downgrade issuer. |
| `UNSUPPORTED_CANON` | high | `canon_version` is not a value the verifier supports. Emitted before JSON Schema validation. | Upgrade verifier or downgrade issuer. |
| `MALFORMED` | high | Credential is not a JSON object, fails JSON Schema validation against `schemas/settlement_credential.schema.json`, or violates a tier-conditional rule (e.g., a T1 credential missing `receipt_ref` or `evidence_manifest_sha256`). The `detail` field MUST cite the violating JSON Pointer path when available. | Fix issuer serialization or honor the tier-conditional schema. |

### Phase 2 — Tier and Anchors

| Code | Severity | Description | Operator Action |
|------|----------|-------------|-----------------|
| `UNSUPPORTED_TIER` | high | `proof_tier` is reserved (`T2`, `T3`) or unrecognized. | Reissue at a supported tier or upgrade verifier. |
| `ANCHORS_NOT_ALLOWED_AT_TIER` | high | `external_anchors` is non-empty at T0 or T1. **This is a hard refusal regardless of anchor origin or content.** | Remove anchors from the issued credential, or use a verifier that supports the corresponding higher tier. |

### Phase 3 — Self-Binding and Signature

| Code | Severity | Description | Operator Action |
|------|----------|-------------|-----------------|
| `CANONICALIZATION_FAILED` | critical | Canonicalization of the credential bytes failed. | Investigate canonicalizer divergence between issuer and verifier. |
| `CREDENTIAL_ID_MISMATCH` | critical | Recomputed `credential_id` does not match the asserted value. | Possible mutation in flight or canonicalizer drift. |
| `UNSUPPORTED_ALG` | critical | `signature.algorithm` is not a value the verifier supports. | Reissue with a supported algorithm. |
| `UNSUPPORTED_SCOPE` | critical | `signature.signature_scope` is not the constant required by this profile. | Reissue with the correct scope. |
| `UNTRUSTED_KEY` | critical | The trusted key store has no entry for `(key_id, signer_pubkey_sha256)`. | Provision the issuer key in the trust store, or revoke. |
| `KEY_FINGERPRINT_MISMATCH` | critical | Trusted key bytes do not hash to the asserted fingerprint. | Trust store integrity violation — investigate immediately. |
| `MALFORMED_SIGNATURE` | critical | Signature value is missing, malformed, or unparseable. | Fix issuer signing path. |
| `BAD_SIGNATURE` | critical | Signature did not verify under the resolved trusted key. | Possible mutation, key compromise, or canonicalizer drift. |

### Phase 4 — Time Window

| Code | Severity | Description | Operator Action |
|------|----------|-------------|-----------------|
| `MALFORMED_TIME` | high | `issued_at` or `valid_until` is missing or unparseable. | Fix issuer time serialization. |
| `INVERTED_WINDOW` | high | `issued_at >= valid_until`. | Fix issuer validity computation. |
| `NOT_YET_VALID` | medium | `now + skew < issued_at`. | Check executor clock or wait. |
| `EXPIRED` | medium | `now >= valid_until`. | Reissue. Do not extend. |

### Phase 5 — Request Binding

| Code | Severity | Description | Operator Action |
|------|----------|-------------|-----------------|
| `AUDIENCE_MISMATCH` | high | Credential `audience` does not match this verifier's audience. | Routing error — credential intended for a different verifier. |
| `EXECUTOR_MISMATCH` | high | Credential `executor_id` does not match this executor. | Routing error — credential intended for a different executor. |
| `RESOURCE_MISMATCH` | high | Credential `resource_uri` does not match the inbound request path. | Confused-deputy attempt or client error. |
| `METHOD_MISMATCH` | high | Credential `http_method` does not match the inbound request method. | Confused-deputy attempt or client error. |
| `ACTION_DIGEST_MISMATCH` | critical | Credential `action_digest` does not match the recomputed hash of the inbound payload. | Possible payload tampering after issuance. |

### Phase 6 — Tier 1 Extras

| Code | Severity | Description | Operator Action |
|------|----------|-------------|-----------------|
| `T1_MISSING_RECEIPT_REF` | high | The receipt-ref binding obligation is unsatisfied at T1. **The name is intentionally narrower than the scope:** this code covers `receipt_ref` absent, `receipt_ref` present but not an object, OR `receipt_ref.decision_receipt_id` missing or empty. **All three conditions are also caught at phase 1b as `MALFORMED`** — by the §3.4 tier-conditional `required`, the `receipt_ref` property `type: object` constraint, and the inner `required` + `minLength: 1` respectively. The verifier's explicit phase 11 composite check is therefore fully redundant with the schema at T1 and is retained solely as defense-in-depth. See the overlap matrix in `conformance/executor_membrane.md`. | Fix issuer to bind `receipt_ref` as an object with a non-empty `decision_receipt_id`. |
| `T1_MISSING_EVIDENCE_MANIFEST` | high | T1 credential lacks `evidence_manifest_sha256`. | Fix issuer to bind the evidence manifest. |

### Phase 7 — Replay

| Code | Severity | Description | Operator Action |
|------|----------|-------------|-----------------|
| `MALFORMED_NONCE` | high | `single_use_nonce` is missing or empty. **In normal operation this condition is caught at phase 1b as `MALFORMED`** by the schema's `required` and `minLength: 16` constraints; the verifier's explicit phase 12 check is therefore fully redundant with the schema and is retained solely as defense-in-depth for embeddings that bypass schema validation. | Fix issuer to generate a nonce. |
| `REPLAY_DETECTED` | critical | The nonce store reports this nonce as already consumed. | Possible replay attack — investigate. |

## Severity Definitions

| Severity | Meaning |
|----------|---------|
| `critical` | Indicates possible attack, key compromise, or canonicalizer drift. Operators SHOULD page on critical refusals. |
| `high` | Indicates an issuer or routing bug. Operators SHOULD investigate but need not page. |
| `medium` | Indicates a likely benign client or clock issue. Operators MAY rate-limit alerts. |
| `low` | Reserved. No Tier 0 / Tier 1 codes are classified as `low`. |

## Stability

These codes are part of the public membrane contract and are versioned with the profile. A future profile version MAY add codes. It MUST NOT remove or rename existing codes. It MUST NOT change the severity of an existing code without bumping the profile version.

## Usage

```python
from assay_membrane.credential_verifier import verify_credential

result = verify_credential(credential, request, now, nonce_store, trusted_keys)
if not result.accepted:
    if result.reason_code == "REPLAY_DETECTED":
        # page security
        ...
    elif result.reason_code == "ANCHORS_NOT_ALLOWED_AT_TIER":
        # honest fail — issuer is sending future-tier credentials to a T0/T1 verifier
        ...
```

All tests in [`conformance/executor_membrane.md`](./conformance/executor_membrane.md) and `reference/python_membrane/tests/` MUST use these codes.
