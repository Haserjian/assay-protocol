"""Proof-Carrying Capabilities (PCCap) — CRITICAL action authorization.

This module implements PCCap tokens: signed, scoped, expiring permits for
dangerous operations that exceed static policy bounds.

Core concepts:
- PCCap token: A signed capability granting specific rights
- Scope: What the token permits (tool, args, constraints)
- Expiry: TTL-bounded validity
- Signature: Ed25519 or HMAC-SHA256 verification

Flow:
1. Agent requests CRITICAL action (e.g., fs.delete with path=/important)
2. Gateway evaluates policy -> REQUIRE_APPROVAL (or DENY without capability)
3. Human approves -> mint_pccap() creates signed token
4. Agent presents token with request
5. Gateway verifies token scope matches request -> ALLOW

Integration with authz.PolicyEngine:
- PCCap augments (doesn't replace) base policy
- CRITICAL actions denied by default unless PCCap presented
- Token scope must match request exactly (no path traversal allowed)

Reference: CSP Tool Safety Profile v1.2, Section 5.3 (Capabilities)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import PurePath
from typing import Any

from .types import Principal


class PCCapError(Exception):
    """Base error for PCCap operations."""
    pass


class TokenExpiredError(PCCapError):
    """Token has expired."""
    pass


class TokenScopeError(PCCapError):
    """Token scope doesn't match request."""
    pass


class TokenSignatureError(PCCapError):
    """Token signature verification failed."""
    pass


class TokenNotFoundError(PCCapError):
    """Token not found in store."""
    pass


class SignatureAlgorithm(str, Enum):
    """Supported signature algorithms."""
    HMAC_SHA256 = "HS256"
    ED25519 = "Ed25519"


@dataclass
class PCCapScope:
    """Scope constraints for a PCCap token.

    Defines what the token permits:
    - tool_name: Which tool (exact match)
    - allowed_args: Permitted argument patterns
    - path_prefix: For fs operations, restrict to path prefix
    - max_bytes: For writes, maximum size
    """
    tool_name: str
    allowed_args: dict[str, Any] = field(default_factory=dict)
    path_prefix: str | None = None
    max_bytes: int | None = None

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "allowed_args": self.allowed_args,
            "path_prefix": self.path_prefix,
            "max_bytes": self.max_bytes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PCCapScope":
        return cls(
            tool_name=d["tool_name"],
            allowed_args=d.get("allowed_args", {}),
            path_prefix=d.get("path_prefix"),
            max_bytes=d.get("max_bytes"),
        )

    def matches_request(self, tool_name: str, arguments: dict) -> tuple[bool, str | None]:
        """Check if a request matches this scope.

        Returns:
            (matches, reason) - reason is error message if not matched
        """
        # Tool name must match exactly
        if tool_name != self.tool_name:
            return False, f"tool mismatch: {tool_name} != {self.tool_name}"

        # Check path prefix constraint
        if self.path_prefix is not None:
            path = arguments.get("path") or arguments.get("file_path") or arguments.get("target")
            if path:
                # Reject traversal attempts before and after normalization.
                path_text = str(path)
                if ".." in PurePath(path_text).parts:
                    return False, f"path traversal detected: {path_text}"
                normalized = os.path.normpath(path_text)
                if ".." in PurePath(normalized).parts:
                    return False, f"path traversal detected: {path}"
                try:
                    requested_abs = os.path.abspath(normalized)
                    allowed_abs = os.path.abspath(os.path.normpath(self.path_prefix))
                    if os.path.commonpath([requested_abs, allowed_abs]) != allowed_abs:
                        return (
                            False,
                            f"path {path_text} not under allowed prefix {self.path_prefix}",
                        )
                except ValueError:
                    return False, f"path {path_text} not under allowed prefix {self.path_prefix}"

        # Check max_bytes constraint
        if self.max_bytes is not None:
            content = arguments.get("content") or arguments.get("data")
            if content is not None:
                if isinstance(content, bytes):
                    size_bytes = len(content)
                else:
                    size_bytes = len(str(content).encode())
                if size_bytes > self.max_bytes:
                    return False, f"content exceeds max_bytes ({self.max_bytes})"

        # Check allowed_args constraints (exact match for specified keys)
        for key, expected in self.allowed_args.items():
            actual = arguments.get(key)
            if actual != expected:
                return False, f"arg mismatch: {key}={actual} (expected {expected})"

        return True, None


@dataclass
class PCCapToken:
    """A Proof-Carrying Capability token.

    Invariants:
    - Token is immutable after creation
    - Signature covers all fields except signature itself
    - issued_at and expires_at are UTC timestamps
    """
    token_id: str
    principal_sub: str
    scope: PCCapScope
    issued_at: float  # Unix timestamp
    expires_at: float  # Unix timestamp
    issued_by: str  # Who approved this capability
    policy_id: str | None = None  # Link to policy that required approval
    single_use: bool = True
    nonce: str | None = None
    signature: str | None = None
    algorithm: SignatureAlgorithm = SignatureAlgorithm.HMAC_SHA256

    def to_dict(self, include_signature: bool = True) -> dict:
        d = {
            "token_id": self.token_id,
            "principal_sub": self.principal_sub,
            "scope": self.scope.to_dict(),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "issued_by": self.issued_by,
            "policy_id": self.policy_id,
            "single_use": self.single_use,
            "nonce": self.nonce,
            "algorithm": self.algorithm.value,
        }
        if include_signature and self.signature:
            d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "PCCapToken":
        return cls(
            token_id=d["token_id"],
            principal_sub=d["principal_sub"],
            scope=PCCapScope.from_dict(d["scope"]),
            issued_at=d["issued_at"],
            expires_at=d["expires_at"],
            issued_by=d["issued_by"],
            policy_id=d.get("policy_id"),
            single_use=d.get("single_use", True),
            nonce=d.get("nonce"),
            signature=d.get("signature"),
            algorithm=SignatureAlgorithm(d.get("algorithm", "HS256")),
        )

    def is_expired(self, now: float | None = None) -> bool:
        """Check if token has expired."""
        if now is None:
            now = time.time()
        return now >= self.expires_at

    def canonical_bytes(self) -> bytes:
        """Get canonical bytes for signing (excludes signature field)."""
        d = self.to_dict(include_signature=False)
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()


class Keyring:
    """Key management for PCCap signing/verification.

    For production: integrate with HSM or vault.
    This implementation uses HMAC-SHA256 with symmetric keys.
    """

    def __init__(self, secret_key: bytes | None = None):
        """Initialize keyring.

        Args:
            secret_key: HMAC secret. If None, generates random key.
        """
        self._secret = secret_key or os.urandom(32)

    def sign(self, token: PCCapToken) -> str:
        """Sign a token, returning base64-encoded signature."""
        msg = token.canonical_bytes()
        sig = hmac.new(self._secret, msg, hashlib.sha256).digest()
        return base64.b64encode(sig).decode()

    def verify(self, token: PCCapToken) -> bool:
        """Verify token signature."""
        if not token.signature:
            return False

        expected = self.sign(token)
        # Use constant-time comparison
        return hmac.compare_digest(token.signature, expected)


class PCCapStore:
    """In-memory store for issued PCCap tokens.

    For production: use persistent storage with TTL cleanup.
    """

    def __init__(self):
        self._tokens: dict[str, PCCapToken] = {}
        self._used_tokens: set[str] = set()

    def store(self, token: PCCapToken) -> None:
        """Store a token."""
        self._tokens[token.token_id] = token

    def get(self, token_id: str) -> PCCapToken | None:
        """Retrieve a token by ID."""
        return self._tokens.get(token_id)

    def revoke(self, token_id: str) -> bool:
        """Revoke (delete) a token."""
        if token_id in self._tokens:
            del self._tokens[token_id]
            self._used_tokens.discard(token_id)
            return True
        return False

    def mark_used(self, token_id: str) -> bool:
        """Mark token as consumed. Returns False if already consumed."""
        if token_id in self._used_tokens:
            return False
        self._used_tokens.add(token_id)
        return True

    def is_used(self, token_id: str) -> bool:
        """Return True when token was already consumed."""
        return token_id in self._used_tokens

    def cleanup_expired(self, now: float | None = None) -> int:
        """Remove expired tokens. Returns count removed."""
        if now is None:
            now = time.time()

        expired = [
            tid for tid, token in self._tokens.items()
            if token.is_expired(now)
        ]
        for tid in expired:
            del self._tokens[tid]
            self._used_tokens.discard(tid)
        return len(expired)

    def list_for_principal(self, principal_sub: str) -> list[PCCapToken]:
        """List all active tokens for a principal."""
        now = time.time()
        return [
            t for t in self._tokens.values()
            if (
                t.principal_sub == principal_sub
                and not t.is_expired(now)
                and not self.is_used(t.token_id)
            )
        ]


def generate_token_id() -> str:
    """Generate a unique token ID."""
    return f"pccap_{base64.b64encode(os.urandom(12)).decode().rstrip('=')}"


def mint_pccap(
    principal: Principal,
    scope: PCCapScope,
    issued_by: str,
    keyring: Keyring,
    ttl_seconds: int = 300,  # 5 minutes default
    policy_id: str | None = None,
    single_use: bool = True,
) -> PCCapToken:
    """Mint a new PCCap token.

    Args:
        principal: The identity receiving the capability
        scope: What the token permits
        issued_by: Who approved this (human reviewer ID)
        keyring: Key management for signing
        ttl_seconds: Token lifetime (default 5 minutes)
        policy_id: Optional link to policy requiring approval

    Returns:
        Signed PCCapToken

    Example:
        >>> scope = PCCapScope(
        ...     tool_name="fs.delete",
        ...     path_prefix="/tmp/scratch/",
        ... )
        >>> token = mint_pccap(
        ...     principal=Principal(sub="agent@example.com", actor_type="agent"),
        ...     scope=scope,
        ...     issued_by="admin@example.com",
        ...     keyring=keyring,
        ...     ttl_seconds=300,
        ... )
    """
    now = time.time()

    token = PCCapToken(
        token_id=generate_token_id(),
        principal_sub=principal.sub,
        scope=scope,
        issued_at=now,
        expires_at=now + ttl_seconds,
        issued_by=issued_by,
        policy_id=policy_id,
        single_use=single_use,
        nonce=base64.b64encode(os.urandom(12)).decode().rstrip("="),
    )

    # Sign the token
    token.signature = keyring.sign(token)

    return token


def mint_pccap_fs_delete(
    principal: Principal,
    path_prefix: str,
    issued_by: str,
    keyring: Keyring,
    ttl_seconds: int = 300,
    single_use: bool = True,
) -> PCCapToken:
    """Convenience: mint a PCCap for fs.delete operations.

    This is a common pattern for the "wedge" demo:
    - Agent wants to delete files
    - Human approves with path constraint
    - Token restricts deletion to specific prefix

    Args:
        principal: Agent identity
        path_prefix: Path prefix where deletion is allowed
        issued_by: Human approver
        keyring: Signing keys
        ttl_seconds: Token lifetime

    Returns:
        Signed PCCapToken scoped to fs.delete under path_prefix
    """
    scope = PCCapScope(
        tool_name="fs.delete",
        path_prefix=os.path.normpath(path_prefix),
    )
    return mint_pccap(
        principal=principal,
        scope=scope,
        issued_by=issued_by,
        keyring=keyring,
        ttl_seconds=ttl_seconds,
        single_use=single_use,
    )


class ReasonCodePCCap(str, Enum):
    """Additional reason codes for PCCap decisions."""
    DENY_PCCAP_EXPIRED = "DENY_PCCAP_EXPIRED"
    DENY_PCCAP_SCOPE_MISMATCH = "DENY_PCCAP_SCOPE_MISMATCH"
    DENY_PCCAP_SIGNATURE_INVALID = "DENY_PCCAP_SIGNATURE_INVALID"
    DENY_PCCAP_PRINCIPAL_MISMATCH = "DENY_PCCAP_PRINCIPAL_MISMATCH"
    DENY_PCCAP_REPLAY = "DENY_PCCAP_REPLAY"
    ALLOW_PCCAP_VALID = "ALLOW_PCCAP_VALID"


def enforce_pccap(
    principal: Principal,
    tool_name: str,
    arguments: dict,
    token: PCCapToken,
    keyring: Keyring,
) -> tuple[bool, str, ReasonCodePCCap]:
    """Enforce a PCCap token against a request.

    Args:
        principal: Requesting identity
        tool_name: Tool being invoked
        arguments: Tool arguments
        token: PCCap token presented
        keyring: For signature verification

    Returns:
        (allowed, reason, code) tuple

    Checks performed:
    1. Token not expired
    2. Signature valid
    3. Principal matches token
    4. Scope matches request
    """
    # Check expiry
    if token.is_expired():
        return (
            False,
            (
                f"Token {token.token_id} expired at "
                f"{datetime.fromtimestamp(token.expires_at, tz=timezone.utc).isoformat()}"
            ),
            ReasonCodePCCap.DENY_PCCAP_EXPIRED,
        )

    # Verify signature
    if not keyring.verify(token):
        return (
            False,
            f"Token {token.token_id} has invalid signature",
            ReasonCodePCCap.DENY_PCCAP_SIGNATURE_INVALID,
        )

    # Check principal
    if token.principal_sub != principal.sub:
        return (
            False,
            f"Token for {token.principal_sub}, not {principal.sub}",
            ReasonCodePCCap.DENY_PCCAP_PRINCIPAL_MISMATCH,
        )

    # Check scope
    matches, reason = token.scope.matches_request(tool_name, arguments)
    if not matches:
        return (
            False,
            f"Scope mismatch: {reason}",
            ReasonCodePCCap.DENY_PCCAP_SCOPE_MISMATCH,
        )

    return (
        True,
        f"PCCap {token.token_id} valid for {tool_name}",
        ReasonCodePCCap.ALLOW_PCCAP_VALID,
    )


def enforce_pccap_for_fs_delete(
    principal: Principal,
    path: str,
    token: PCCapToken,
    keyring: Keyring,
) -> tuple[bool, str, ReasonCodePCCap]:
    """Convenience: enforce PCCap for fs.delete operation.

    Args:
        principal: Agent identity
        path: Path to delete
        token: PCCap token
        keyring: For verification

    Returns:
        (allowed, reason, code)
    """
    return enforce_pccap(
        principal=principal,
        tool_name="fs.delete",
        arguments={"path": path},
        token=token,
        keyring=keyring,
    )


class PCCapPolicyEngine:
    """Policy engine extension for PCCap-aware authorization.

    Wraps base PolicyEngine to add PCCap token handling for CRITICAL
    actions that require explicit capability grants.
    """

    def __init__(
        self,
        keyring: Keyring,
        store: PCCapStore | None = None,
    ):
        self._keyring = keyring
        self._store = store or PCCapStore()

    def mint(
        self,
        principal: Principal,
        scope: PCCapScope,
        issued_by: str,
        ttl_seconds: int = 300,
        policy_id: str | None = None,
        single_use: bool = True,
    ) -> PCCapToken:
        """Mint and store a new token."""
        token = mint_pccap(
            principal=principal,
            scope=scope,
            issued_by=issued_by,
            keyring=self._keyring,
            ttl_seconds=ttl_seconds,
            policy_id=policy_id,
            single_use=single_use,
        )
        self._store.store(token)
        return token

    def evaluate_with_pccap(
        self,
        principal: Principal,
        tool_name: str,
        arguments: dict,
        token_id: str | None = None,
    ) -> tuple[bool, str, str]:
        """Evaluate request with PCCap support.

        Args:
            principal: Requesting identity
            tool_name: Tool to invoke
            arguments: Tool arguments
            token_id: Optional PCCap token ID

        Returns:
            (allowed, reason, code)
        """
        if not token_id:
            # No token - check if principal has any valid tokens for this scope
            tokens = self._store.list_for_principal(principal.sub)
            for t in tokens:
                if t.single_use and self._store.is_used(t.token_id):
                    continue
                matches, _ = t.scope.matches_request(tool_name, arguments)
                if matches:
                    if t.single_use and self._store.is_used(t.token_id):
                        return (
                            False,
                            f"Token {t.token_id} has already been used",
                            ReasonCodePCCap.DENY_PCCAP_REPLAY.value,
                        )
                    allowed, reason, code = enforce_pccap(
                        principal, tool_name, arguments, t, self._keyring
                    )
                    if allowed:
                        if t.single_use and not self._store.mark_used(t.token_id):
                            return (
                                False,
                                f"Token {t.token_id} has already been used",
                                ReasonCodePCCap.DENY_PCCAP_REPLAY.value,
                            )
                        return allowed, reason, code.value

            return (
                False,
                f"No valid PCCap token for {tool_name}",
                "DENY_NO_PCCAP",
            )

        # Look up token
        token = self._store.get(token_id)
        if not token:
            return (
                False,
                f"Token {token_id} not found",
                "DENY_PCCAP_NOT_FOUND",
            )
        if token.single_use and self._store.is_used(token.token_id):
            return (
                False,
                f"Token {token.token_id} has already been used",
                ReasonCodePCCap.DENY_PCCAP_REPLAY.value,
            )

        allowed, reason, code = enforce_pccap(
            principal, tool_name, arguments, token, self._keyring
        )
        if allowed and token.single_use and not self._store.mark_used(token.token_id):
            return (
                False,
                f"Token {token.token_id} has already been used",
                ReasonCodePCCap.DENY_PCCAP_REPLAY.value,
            )
        return allowed, reason, code.value

    def revoke(self, token_id: str) -> bool:
        """Revoke a token."""
        return self._store.revoke(token_id)

    def cleanup(self) -> int:
        """Remove expired tokens."""
        return self._store.cleanup_expired()


# Exports
__all__ = [
    "PCCapError",
    "TokenExpiredError",
    "TokenScopeError",
    "TokenSignatureError",
    "TokenNotFoundError",
    "SignatureAlgorithm",
    "PCCapScope",
    "PCCapToken",
    "Keyring",
    "PCCapStore",
    "generate_token_id",
    "mint_pccap",
    "mint_pccap_fs_delete",
    "ReasonCodePCCap",
    "enforce_pccap",
    "enforce_pccap_for_fs_delete",
    "PCCapPolicyEngine",
]
