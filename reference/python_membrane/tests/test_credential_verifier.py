"""
Adversarial conformance tests for the Executor Membrane reference verifier.

These tests implement the test matrix in
conformance/executor_membrane.md. Every test ID below maps to a row in
that matrix and to a MUST/MUST NOT clause in EXECUTOR_MEMBRANE_PROFILE.md.

Two tests are not optional and not "polish":
  * MEMB-TIER-03 — Moth invariant. Anchors at T0/T1 MUST be refused
    regardless of origin.
  * MEMB-SIG-02 — Canonicalizer drift detection. Recomputed credential_id
    with mutated body MUST NOT pass signature verification.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from assay_membrane.credential_verifier import (
    SETTLEMENT_CREDENTIAL_SCHEMA,
    InboundRequest,
    compute_action_digest,
    jcs_canonicalize,
    sha256_hex,
    verify_credential,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@dataclass
class InMemoryNonceStore:
    seen: set = field(default_factory=set)

    def consume(self, nonce, not_after):
        if nonce in self.seen:
            return False
        self.seen.add(nonce)
        return True


@dataclass
class SingleKeyStore:
    key_id: str
    fingerprint: str
    public_bytes: bytes

    def get(self, key_id, fingerprint):
        if key_id != self.key_id or fingerprint != self.fingerprint:
            return None
        return self.public_bytes


class NoKeys:
    def get(self, *_):
        return None


@pytest.fixture
def signing_context():
    sk = Ed25519PrivateKey.generate()
    pk_bytes = sk.public_key().public_bytes(
        encoding=Encoding.Raw, format=PublicFormat.Raw
    )
    fingerprint = sha256_hex(pk_bytes)
    store = SingleKeyStore("key-1", fingerprint, pk_bytes)
    return sk, fingerprint, store


@pytest.fixture
def now():
    return datetime(2026, 4, 8, 7, 27, 0, tzinfo=timezone.utc)


@pytest.fixture
def request_obj():
    payload = {"side": "buy", "notional": 1000, "instrument": "MLB-TEAM-X"}
    # Embedding layer is responsible for computing payload_digest from
    # raw inbound bytes via the canonical envelope. compute_action_digest
    # is the reference implementation of that envelope.
    digest = compute_action_digest(payload)
    return InboundRequest(
        audience="escrow.mlb.v0",
        executor_id="api.brokerage.prod.v4",
        resource_uri="/v1/orders/mlb",
        http_method="POST",
        payload_digest=digest,
    )


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _swap(req: InboundRequest, **kwargs) -> InboundRequest:
    return InboundRequest(
        audience=kwargs.get("audience", req.audience),
        executor_id=kwargs.get("executor_id", req.executor_id),
        resource_uri=kwargs.get("resource_uri", req.resource_uri),
        http_method=kwargs.get("http_method", req.http_method),
        payload_digest=kwargs.get("payload_digest", req.payload_digest),
    )


def _mint_credential(
    sk,
    fingerprint,
    now_dt,
    request: InboundRequest,
    *,
    tier="T0",
    lean=False,
    tweaks=None,
):
    unsigned_without_id = {
        "schema_version": "0.1.0",
        "canon_version": "jcs-rfc8785",
        "issuer": {
            "authority_id": "escrow.market_order.mlb.v0",
            "signer_pubkey_sha256": fingerprint,
            "trust_tier": "T2",
        },
        "key_id": "key-1",
        "issued_at": _iso(now_dt),
        "valid_until": _iso(now_dt + timedelta(seconds=20)),
        "single_use_nonce": "abcdef0123456789abcdef01",
        "audience": request.audience,
        "executor_id": request.executor_id,
        "subject": {
            "subject_id": "organism.mlb.v1",
            "subject_type": "organism",
        },
        "purpose": "place MLB market order",
        "resource_uri": request.resource_uri,
        "http_method": request.http_method,
        "action_digest": request.payload_digest,
        "policy_card_id": "escrow.market_order.mlb.v0",
        "policy_hash": "9e2b8b8aa2d2a3d2df09f5f39b5fc6d58c2d3988182e7dbd96c95b0c97c0a6f1",
        "receipt_ref": {
            "decision_receipt_id": "dr_01JQ0M7G4V2B8X4T9N8S0A1BCD",
        },
        "evidence_manifest_sha256":
            "f1e2d3c4b5a69786756453423120191817161514131211100908070605040302",
        "proof_tier": tier,
        "risk_budget": {
            "units": "usd",
            "magnitude": 10000,
            "scope": "per_credential",
        },
        "obligations": {
            "post_execution": {
                "require_receipt": True,
                "require_ledger_anchor": False,
                "deadline_seconds": 60,
            }
        },
        "external_anchors": [],
    }
    if lean:
        # Tier 0 may legitimately omit the T1-only fields entirely.
        unsigned_without_id.pop("receipt_ref", None)
        unsigned_without_id.pop("evidence_manifest_sha256", None)
    if tweaks:
        tweaks(unsigned_without_id)

    credential_id = sha256_hex(jcs_canonicalize(unsigned_without_id))
    unsigned = dict(unsigned_without_id)
    unsigned["credential_id"] = credential_id
    signed_bytes = jcs_canonicalize(unsigned)
    sig = sk.sign(signed_bytes)

    credential = dict(unsigned)
    credential["signature"] = {
        "algorithm": "Ed25519",
        "signature_scope": "jcs_rfc8785_without_signature",
        "value": base64.b64encode(sig).decode("ascii"),
    }
    return credential


# --------------------------------------------------------------------------- #
# MEMB-ACC: Acceptance
# --------------------------------------------------------------------------- #


def test_MEMB_ACC_01_valid_t0_credential_accepted(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj, tier="T0")
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert result.accepted, result
    assert result.reason_code == "ACCEPT"


def test_MEMB_ACC_02_valid_t1_credential_accepted(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj, tier="T1")
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert result.accepted, result
    assert result.reason_code == "ACCEPT"


def test_MEMB_ACC_03_lean_t0_credential_accepted(
    signing_context, now, request_obj
):
    """A T0 credential that omits receipt_ref and evidence_manifest_sha256
    entirely MUST verify successfully. The schema makes those fields
    tier-conditional (§3.4); they are required only at T1 and OPTIONAL at
    T0. A verifier that always demands them would silently collapse the
    tier distinction."""
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj, tier="T0", lean=True)
    assert "receipt_ref" not in cred
    assert "evidence_manifest_sha256" not in cred
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert result.accepted, result
    assert result.reason_code == "ACCEPT"


# --------------------------------------------------------------------------- #
# MEMB-SCH: Schema and Version
# --------------------------------------------------------------------------- #


def test_MEMB_SCH_01_unsupported_schema_version_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tweaks=lambda c: c.update({"schema_version": "0.2.0"}),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "UNSUPPORTED_SCHEMA"


def test_MEMB_SCH_02_unsupported_canon_version_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tweaks=lambda c: c.update({"canon_version": "jcs-custom"}),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "UNSUPPORTED_CANON"


def test_MEMB_SCH_03_additional_property_refused(
    signing_context, now, request_obj
):
    """JSON Schema validation must actually run.

    A credential carrying an unknown top-level field violates
    additionalProperties: false. The schema validator (phase 1b) MUST
    catch this and emit MALFORMED with a path-bearing detail. This
    confirms the verifier does not accept smuggled fields."""
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    cred["smuggled_field"] = "should not be allowed"
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "MALFORMED"
    assert "schema" in result.detail.lower()


def test_MEMB_SCH_03b_missing_required_field_refused(
    signing_context, now, request_obj
):
    """A credential missing a required top-level field MUST be refused
    with MALFORMED via JSON Schema validation, not via a downstream
    AttributeError or KeyError."""
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    cred.pop("policy_card_id")
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "MALFORMED"


# --------------------------------------------------------------------------- #
# MEMB-TIER: Tier and Anchors
# --------------------------------------------------------------------------- #


def test_MEMB_TIER_01_reserved_tier_refused(signing_context, now, request_obj):
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tweaks=lambda c: c.update({"proof_tier": "T2"}),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "UNSUPPORTED_TIER"


def test_MEMB_TIER_02_unknown_tier_refused(signing_context, now, request_obj):
    """An unknown proof_tier value (e.g. "T9") MUST be refused. The schema
    enum on proof_tier catches this at phase 1b with MALFORMED. The
    verifier also has an explicit fall-through that would emit
    UNSUPPORTED_TIER if schema validation were bypassed. Either reason
    code is conformant per conformance/executor_membrane.md MEMB-TIER-02."""
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tweaks=lambda c: c.update({"proof_tier": "T9"}),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code in {"MALFORMED", "UNSUPPORTED_TIER"}


def test_MEMB_TIER_03_self_referential_anchors_refused(
    signing_context, now, request_obj
):
    """Moth invariant.

    A credential carrying any non-empty external_anchors at T0/T1 MUST be
    refused regardless of anchor origin or content. Independence cannot be
    mechanically established at these tiers, so anchors acquire no trust
    and MUST be refused at the schema boundary.

    The schema's allOf if/then rule for T0/T1 enforces external_anchors
    maxItems: 0, so JSON Schema validation (phase 1b) catches this as
    MALFORMED. The verifier's explicit anchor check at phase 2 is kept
    as defense-in-depth and would emit ANCHORS_NOT_ALLOWED_AT_TIER if
    schema validation were bypassed. Either reason code is conformant
    per conformance/executor_membrane.md MEMB-TIER-03 — what matters is
    that the refusal is hard, observable, and tier-aware.

    A verifier that silently ignores anchors here will eventually be
    assumed by some downstream consumer to have validated them.
    """
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tweaks=lambda c: c.update({
            "external_anchors": [
                {
                    "anchor_type": "transparency_log",
                    "anchor_id": "self://issuer-log/1",
                    "anchor_hash": "a" * 64,
                    "observed_at": _iso(now),
                }
            ],
        }),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code in {"MALFORMED", "ANCHORS_NOT_ALLOWED_AT_TIER"}


# --------------------------------------------------------------------------- #
# MEMB-SIG: Signature and Self-Binding
# --------------------------------------------------------------------------- #


def test_MEMB_SIG_01_mutated_payload_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    cred["risk_budget"]["magnitude"] = 9_999_999
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "CREDENTIAL_ID_MISMATCH"


def test_MEMB_SIG_02_recomputed_id_invalid_signature_refused(
    signing_context, now, request_obj
):
    """Canonicalizer drift detection.

    Attacker mutates payload AND recomputes credential_id to match the
    mutated body. The signature is over canonicalized bytes that include
    credential_id, so recomputing the id cannot rescue a mutated payload.
    Verification MUST fail at signature check.
    """
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    cred["risk_budget"]["magnitude"] = 9_999_999
    unsigned_without_id = {
        k: v for k, v in cred.items()
        if k not in ("signature", "credential_id")
    }
    cred["credential_id"] = sha256_hex(jcs_canonicalize(unsigned_without_id))
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "BAD_SIGNATURE"


def test_MEMB_SIG_03_untrusted_key_refused(signing_context, now, request_obj):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), NoKeys()
    )
    assert not result.accepted
    assert result.reason_code == "UNTRUSTED_KEY"


def test_MEMB_SIG_04_key_fingerprint_mismatch_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    bad_keys = SingleKeyStore("key-1", fp, b"\x00" * 32)
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), bad_keys
    )
    assert not result.accepted
    assert result.reason_code == "KEY_FINGERPRINT_MISMATCH"


# --------------------------------------------------------------------------- #
# MEMB-TIME: Time Window
# --------------------------------------------------------------------------- #


def test_MEMB_TIME_01_expired_credential_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    result = verify_credential(
        cred, request_obj, now + timedelta(seconds=120),
        InMemoryNonceStore(), keys,
    )
    assert not result.accepted
    assert result.reason_code == "EXPIRED"


def test_MEMB_TIME_02_not_yet_valid_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    result = verify_credential(
        cred, request_obj, now - timedelta(seconds=600),
        InMemoryNonceStore(), keys,
    )
    assert not result.accepted
    assert result.reason_code == "NOT_YET_VALID"


# --------------------------------------------------------------------------- #
# MEMB-BIND: Request Binding
# --------------------------------------------------------------------------- #


def test_MEMB_BIND_01_wrong_audience_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    other = _swap(request_obj, audience="escrow.nfl.v0")
    result = verify_credential(cred, other, now, InMemoryNonceStore(), keys)
    assert not result.accepted
    assert result.reason_code == "AUDIENCE_MISMATCH"


def test_MEMB_BIND_02_wrong_executor_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    other = _swap(request_obj, executor_id="api.brokerage.staging.v1")
    result = verify_credential(cred, other, now, InMemoryNonceStore(), keys)
    assert not result.accepted
    assert result.reason_code == "EXECUTOR_MISMATCH"


def test_MEMB_BIND_03_wrong_resource_uri_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    other = _swap(request_obj, resource_uri="/v1/withdraw")
    result = verify_credential(cred, other, now, InMemoryNonceStore(), keys)
    assert not result.accepted
    assert result.reason_code == "RESOURCE_MISMATCH"


def test_MEMB_BIND_04_wrong_method_refused(signing_context, now, request_obj):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    other = _swap(request_obj, http_method="DELETE")
    result = verify_credential(cred, other, now, InMemoryNonceStore(), keys)
    assert not result.accepted
    assert result.reason_code == "METHOD_MISMATCH"


def test_MEMB_BIND_05_action_digest_mismatch_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    other = _swap(request_obj, payload_digest="0" * 64)
    result = verify_credential(cred, other, now, InMemoryNonceStore(), keys)
    assert not result.accepted
    assert result.reason_code == "ACTION_DIGEST_MISMATCH"


# --------------------------------------------------------------------------- #
# MEMB-T1: Tier 1 Extras
# --------------------------------------------------------------------------- #


def test_MEMB_T1_01_t1_without_receipt_ref_refused(
    signing_context, now, request_obj
):
    """T1 with empty decision_receipt_id is caught by the explicit T1
    check (phase 11). The schema's tier-conditional rule requires the
    field to be present; the explicit check enforces non-emptiness as
    defense-in-depth."""
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tier="T1",
        tweaks=lambda c: c.update(
            {"receipt_ref": {"decision_receipt_id": ""}}
        ),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    # Schema validator catches empty string via minLength: 1, emitting
    # MALFORMED before the explicit T1 check runs. Either reason code
    # is conformant per conformance/executor_membrane.md MEMB-T1-01.
    assert result.reason_code in {"MALFORMED", "T1_MISSING_RECEIPT_REF"}


def test_MEMB_T1_01b_t1_with_absent_receipt_ref_refused(
    signing_context, now, request_obj
):
    """T1 with absent receipt_ref MUST be refused. The schema's
    tier-conditional rule (§3.4) makes the field required at T1, so
    JSON Schema validation rejects this with MALFORMED."""
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tier="T1",
        tweaks=lambda c: c.pop("receipt_ref", None),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "MALFORMED"


def test_MEMB_T1_01c_t1_with_wrong_type_receipt_ref_refused(
    signing_context, now, request_obj
):
    """T1 with receipt_ref present but not an object MUST be refused.

    This exercises condition (b) of the composite receipt-ref check
    enumerated in the overlap matrix and in MEMB-T1-01. The schema's
    `receipt_ref` property `type: object` constraint catches this at
    phase 1b as MALFORMED regardless of tier; here we verify the T1
    path specifically so the conformance matrix claim that all three
    composite conditions ((a) absent, (b) wrong type, (c) empty inner)
    are exercised by the test suite holds in-tree, not just in
    external QA artifacts.
    """
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tier="T1",
        tweaks=lambda c: c.update({"receipt_ref": "not_an_object"}),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "MALFORMED"


def test_MEMB_T1_02_t1_without_evidence_manifest_refused(
    signing_context, now, request_obj
):
    """T1 with absent evidence_manifest_sha256 MUST be refused. Caught
    by JSON Schema validation via the §3.4 tier-conditional rule.
    Documented in conformance/executor_membrane.md MEMB-T1-02."""
    sk, fp, keys = signing_context
    cred = _mint_credential(
        sk, fp, now, request_obj,
        tier="T1",
        tweaks=lambda c: c.pop("evidence_manifest_sha256", None),
    )
    result = verify_credential(
        cred, request_obj, now, InMemoryNonceStore(), keys
    )
    assert not result.accepted
    assert result.reason_code == "MALFORMED"


# --------------------------------------------------------------------------- #
# MEMB-REPLAY: Replay
# --------------------------------------------------------------------------- #


def test_MEMB_REPLAY_01_nonce_replay_refused(
    signing_context, now, request_obj
):
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    store = InMemoryNonceStore()
    first = verify_credential(cred, request_obj, now, store, keys)
    assert first.accepted
    second = verify_credential(cred, request_obj, now, store, keys)
    assert not second.accepted
    assert second.reason_code == "REPLAY_DETECTED"


def test_MEMB_REPLAY_02_nonce_not_consumed_on_structural_failure(
    signing_context, now, request_obj
):
    """A refusal before the nonce step MUST NOT burn the nonce."""
    sk, fp, keys = signing_context
    cred = _mint_credential(sk, fp, now, request_obj)
    bad = _swap(request_obj, executor_id="api.brokerage.staging.v1")
    store = InMemoryNonceStore()
    first = verify_credential(cred, bad, now, store, keys)
    assert not first.accepted
    # Same nonce remains fresh for the legitimate request.
    second = verify_credential(cred, request_obj, now, store, keys)
    assert second.accepted


# --------------------------------------------------------------------------- #
# Cross-language JCS vectors (deferred)
# --------------------------------------------------------------------------- #


@pytest.mark.skip(
    reason="requires conformant RFC 8785 JCS implementation; "
    "the prototype jcs_canonicalize in this package is not RFC 8785-conformant "
    "and cannot be checked against cross-language vectors. "
    "See EXECUTOR_MEMBRANE_PROFILE.md §0.3 and reference/python_membrane/README.md."
)
def test_MEMB_JCS_01_cross_language_vectors_pending():
    """Placeholder for cross-language JCS conformance vectors.

    When a real RFC 8785 canonicalizer is wired in, this test should load
    a vector file shared with non-Python implementations and assert that
    canonicalization produces byte-identical output.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# Bundled schema sync (drift detection)
# --------------------------------------------------------------------------- #


def test_bundled_schema_matches_canonical():
    """The bundled assay_membrane/_schema.json MUST be byte-identical to
    the canonical schemas/settlement_credential.schema.json in the repo.
    This test catches drift between the wire contract and the
    reference verifier's view of it."""
    import json as _json
    from pathlib import Path

    here = Path(__file__).resolve()
    # tests/test_credential_verifier.py -> python_membrane/tests/ ->
    # python_membrane/ -> reference/ -> repo_root/
    repo_root = here.parents[3]
    canonical = repo_root / "schemas" / "settlement_credential.schema.json"
    assert canonical.exists(), f"canonical schema not found at {canonical}"

    canonical_obj = _json.loads(canonical.read_text(encoding="utf-8"))
    assert canonical_obj == SETTLEMENT_CREDENTIAL_SCHEMA, (
        "Bundled schema in assay_membrane/_schema.json has drifted from "
        "the canonical schemas/settlement_credential.schema.json. "
        "Re-copy the canonical file into the package."
    )
