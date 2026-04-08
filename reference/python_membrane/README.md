# Assay Executor Membrane Reference Verifier

> **Non-normative. Prototype-only. NOT production-safe.**
>
> This package exists to exercise the conformance suite in
> [`conformance/executor_membrane.md`](../../conformance/executor_membrane.md)
> and to demonstrate the verifier algorithm contract from
> [`EXECUTOR_MEMBRANE_PROFILE.md`](../../EXECUTOR_MEMBRANE_PROFILE.md).
>
> **It MUST NOT be used in production.**
>
> The `jcs_canonicalize` function in `credential_verifier.py` is a prototype
> approximation of [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) JSON
> Canonicalization Scheme. It is not conformant. Any cross-implementation
> divergence between issuer and verifier canonicalization will silently
> break signature verification. Production verifiers MUST replace this
> function with a fully RFC 8785-conformant canonicalizer and pin
> cross-language test vectors before deployment.

## What this package is

A reference implementation of the verifier described in
[`EXECUTOR_MEMBRANE_PROFILE.md`](../../EXECUTOR_MEMBRANE_PROFILE.md) §2.2.

The package contains exactly one public entry point:

```python
from assay_membrane.credential_verifier import (
    InboundRequest,
    NonceStore,
    TrustedKeys,
    VerificationResult,
    verify_credential,
)

result = verify_credential(
    credential=credential_dict,
    request=inbound_request,
    now=current_utc_time,
    nonce_store=my_nonce_store,
    trusted_keys=my_key_store,
)

if result.accepted:
    # release the request to the executor
    ...
else:
    # honest fail. log result.reason_code and result.detail.
    ...
```

The verifier is a pure function modulo the injected `nonce_store` and
`trusted_keys`. It performs no network I/O. It does not parse decision
receipts. It does not interpret policy. It refuses anchors at Tier 0/1
unconditionally.

## What this package is NOT

- Not a production verifier.
- Not a conformant JCS canonicalizer.
- Not an issuer (issuers are intentionally out of scope for this repo).
- Not an executor (executors are intentionally out of scope for this repo).
- Not a trust store, nonce store, or key rotation system.
- Not a policy engine, decision-receipt parser, or attestation validator.

## Install

```bash
pip install -e ".[dev]"
```

## Run conformance tests

```bash
pytest tests/test_credential_verifier.py -v
```

Or from the repo root:

```bash
make membrane-test
```

## What you must replace before going to production

| Component | Status | Required action |
|-----------|--------|-----------------|
| `jcs_canonicalize` | Prototype | Replace with a fully RFC 8785-conformant canonicalizer. Pin cross-language test vectors. |
| `InMemoryNonceStore` (in tests) | Test fixture only | Replace with a durable, partition-tolerant nonce store. Retain consumed nonces for at least `valid_until + skew`. |
| `SingleKeyStore` (in tests) | Test fixture only | Replace with a real trusted key store. Define rotation, compromise, and retirement procedures. |
| Algorithm agility | Ed25519 only | If you need additional algorithms, bump the profile version. Do NOT silently widen the enum. |

## Reference, not normative

If this implementation disagrees with
[`EXECUTOR_MEMBRANE_PROFILE.md`](../../EXECUTOR_MEMBRANE_PROFILE.md),
[`schemas/settlement_credential.schema.json`](../../schemas/settlement_credential.schema.json),
or [`MEMBRANE_REASON_CODES.md`](../../MEMBRANE_REASON_CODES.md), the profile,
schema, and reason codes win. File an issue.
