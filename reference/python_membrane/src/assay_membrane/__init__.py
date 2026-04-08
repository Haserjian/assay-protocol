"""Assay Executor Membrane reference verifier.

Non-normative, prototype-only. NOT production-safe.

See ../README.md and ../../../EXECUTOR_MEMBRANE_PROFILE.md for full warnings
and the normative profile.
"""

from assay_membrane.credential_verifier import (
    SETTLEMENT_CREDENTIAL_SCHEMA,
    InboundRequest,
    NonceStore,
    TrustedKeys,
    VerificationResult,
    compute_action_digest,
    jcs_canonicalize,
    sha256_hex,
    verify_credential,
)

__all__ = [
    "SETTLEMENT_CREDENTIAL_SCHEMA",
    "InboundRequest",
    "NonceStore",
    "TrustedKeys",
    "VerificationResult",
    "compute_action_digest",
    "jcs_canonicalize",
    "sha256_hex",
    "verify_credential",
]

__version__ = "0.1.0"
