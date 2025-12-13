"""Credential Broker - MUST 5: Credential boundary (no token passthrough)."""

from dataclasses import dataclass

from .types import Decision, DecisionResult, ReasonCode, TokenHandling, TokenMode


@dataclass
class UpstreamCredential:
    """Credential for upstream server."""

    token: str | None
    mode: TokenMode
    audience: str | None = None


class CredentialBroker:
    """Manages credentials for upstream MCP servers.

    MUST 5: NEVER passthrough raw client tokens upstream.
    Exchange via RFC 8693 or retrieve from vault.
    """

    def __init__(self):
        self._vault: dict[str, str] = {}
        self._exchange_config: dict[str, dict] = {}
        self._passthrough_blocked = True

    def configure_vault(self, server_id: str, secret: str) -> None:
        """Configure vault secret for a server."""
        self._vault[server_id] = secret

    def configure_exchange(
        self, server_id: str, audience: str, scope: str | None = None
    ) -> None:
        """Configure token exchange for a server."""
        self._exchange_config[server_id] = {"audience": audience, "scope": scope}

    def allow_passthrough(self, allow: bool = True) -> None:
        """Configure passthrough behavior (default: blocked)."""
        self._passthrough_blocked = not allow

    def get_upstream_credential(
        self, client_token: str, target_server: str
    ) -> tuple[UpstreamCredential | None, TokenHandling]:
        """Get credential for upstream server.

        Returns (credential, token_handling_metadata).
        If passthrough would occur, returns (None, metadata with passthrough_detected=True).
        """
        # Check vault first
        if target_server in self._vault:
            credential = UpstreamCredential(
                token=self._vault[target_server],
                mode=TokenMode.VAULT,
                audience=target_server,
            )
            handling = TokenHandling(
                mode=TokenMode.VAULT,
                passthrough_detected=False,
                audience=target_server,
            )
            return credential, handling

        # Check exchange config
        if target_server in self._exchange_config:
            config = self._exchange_config[target_server]
            # Simulate token exchange (in production, call token endpoint)
            exchanged_token = f"exchanged:{target_server}:{client_token[:8]}..."
            credential = UpstreamCredential(
                token=exchanged_token,
                mode=TokenMode.EXCHANGED,
                audience=config["audience"],
            )
            handling = TokenHandling(
                mode=TokenMode.EXCHANGED,
                passthrough_detected=False,
                audience=config["audience"],
            )
            return credential, handling

        # No config = would be passthrough
        if self._passthrough_blocked:
            # Block passthrough - return None credential
            handling = TokenHandling(
                mode=TokenMode.BLOCKED,
                passthrough_detected=True,
            )
            return None, handling

        # This path should never be reached in conforming implementations
        handling = TokenHandling(
            mode=TokenMode.NONE,
            passthrough_detected=True,
        )
        return None, handling

    def deny_passthrough(self) -> Decision:
        """Return deny decision for passthrough attempt."""
        return Decision(
            result=DecisionResult.DENY,
            reason_codes=[ReasonCode.DENY_PASSTHROUGH_BLOCKED],
        )
