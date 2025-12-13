"""MCP Gateway - Main orchestration layer."""

from dataclasses import dataclass
from pathlib import Path

from .authn import Authenticator
from .authz import PolicyEngine
from .credentials import CredentialBroker
from .incident import IncidentController
from .preflight import PreflightValidator
from .receipts import ReceiptEmitter
from .registry import ToolRegistry
from .sandbox import SandboxConfig, SandboxExecutor
from .types import (
    Decision,
    DecisionResult,
    Principal,
    ReasonCode,
    Receipt,
    TokenHandling,
    TokenMode,
    ToolEntry,
)


@dataclass
class GatewayConfig:
    """Gateway configuration."""

    workspace: str
    max_payload_bytes: int = 1_000_000
    network_allowlist: list[str] | None = None
    receipts_path: str | None = None


class MCPGateway:
    """CSP MCP Gateway reference implementation.

    Orchestrates the enforcement flow:
    AuthN -> Discovery/AuthZ -> Preflight -> Credentials -> Sandbox -> Receipts

    This is reference quality for conformance testing.
    """

    def __init__(self, config: GatewayConfig):
        self._config = config
        self._workspace = Path(config.workspace)

        # Initialize components
        self._registry = ToolRegistry()
        self._authn = Authenticator()
        self._authz = PolicyEngine(self._registry)
        self._credentials = CredentialBroker()
        self._preflight = PreflightValidator(
            max_payload_bytes=config.max_payload_bytes,
            workspace=config.workspace,
        )
        self._sandbox = SandboxExecutor(
            SandboxConfig(
                workspace=self._workspace,
                network_allowlist=config.network_allowlist or [],
            )
        )
        self._receipts = ReceiptEmitter(
            output_path=Path(config.receipts_path) if config.receipts_path else None
        )
        self._incident = IncidentController()

    # Component accessors (for testing/configuration)
    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    @property
    def authn(self) -> Authenticator:
        return self._authn

    @property
    def authz(self) -> PolicyEngine:
        return self._authz

    @property
    def credentials(self) -> CredentialBroker:
        return self._credentials

    @property
    def preflight(self) -> PreflightValidator:
        return self._preflight

    @property
    def sandbox(self) -> SandboxExecutor:
        return self._sandbox

    @property
    def receipts(self) -> ReceiptEmitter:
        return self._receipts

    @property
    def incident(self) -> IncidentController:
        return self._incident

    def handle_tools_list(
        self, token: str | None, trace_id: str | None = None
    ) -> tuple[list[ToolEntry] | None, Decision, Receipt]:
        """Handle tools/list request.

        MUST 2: AuthN required
        MUST 3: Identity-bound filtering
        """
        # MUST 2: Authenticate
        authn_result = self._authn.authenticate(token)
        if not authn_result.authenticated:
            decision = self._authn.deny_no_authn()
            receipt = self._receipts.emit(
                principal=Principal(sub="anonymous", actor_type="user"),
                mcp_method="tools/list",
                decision=decision,
                token_handling=TokenHandling(mode=TokenMode.NONE, passthrough_detected=False),
                trace_id=trace_id,
            )
            return None, decision, receipt

        principal = authn_result.principal

        # MUST 3: Filter by permissions
        all_tools = self._registry.list_all()
        visible_tools = self._authz.filter_tools_list(principal, all_tools)

        decision = Decision(
            result=DecisionResult.ALLOW,
            reason_codes=[ReasonCode.ALLOW_POLICY_MATCH],
        )
        receipt = self._receipts.emit(
            principal=principal,
            mcp_method="tools/list",
            decision=decision,
            token_handling=TokenHandling(mode=TokenMode.NONE, passthrough_detected=False),
            trace_id=trace_id,
        )
        return visible_tools, decision, receipt

    def handle_tools_call(
        self,
        token: str | None,
        tool_name: str,
        arguments: dict,
        server_id: str | None = None,
        trace_id: str | None = None,
    ) -> tuple[Decision, Receipt]:
        """Handle tools/call request.

        Full enforcement flow:
        MUST 2: AuthN
        MUST 4: AuthZ
        MUST 7: Preflight
        MUST 5: Credentials
        MUST 9: Receipts
        """
        # MUST 2: Authenticate
        authn_result = self._authn.authenticate(token)
        if not authn_result.authenticated:
            decision = self._authn.deny_no_authn()
            receipt = self._receipts.emit(
                principal=Principal(sub="anonymous", actor_type="user"),
                mcp_method="tools/call",
                decision=decision,
                token_handling=TokenHandling(mode=TokenMode.NONE, passthrough_detected=False),
                trace_id=trace_id,
                tool_name=tool_name,
                server_id=server_id,
                arguments=arguments,
            )
            return decision, receipt

        principal = authn_result.principal

        # Check incident state
        if self._incident.is_revoked(principal):
            decision = Decision(
                result=DecisionResult.DENY,
                reason_codes=[ReasonCode.DENY_KILL_SWITCH],
            )
            receipt = self._receipts.emit(
                principal=principal,
                mcp_method="tools/call",
                decision=decision,
                token_handling=TokenHandling(mode=TokenMode.BLOCKED, passthrough_detected=False),
                trace_id=trace_id,
                tool_name=tool_name,
                server_id=server_id,
                arguments=arguments,
            )
            return decision, receipt

        # MUST 4: Authorize
        authz_decision = self._authz.evaluate(principal, tool_name, arguments)
        if authz_decision.result != DecisionResult.ALLOW:
            receipt = self._receipts.emit(
                principal=principal,
                mcp_method="tools/call",
                decision=authz_decision,
                token_handling=TokenHandling(mode=TokenMode.NONE, passthrough_detected=False),
                trace_id=trace_id,
                tool_name=tool_name,
                server_id=server_id,
                arguments=arguments,
            )
            return authz_decision, receipt

        # MUST 7: Preflight validation
        validation = self._preflight.validate(tool_name, arguments)
        if not validation.valid:
            decision = self._preflight.to_decision(validation)
            receipt = self._receipts.emit(
                principal=principal,
                mcp_method="tools/call",
                decision=decision,
                token_handling=TokenHandling(mode=TokenMode.NONE, passthrough_detected=False),
                trace_id=trace_id,
                tool_name=tool_name,
                server_id=server_id,
                arguments=arguments,
            )
            return decision, receipt

        # MUST 5: Get upstream credentials (if server_id provided)
        if server_id:
            credential, token_handling = self._credentials.get_upstream_credential(
                token or "", server_id
            )
            if token_handling.passthrough_detected:
                decision = self._credentials.deny_passthrough()
                receipt = self._receipts.emit(
                    principal=principal,
                    mcp_method="tools/call",
                    decision=decision,
                    token_handling=token_handling,
                    trace_id=trace_id,
                    tool_name=tool_name,
                    server_id=server_id,
                    arguments=arguments,
                )
                return decision, receipt
        else:
            token_handling = TokenHandling(mode=TokenMode.NONE, passthrough_detected=False)

        # All checks passed
        decision = Decision(
            result=DecisionResult.ALLOW,
            reason_codes=[ReasonCode.ALLOW_POLICY_MATCH],
        )
        receipt = self._receipts.emit(
            principal=principal,
            mcp_method="tools/call",
            decision=decision,
            token_handling=token_handling,
            trace_id=trace_id,
            tool_name=tool_name,
            server_id=server_id,
            arguments=arguments,
            sandbox_fs_policy=self._sandbox.fs_policy,
            sandbox_net_policy=self._sandbox.net_policy,
        )
        return decision, receipt
