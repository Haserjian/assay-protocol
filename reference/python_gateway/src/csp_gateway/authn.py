"""Authentication - MUST 2: AuthN on every request."""

from dataclasses import dataclass

from .types import Decision, DecisionResult, Principal, ReasonCode


@dataclass
class AuthnResult:
    """Result of authentication."""

    authenticated: bool
    principal: Principal | None = None
    error: str | None = None


class Authenticator:
    """Token verification and principal extraction.

    This is a stub implementation for reference/testing.
    Production implementations should use proper JWT verification.
    """

    def __init__(self, valid_tokens: dict[str, dict] | None = None):
        """
        Args:
            valid_tokens: Map of token -> claims for testing.
                         In production, use JWT verification.
        """
        self._valid_tokens = valid_tokens or {}

    def add_valid_token(self, token: str, claims: dict) -> None:
        """Add a valid token for testing."""
        self._valid_tokens[token] = claims

    def authenticate(self, token: str | None) -> AuthnResult:
        """Authenticate a request.

        MUST 2: Every request must be authenticated.
        """
        if not token:
            return AuthnResult(
                authenticated=False,
                error="Missing authentication token",
            )

        # Strip Bearer prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        claims = self._valid_tokens.get(token)
        if not claims:
            return AuthnResult(
                authenticated=False,
                error="Invalid authentication token",
            )

        principal = Principal(
            sub=claims.get("sub", "unknown"),
            actor_type=claims.get("actor_type", "user"),
            client_id=claims.get("client_id"),
            org_id=claims.get("org_id"),
        )

        return AuthnResult(authenticated=True, principal=principal)

    def deny_no_authn(self) -> Decision:
        """Return a deny decision for authentication failure."""
        return Decision(
            result=DecisionResult.DENY,
            reason_codes=[ReasonCode.DENY_NO_AUTHN],
        )
