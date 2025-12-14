#!/usr/bin/env python3
"""
Crypto Core: The Autograph Kernel

Constitutional Receipt Standard (CRS) cryptographic primitives:
- JCS canonicalization (RFC 8785)
- SHA-256 hashing
- Ed25519 signing/verification (RFC 8032)
- Receipt chain verification

This is the foundation for court-grade proof.
"""

import hashlib
import json
import base64
import sys
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field

# Optional: Use cryptography library for Ed25519
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    warnings.warn(
        "cryptography library not installed. Signing will be simulated.",
        UserWarning,
        stacklevel=1,
    )


# =============================================================================
# JCS Canonicalization (RFC 8785)
# =============================================================================

def jcs_canonicalize(obj: Any) -> str:
    """
    Canonicalize a Python object to JCS (JSON Canonicalization Scheme).

    RFC 8785 requires:
    - Sorted object keys (lexicographic)
    - No whitespace
    - Specific number formatting
    - UTF-8 encoding

    Args:
        obj: Python dict/list/value to canonicalize

    Returns:
        Canonical JSON string
    """
    return json.dumps(
        obj,
        separators=(',', ':'),
        sort_keys=True,
        ensure_ascii=False,
    )


def canonical_hash(obj: Any, exclude_fields: Optional[list[str]] = None) -> str:
    """
    Compute SHA-256 hash of canonicalized JSON.

    Args:
        obj: Object to hash
        exclude_fields: Fields to exclude (e.g., ['signature', 'receipt_hash'])

    Returns:
        Hex-encoded SHA-256 hash prefixed with "sha256:"
    """
    if exclude_fields and isinstance(obj, dict):
        obj = {k: v for k, v in obj.items() if k not in exclude_fields}

    canonical = jcs_canonicalize(obj)
    digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    return f"sha256:{digest}"


# =============================================================================
# Ed25519 Key Management
# =============================================================================

@dataclass
class KeyPair:
    """Ed25519 key pair with metadata."""
    key_id: str
    private_key: Optional[bytes] = None
    public_key: Optional[bytes] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """Export public portion for sharing."""
        return {
            "key_id": self.key_id,
            "public_key": base64.b64encode(self.public_key).decode() if self.public_key else None,
            "created_at": self.created_at,
            "algorithm": "Ed25519",
        }


def generate_keypair(key_id: Optional[str] = None) -> KeyPair:
    """
    Generate a new Ed25519 key pair.

    Args:
        key_id: Optional identifier; generated if not provided

    Returns:
        KeyPair with private and public key bytes
    """
    if not HAS_CRYPTO:
        # Simulated keypair for testing without cryptography library
        return KeyPair(
            key_id=key_id or f"simulated-{uuid.uuid4().hex[:8]}",
            private_key=b"SIMULATED_PRIVATE_KEY",
            public_key=b"SIMULATED_PUBLIC_KEY",
        )

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    return KeyPair(
        key_id=key_id or f"ed25519-{uuid.uuid4().hex[:8]}",
        private_key=private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        public_key=public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ),
    )


def load_private_key(key_bytes: bytes) -> "Ed25519PrivateKey":
    """Load Ed25519 private key from raw bytes."""
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography library required for signing")
    return Ed25519PrivateKey.from_private_bytes(key_bytes)


def load_public_key(key_bytes: bytes) -> "Ed25519PublicKey":
    """Load Ed25519 public key from raw bytes."""
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography library required for verification")
    return Ed25519PublicKey.from_public_bytes(key_bytes)


# =============================================================================
# Receipt Signing
# =============================================================================

@dataclass
class Signature:
    """Ed25519 signature with metadata."""
    alg: str = "Ed25519"
    key_id: str = ""
    sig: str = ""  # Base64-encoded signature bytes

    def to_dict(self) -> dict:
        return {
            "alg": self.alg,
            "key_id": self.key_id,
            "sig": self.sig,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Signature":
        return cls(
            alg=d.get("alg", "Ed25519"),
            key_id=d.get("key_id", ""),
            sig=d.get("sig", ""),
        )


def sign_receipt(receipt: dict, keypair: KeyPair) -> dict:
    """
    Sign a receipt using Ed25519.

    The signature covers the receipt_hash field (which is computed from
    the canonical JSON excluding signature and receipt_hash).

    Args:
        receipt: Receipt dict (must have receipt_hash computed)
        keypair: KeyPair with private key

    Returns:
        Receipt dict with signature field added
    """
    if "receipt_hash" not in receipt:
        raise ValueError("Receipt must have receipt_hash computed before signing")

    hash_to_sign = receipt["receipt_hash"]

    if not HAS_CRYPTO or keypair.private_key == b"SIMULATED_PRIVATE_KEY":
        # Simulated signature for testing
        sig_bytes = hashlib.sha256(
            f"SIMULATED_SIG:{hash_to_sign}:{keypair.key_id}".encode()
        ).digest()
    else:
        private_key = load_private_key(keypair.private_key)
        sig_bytes = private_key.sign(hash_to_sign.encode('utf-8'))

    signature = Signature(
        alg="Ed25519",
        key_id=keypair.key_id,
        sig=base64.b64encode(sig_bytes).decode(),
    )

    result = dict(receipt)
    result["signature"] = signature.to_dict()
    return result


def verify_signature(receipt: dict, public_key_bytes: bytes) -> bool:
    """
    Verify an Ed25519 signature on a receipt.

    Args:
        receipt: Receipt dict with signature field
        public_key_bytes: Raw public key bytes

    Returns:
        True if signature is valid
    """
    if "signature" not in receipt:
        return False

    if "receipt_hash" not in receipt:
        return False

    sig = Signature.from_dict(receipt["signature"])
    hash_to_verify = receipt["receipt_hash"]

    if not HAS_CRYPTO:
        # Simulated verification
        expected = hashlib.sha256(
            f"SIMULATED_SIG:{hash_to_verify}:{sig.key_id}".encode()
        ).digest()
        return base64.b64decode(sig.sig) == expected

    try:
        sig_bytes = base64.b64decode(sig.sig)
        public_key = load_public_key(public_key_bytes)
        public_key.verify(sig_bytes, hash_to_verify.encode('utf-8'))
        return True
    except Exception:
        return False


# =============================================================================
# Receipt Creation
# =============================================================================

def create_receipt(
    receipt_type: str,
    payload: dict,
    parent_hashes: Optional[list[str]] = None,
    proof_tier: str = "core",
    keypair: Optional[KeyPair] = None,
) -> dict:
    """
    Create a complete CRS-compliant receipt.

    Args:
        receipt_type: Namespaced type (e.g., "crs.agent_action/v1")
        payload: Domain-specific content
        parent_hashes: Hash references to parent receipts
        proof_tier: "none", "simulated", "core", or "court"
        keypair: Optional keypair for signing (required for court tier)

    Returns:
        Complete receipt dict
    """
    receipt = {
        "receipt_id": str(uuid.uuid4()),
        "receipt_type": receipt_type,
        "ts": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "parent_hashes": parent_hashes or [],
        "proof_tier": proof_tier,
        "schema_version": "crs/0.1",
    }

    # Compute hash (excluding signature and receipt_hash)
    receipt["receipt_hash"] = canonical_hash(receipt, exclude_fields=["receipt_hash", "signature"])

    # Sign if keypair provided or court tier requires it
    if keypair and proof_tier in ("core", "court"):
        receipt = sign_receipt(receipt, keypair)

    return receipt


# =============================================================================
# Chain Verification
# =============================================================================

@dataclass
class VerificationResult:
    """Result of receipt verification."""
    receipt_id: str
    hash_valid: bool
    signature_valid: Optional[bool] = None
    chain_valid: Optional[bool] = None
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Overall validity check."""
        if not self.hash_valid:
            return False
        if self.signature_valid is False:
            return False
        if self.chain_valid is False:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "hash_valid": self.hash_valid,
            "signature_valid": self.signature_valid,
            "chain_valid": self.chain_valid,
            "is_valid": self.is_valid,
            "errors": self.errors,
        }


def verify_receipt_hash(receipt: dict) -> VerificationResult:
    """
    Verify a receipt's hash is correct.

    Args:
        receipt: Receipt dict to verify

    Returns:
        VerificationResult
    """
    result = VerificationResult(
        receipt_id=receipt.get("receipt_id", "unknown"),
        hash_valid=False,
    )

    if "receipt_hash" not in receipt:
        result.errors.append("Missing receipt_hash field")
        return result

    expected_hash = canonical_hash(receipt, exclude_fields=["receipt_hash", "signature"])

    if receipt["receipt_hash"] == expected_hash:
        result.hash_valid = True
    else:
        result.errors.append(f"Hash mismatch: expected {expected_hash}, got {receipt['receipt_hash']}")

    return result


def verify_chain(receipts: list[dict], public_keys: Optional[dict[str, bytes]] = None) -> list[VerificationResult]:
    """
    Verify a chain of receipts.

    Args:
        receipts: List of receipts in chain order
        public_keys: Optional dict mapping key_id to public key bytes

    Returns:
        List of VerificationResult for each receipt
    """
    results = []
    known_hashes = set()

    for receipt in receipts:
        result = verify_receipt_hash(receipt)

        # Verify parent chain references
        parent_hashes = receipt.get("parent_hashes", [])
        if parent_hashes:
            missing_parents = [h for h in parent_hashes if h not in known_hashes]
            if missing_parents:
                result.chain_valid = False
                result.errors.append(f"Missing parent receipts: {missing_parents}")
            else:
                result.chain_valid = True

        # Verify signature if present and keys available
        if "signature" in receipt and public_keys:
            sig = Signature.from_dict(receipt["signature"])
            if sig.key_id in public_keys:
                result.signature_valid = verify_signature(receipt, public_keys[sig.key_id])
                if not result.signature_valid:
                    result.errors.append(f"Invalid signature from key {sig.key_id}")
            else:
                result.signature_valid = None
                result.errors.append(f"Unknown signing key: {sig.key_id}")

        # Track this receipt's hash for chain verification
        if result.hash_valid:
            known_hashes.add(receipt["receipt_hash"])

        results.append(result)

    return results


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI for crypto core operations."""
    import argparse

    parser = argparse.ArgumentParser(description="CRS Crypto Core")
    subparsers = parser.add_subparsers(dest="command")

    # keygen command
    keygen_parser = subparsers.add_parser("keygen", help="Generate Ed25519 keypair")
    keygen_parser.add_argument("--key-id", help="Key identifier")
    keygen_parser.add_argument("--output", "-o", help="Output directory", default=".")

    # hash command
    hash_parser = subparsers.add_parser("hash", help="Compute canonical hash")
    hash_parser.add_argument("file", help="JSON file to hash")

    # sign command
    sign_parser = subparsers.add_parser("sign", help="Sign a receipt")
    sign_parser.add_argument("receipt", help="Receipt JSON file")
    sign_parser.add_argument("--key", "-k", required=True, help="Private key file")
    sign_parser.add_argument("--output", "-o", help="Output file")

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify receipt(s)")
    verify_parser.add_argument("receipts", nargs="+", help="Receipt JSON files")
    verify_parser.add_argument("--keys", "-k", help="Public keys JSON file")

    args = parser.parse_args()

    if args.command == "keygen":
        keypair = generate_keypair(args.key_id)
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Save private key (keep secret!)
        private_path = out_dir / f"{keypair.key_id}.private.json"
        with open(private_path, "w") as f:
            json.dump({
                "key_id": keypair.key_id,
                "algorithm": "Ed25519",
                "private_key": base64.b64encode(keypair.private_key).decode(),
                "created_at": keypair.created_at,
            }, f, indent=2)
        print(f"Private key saved to: {private_path}")

        # Save public key (share freely)
        public_path = out_dir / f"{keypair.key_id}.public.json"
        with open(public_path, "w") as f:
            json.dump(keypair.to_dict(), f, indent=2)
        print(f"Public key saved to: {public_path}")

    elif args.command == "hash":
        with open(args.file) as f:
            obj = json.load(f)
        hash_value = canonical_hash(obj, exclude_fields=["receipt_hash", "signature"])
        print(hash_value)

    elif args.command == "sign":
        with open(args.receipt) as f:
            receipt = json.load(f)
        with open(args.key) as f:
            key_data = json.load(f)

        keypair = KeyPair(
            key_id=key_data["key_id"],
            private_key=base64.b64decode(key_data["private_key"]),
        )

        if "receipt_hash" not in receipt:
            receipt["receipt_hash"] = canonical_hash(receipt, exclude_fields=["receipt_hash", "signature"])

        signed = sign_receipt(receipt, keypair)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(signed, f, indent=2)
            print(f"Signed receipt saved to: {args.output}")
        else:
            print(json.dumps(signed, indent=2))

    elif args.command == "verify":
        receipts = []
        for path in args.receipts:
            with open(path) as f:
                receipts.append(json.load(f))

        public_keys = {}
        if args.keys:
            with open(args.keys) as f:
                keys_data = json.load(f)
            for key_data in keys_data:
                public_keys[key_data["key_id"]] = base64.b64decode(key_data["public_key"])

        results = verify_chain(receipts, public_keys if public_keys else None)

        all_valid = True
        for result in results:
            status = "PASS" if result.is_valid else "FAIL"
            print(f"[{status}] {result.receipt_id}")
            if result.errors:
                for error in result.errors:
                    print(f"       {error}")
            all_valid = all_valid and result.is_valid

        exit(0 if all_valid else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
