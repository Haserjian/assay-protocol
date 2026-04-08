"""
Credential verifier for the Executor Membrane Profile v0.1.

================================================================================
NON-NORMATIVE. PROTOTYPE-ONLY. NOT PRODUCTION-SAFE.
================================================================================

This module is a reference implementation of the verifier algorithm contract
defined in EXECUTOR_MEMBRANE_PROFILE.md §2.2. It exists to exercise the
conformance suite in conformance/executor_membrane.md and to demonstrate the
exact verification order, not to be deployed.

The `jcs_canonicalize` function below is a PROTOTYPE approximation of
RFC 8785 (https://www.rfc-editor.org/rfc/rfc8785) JSON Canonicalization
Scheme. It is NOT conformant. Production verifiers MUST replace it with a
fully RFC 8785-compliant canonicalizer and pin cross-language test vectors
before deployment. Any divergence between issuer and verifier
canonicalization will silently break signature verification.

If this module disagrees with EXECUTOR_MEMBRANE_PROFILE.md,
schemas/settlement_credential.schema.json, or MEMBRANE_REASON_CODES.md,
the profile, schema, and reason codes win.

Spinal invariant:
    No execution crosses the executor membrane on narrative authority alone.
    Effects require a settlement credential whose execution-relevant claims
    are canonically encoded, cryptographically bound to the intended action,
    and locally verified by the executor.

Tier 0 and Tier 1 prove bounded authorization integrity, not truth.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from importlib.resources import files as _resource_files
from typing import Any, Mapping, Protocol


SUPPORTED_SCHEMA_VERSION = "0.1.0"
SUPPORTED_CANON_VERSION = "jcs-rfc8785"
SUPPORTED_SIGNATURE_SCOPE = "jcs_rfc8785_without_signature"
SUPPORTED_ALGORITHMS = frozenset({"Ed25519"})
SUPPORTED_TIERS = frozenset({"T0", "T1"})
RESERVED_TIERS = frozenset({"T2", "T3"})
DEFAULT_CLOCK_SKEW = timedelta(seconds=2)


# --------------------------------------------------------------------------- #
# Bundled schema + JSON Schema validator
# --------------------------------------------------------------------------- #


def _load_bundled_schema() -> dict[str, Any]:
    """Load the bundled copy of settlement_credential.schema.json.

    The package ships a byte-identical copy of the canonical schema at
    assay_membrane/_schema.json. A sync test in the test suite verifies the
    bundled copy matches schemas/settlement_credential.schema.json in the
    repo.
    """
    resource = _resource_files("assay_membrane") / "_schema.json"
    return json.loads(resource.read_text(encoding="utf-8"))


SETTLEMENT_CREDENTIAL_SCHEMA: dict[str, Any] = _load_bundled_schema()


def _build_validator():
    """Construct a Draft 2020-12 validator. Imported lazily so that an
    environment without jsonschema fails with a clear error message at
    construction time, not at module import."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "jsonschema is required for credential verification. "
            "Install with: pip install jsonschema>=4.18"
        ) from exc
    return Draft202012Validator(SETTLEMENT_CREDENTIAL_SCHEMA)


_VALIDATOR = _build_validator()


# --------------------------------------------------------------------------- #
# Result
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    reason_code: str
    detail: str
    credential_id: str | None = None

    @classmethod
    def accept(cls, credential_id: str) -> "VerificationResult":
        return cls(True, "ACCEPT", "credential verified", credential_id)

    @classmethod
    def refuse(
        cls,
        reason_code: str,
        detail: str,
        credential_id: str | None = None,
    ) -> "VerificationResult":
        return cls(False, reason_code, detail, credential_id)


# --------------------------------------------------------------------------- #
# Injected dependencies
# --------------------------------------------------------------------------- #


class NonceStore(Protocol):
    def consume(self, nonce: str, not_after: datetime) -> bool:
        """Atomically mark `nonce` consumed until `not_after`. Return True
        only on the first successful consume."""
        ...


class TrustedKeys(Protocol):
    def get(self, key_id: str, fingerprint: str) -> bytes | None:
        """Return raw Ed25519 public key bytes for (key_id, fingerprint),
        or None if not trusted. The verifier independently re-checks that
        SHA-256 of the returned bytes equals `fingerprint`."""
        ...


@dataclass(frozen=True)
class InboundRequest:
    audience: str
    executor_id: str
    resource_uri: str
    http_method: str
    payload_digest: str  # sha256 hex of the canonical request envelope


# --------------------------------------------------------------------------- #
# Canonicalization + helpers
# --------------------------------------------------------------------------- #


def jcs_canonicalize(obj: Any) -> bytes:
    """
    PROTOTYPE approximation of RFC 8785 JSON Canonicalization Scheme.

    THIS IS NOT A CONFORMANT JCS IMPLEMENTATION. It is suitable only for
    ASCII-keyed, finite-number, no-NaN inputs in test fixtures. It does NOT
    implement the full RFC 8785 number serialization rules. Cross-language
    parity is NOT guaranteed.

    Production verifiers MUST replace this function with a fully RFC 8785
    -compliant canonicalizer and pin cross-language test vectors.
    """
    # TODO(jcs): replace with RFC 8785-conformant canonicalizer before any
    # production deployment. See README.md and the module docstring.
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_action_digest(payload: Mapping[str, Any]) -> str:
    """Reference implementation of the canonical request envelope.

    See EXECUTOR_MEMBRANE_PROFILE.md §3.3.1. The embedding layer is
    responsible for computing the action_digest from the actual inbound
    payload using this canonical envelope (or an equivalent), and for
    passing the resulting digest in InboundRequest.payload_digest.

    The verifier itself does NOT access raw request bytes. The membrane
    proves the credential is bound to a specific action_digest; the
    embedding layer is responsible for ensuring the inbound bytes hash
    to that digest under the canonical envelope.

    For JSON payloads:

        action_digest = sha256_hex( jcs_canonicalize( payload ) )

    For non-JSON payloads, the canonical envelope is OUT OF SCOPE for
    Executor Membrane Profile v0.1.

    --------------------------------------------------------------------
    Overclaim guard. Read this before citing the helper as a proof.
    --------------------------------------------------------------------

    What this function proves:
        - The digest of `payload` under the reference canonicalization
          contract (jcs_canonicalize + sha256).

    What this function does NOT prove:
        - Byte-identity between `payload` and any earlier or later
          representation of the original inbound request.
        - That the structured `payload` passed in is what the original
          client sent. Acquiring and normalizing raw bytes is the
          embedding layer's responsibility.
        - That the canonicalization contract used here is RFC 8785
          conformant. jcs_canonicalize in this package is a prototype
          approximation; production callers MUST substitute a conformant
          canonicalizer here as well, or this helper inherits the same
          drift risk as the verifier.

    A matching action_digest at the verifier demonstrates equivalence
    under the canonicalization contract. It does NOT demonstrate
    end-to-end tamper-evidence of the original request bytes. Downstream
    consumers MUST NOT smuggle stronger claims on top of this helper.
    """
    return sha256_hex(jcs_canonicalize(payload))


def _parse_rfc3339(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except Exception:
        return None


def _verify_ed25519(public_key: bytes, message: bytes, signature: bytes) -> bool:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "cryptography is required for credential verification"
        ) from exc

    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# Verifier entry point
# --------------------------------------------------------------------------- #


def verify_credential(
    credential: Mapping[str, Any],
    request: InboundRequest,
    now: datetime,
    nonce_store: NonceStore,
    trusted_keys: TrustedKeys,
    *,
    clock_skew: timedelta = DEFAULT_CLOCK_SKEW,
) -> VerificationResult:
    """Verify a settlement credential against an inbound request.

    Implements EXECUTOR_MEMBRANE_PROFILE.md §2.2 in the exact order required.
    Pure modulo the injected `nonce_store` and `trusted_keys`. The only side
    effect is `nonce_store.consume`, which runs LAST so nonces are never
    burned on structural failures (see MEMB-REPLAY-02).
    """

    # --- Phase 1a: version pinning (cheap, specific reason codes) ---------- #
    #
    # Run version checks BEFORE schema validation so that mismatched
    # versions emit UNSUPPORTED_SCHEMA / UNSUPPORTED_CANON instead of being
    # absorbed into a generic MALFORMED from the schema's `const` rules.

    if not isinstance(credential, Mapping):
        return VerificationResult.refuse("MALFORMED", "credential is not an object")

    if credential.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        return VerificationResult.refuse(
            "UNSUPPORTED_SCHEMA",
            f"schema_version={credential.get('schema_version')!r}",
        )
    if credential.get("canon_version") != SUPPORTED_CANON_VERSION:
        return VerificationResult.refuse(
            "UNSUPPORTED_CANON",
            f"canon_version={credential.get('canon_version')!r}",
        )

    # --- Phase 1b: JSON Schema validation (Draft 2020-12) ------------------ #
    #
    # This is the real schema validation step required by
    # EXECUTOR_MEMBRANE_PROFILE.md §2.2 step 2. It enforces:
    #   - additionalProperties: false (no smuggled fields)
    #   - presence of required fields
    #   - type and pattern correctness on every field
    #   - the tier-conditional rules in §3.4 and §3.5:
    #       * external_anchors empty at T0/T1
    #       * receipt_ref + evidence_manifest_sha256 required at T1
    #
    # Sorted by absolute_path so test output is deterministic.

    schema_errors = sorted(
        _VALIDATOR.iter_errors(dict(credential)),
        key=lambda e: tuple(map(str, e.absolute_path)),
    )
    if schema_errors:
        first = schema_errors[0]
        path = "/".join(map(str, first.absolute_path)) or "<root>"
        return VerificationResult.refuse(
            "MALFORMED",
            f"schema: {path}: {first.message}",
        )

    # --- Phase 2: tier and anchors ----------------------------------------- #

    proof_tier = credential.get("proof_tier")
    if proof_tier in RESERVED_TIERS:
        return VerificationResult.refuse(
            "UNSUPPORTED_TIER",
            f"tier {proof_tier} is reserved and not verifiable here",
        )
    if proof_tier not in SUPPORTED_TIERS:
        return VerificationResult.refuse(
            "UNSUPPORTED_TIER",
            f"unknown proof_tier={proof_tier!r}",
        )

    anchors = credential.get("external_anchors")
    if not isinstance(anchors, list):
        return VerificationResult.refuse(
            "MALFORMED", "external_anchors must be an array"
        )
    if len(anchors) > 0:
        # Moth invariant. Self-referential or otherwise: T0/T1 cannot
        # mechanically establish independence, so anchors acquire no trust
        # and MUST be refused at the schema boundary.
        return VerificationResult.refuse(
            "ANCHORS_NOT_ALLOWED_AT_TIER",
            f"tier {proof_tier} does not accept external_anchors",
        )

    # --- Phase 3: self-binding and signature ------------------------------- #

    try:
        unsigned = {k: v for k, v in credential.items() if k != "signature"}
        unsigned_for_id = {
            k: v for k, v in unsigned.items() if k != "credential_id"
        }
        expected_id = sha256_hex(jcs_canonicalize(unsigned_for_id))
    except Exception as exc:
        return VerificationResult.refuse("CANONICALIZATION_FAILED", str(exc))

    credential_id = credential.get("credential_id")
    if credential_id != expected_id:
        return VerificationResult.refuse(
            "CREDENTIAL_ID_MISMATCH",
            f"got={credential_id} expected={expected_id}",
            credential_id if isinstance(credential_id, str) else None,
        )

    signature_block = credential.get("signature")
    if not isinstance(signature_block, Mapping):
        return VerificationResult.refuse(
            "MALFORMED", "missing signature block", credential_id
        )
    if signature_block.get("algorithm") not in SUPPORTED_ALGORITHMS:
        return VerificationResult.refuse(
            "UNSUPPORTED_ALG",
            f"algorithm={signature_block.get('algorithm')!r}",
            credential_id,
        )
    if signature_block.get("signature_scope") != SUPPORTED_SIGNATURE_SCOPE:
        return VerificationResult.refuse(
            "UNSUPPORTED_SCOPE",
            f"signature_scope={signature_block.get('signature_scope')!r}",
            credential_id,
        )

    issuer_block = credential.get("issuer")
    if not isinstance(issuer_block, Mapping):
        return VerificationResult.refuse(
            "MALFORMED", "missing issuer block", credential_id
        )
    fingerprint = issuer_block.get("signer_pubkey_sha256")
    key_id = credential.get("key_id")
    if not isinstance(fingerprint, str) or not isinstance(key_id, str):
        return VerificationResult.refuse(
            "MALFORMED", "missing key_id or fingerprint", credential_id
        )

    public_key = trusted_keys.get(key_id, fingerprint)
    if public_key is None:
        return VerificationResult.refuse(
            "UNTRUSTED_KEY",
            f"key_id={key_id} fingerprint={fingerprint}",
            credential_id,
        )
    if sha256_hex(public_key) != fingerprint:
        return VerificationResult.refuse(
            "KEY_FINGERPRINT_MISMATCH",
            "trusted key bytes do not match asserted fingerprint",
            credential_id,
        )

    try:
        signed_bytes = jcs_canonicalize(unsigned)
        signature_bytes = base64.b64decode(
            signature_block["value"], validate=True
        )
    except Exception as exc:
        return VerificationResult.refuse(
            "MALFORMED_SIGNATURE", str(exc), credential_id
        )

    if not _verify_ed25519(public_key, signed_bytes, signature_bytes):
        return VerificationResult.refuse(
            "BAD_SIGNATURE", "signature did not verify", credential_id
        )

    # --- Phase 4: time window ---------------------------------------------- #

    now_utc = now.astimezone(timezone.utc)
    issued_at = _parse_rfc3339(str(credential.get("issued_at", "")))
    valid_until = _parse_rfc3339(str(credential.get("valid_until", "")))
    if issued_at is None or valid_until is None:
        return VerificationResult.refuse(
            "MALFORMED_TIME",
            "issued_at or valid_until unparseable",
            credential_id,
        )
    if issued_at >= valid_until:
        return VerificationResult.refuse(
            "INVERTED_WINDOW", "issued_at >= valid_until", credential_id
        )
    if now_utc + clock_skew < issued_at:
        return VerificationResult.refuse(
            "NOT_YET_VALID", f"now={now_utc.isoformat()}", credential_id
        )
    if now_utc >= valid_until:
        return VerificationResult.refuse(
            "EXPIRED", f"now={now_utc.isoformat()}", credential_id
        )

    # --- Phase 5: request binding ------------------------------------------ #

    if credential.get("audience") != request.audience:
        return VerificationResult.refuse(
            "AUDIENCE_MISMATCH",
            f"got={credential.get('audience')!r}",
            credential_id,
        )
    if credential.get("executor_id") != request.executor_id:
        return VerificationResult.refuse(
            "EXECUTOR_MISMATCH",
            f"got={credential.get('executor_id')!r}",
            credential_id,
        )
    if credential.get("resource_uri") != request.resource_uri:
        return VerificationResult.refuse(
            "RESOURCE_MISMATCH",
            f"got={credential.get('resource_uri')!r}",
            credential_id,
        )
    cred_method = credential.get("http_method")
    if (
        not isinstance(cred_method, str)
        or cred_method.upper() != request.http_method.upper()
    ):
        return VerificationResult.refuse(
            "METHOD_MISMATCH", f"got={cred_method!r}", credential_id
        )
    if credential.get("action_digest") != request.payload_digest:
        return VerificationResult.refuse(
            "ACTION_DIGEST_MISMATCH",
            "payload digest does not match",
            credential_id,
        )

    # --- Phase 6: Tier 1 extras -------------------------------------------- #

    if proof_tier == "T1":
        # Composite check: T1_MISSING_RECEIPT_REF is intentionally named
        # narrower than its scope. It covers all three of:
        #   (a) receipt_ref field absent
        #   (b) receipt_ref present but not an object
        #   (c) receipt_ref.decision_receipt_id missing or empty
        # The schema ALSO catches all three at phase 1b as MALFORMED:
        #   (a) via the §3.4 tier-conditional `required`
        #   (b) via the `receipt_ref` property `type: object` constraint
        #   (c) via the inner `required` and `minLength: 1`
        # This explicit phase 11 check is therefore fully redundant with
        # the schema at T1 and is retained solely as defense-in-depth
        # (e.g., if the schema validator is bypassed by an embedding).
        # See conformance/executor_membrane.md §"Reason Code Overlap Matrix".
        #
        # DO NOT REMOVE THIS CHECK SOLELY BECAUSE IT IS REDUNDANT WITH THE
        # SCHEMA AT T1. It exists to preserve the stable T1_MISSING_RECEIPT_REF
        # refusal semantics in the public reason-code surface and to protect
        # embeddings that bypass schema validation. Removal requires a profile
        # version bump per conformance/executor_membrane.md amendment rule 5.
        receipt_ref = credential.get("receipt_ref")
        if (
            not isinstance(receipt_ref, Mapping)
            or not receipt_ref.get("decision_receipt_id")
        ):
            return VerificationResult.refuse(
                "T1_MISSING_RECEIPT_REF",
                "tier T1 requires receipt_ref to be an object with a "
                "non-empty decision_receipt_id",
                credential_id,
            )
        if not credential.get("evidence_manifest_sha256"):
            return VerificationResult.refuse(
                "T1_MISSING_EVIDENCE_MANIFEST",
                "tier T1 requires evidence_manifest_sha256",
                credential_id,
            )

    # --- Phase 7: replay (LAST) -------------------------------------------- #

    nonce = credential.get("single_use_nonce")
    if not isinstance(nonce, str) or not nonce:
        return VerificationResult.refuse(
            "MALFORMED_NONCE", "single_use_nonce missing", credential_id
        )
    if not nonce_store.consume(nonce, valid_until):
        return VerificationResult.refuse(
            "REPLAY_DETECTED", f"nonce already seen: {nonce}", credential_id
        )

    return VerificationResult.accept(credential_id)
