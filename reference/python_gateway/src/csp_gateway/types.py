"""Core types for CSP MCP Gateway."""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal


class TrustLevel(str, Enum):
    INTERNAL = "internal"
    VERIFIED = "verified"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class RiskCategory(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionResult(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class TokenMode(str, Enum):
    EXCHANGED = "exchanged"
    VAULT = "vault"
    BLOCKED = "blocked"
    NONE = "none"


class ReasonCode(str, Enum):
    # Allow
    ALLOW_POLICY_MATCH = "ALLOW_POLICY_MATCH"

    # Deny - Auth
    DENY_NO_AUTHN = "DENY_NO_AUTHN"
    DENY_NO_PERMISSION = "DENY_NO_PERMISSION"
    DENY_TOOL_NOT_FOUND = "DENY_TOOL_NOT_FOUND"
    DENY_NO_MATCHING_RULE = "DENY_NO_MATCHING_RULE"

    # Deny - Validation
    DENY_UNKNOWN_FIELDS = "DENY_UNKNOWN_FIELDS"
    DENY_PAYLOAD_TOO_LARGE = "DENY_PAYLOAD_TOO_LARGE"
    DENY_PATH_TRAVERSAL = "DENY_PATH_TRAVERSAL"
    DENY_RATE_LIMIT = "DENY_RATE_LIMIT"

    # Deny - Security
    DENY_KILL_SWITCH = "DENY_KILL_SWITCH"
    DENY_PASSTHROUGH_BLOCKED = "DENY_PASSTHROUGH_BLOCKED"
    DENY_OAUTH_REDIRECT_INVALID = "DENY_OAUTH_REDIRECT_INVALID"
    DENY_OAUTH_CLIENT_UNAPPROVED = "DENY_OAUTH_CLIENT_UNAPPROVED"

    # Approval
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass
class Principal:
    """Authenticated identity."""

    sub: str
    actor_type: Literal["user", "agent", "system"]
    client_id: str | None = None
    org_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "sub": self.sub,
            "actor_type": self.actor_type,
            "client_id": self.client_id,
            "org_id": self.org_id,
        }


@dataclass
class ToolEntry:
    """Tool in the registry."""

    server_id: str
    tool_name: str
    trust_level: TrustLevel
    risk_category: RiskCategory
    schema: dict | None = None
    version: str | None = None

    def to_dict(self) -> dict:
        return {
            "server_id": self.server_id,
            "tool_name": self.tool_name,
            "trust_level": self.trust_level.value,
            "risk_category": self.risk_category.value,
        }


@dataclass
class Decision:
    """Policy decision."""

    result: DecisionResult
    reason_codes: list[ReasonCode] = field(default_factory=list)
    policy_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "result": self.result.value,
            "reason_codes": [rc.value for rc in self.reason_codes],
            "policy_id": self.policy_id,
        }


@dataclass
class TokenHandling:
    """Token handling metadata."""

    mode: TokenMode
    passthrough_detected: bool = False
    audience: str | None = None

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "passthrough_detected": self.passthrough_detected,
            "audience": self.audience,
        }


@dataclass
class Receipt:
    """MCP Gateway Receipt."""

    receipt_id: str
    trace_id: str
    ts: str
    principal: Principal
    mcp_method: str
    decision: Decision
    token_handling: TokenHandling
    server_id: str | None = None
    tool_name: str | None = None
    trust_level: TrustLevel | None = None
    args_hash: str | None = None
    size_bytes_in: int | None = None
    sandbox_fs_policy: str | None = None
    sandbox_net_policy: str | None = None
    outcome_status: str | None = None

    @classmethod
    def create(
        cls,
        principal: Principal,
        mcp_method: str,
        decision: Decision,
        token_handling: TokenHandling,
        trace_id: str | None = None,
        **kwargs,
    ) -> "Receipt":
        return cls(
            receipt_id=str(uuid.uuid4()),
            trace_id=trace_id or str(uuid.uuid4()),
            ts=datetime.now(timezone.utc).isoformat(),
            principal=principal,
            mcp_method=mcp_method,
            decision=decision,
            token_handling=token_handling,
            **kwargs,
        )

    def to_dict(self) -> dict:
        return {
            "ts": self.ts,
            "receipt_id": self.receipt_id,
            "trace_id": self.trace_id,
            "principal": self.principal.to_dict(),
            "mcp": {
                "method": self.mcp_method,
                "server_id": self.server_id,
                "tool_name": self.tool_name,
                "trust_level": self.trust_level.value if self.trust_level else None,
            },
            "request": {
                "args_hash": self.args_hash,
                "size_bytes_in": self.size_bytes_in,
            },
            "decision": self.decision.to_dict(),
            "token_handling": self.token_handling.to_dict(),
            "sandbox": {
                "fs_policy": self.sandbox_fs_policy,
                "net_policy": self.sandbox_net_policy,
            },
        }


def hash_args(args: dict) -> str:
    """Hash arguments for receipt (never store raw secrets)."""
    import json

    canonical = json.dumps(args, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
