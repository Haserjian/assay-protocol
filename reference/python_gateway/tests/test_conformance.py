"""CSP MCP Gateway Conformance Tests.

Test IDs from CONTROL_MAP.md:
- AUTH-01, AUTH-02: Authentication
- DISC-01, DISC-02: Discovery filtering
- AUTHZ-01, AUTHZ-02: Runtime authorization
- CRED-01, CRED-02: Credential boundary
- VAL-01, VAL-02, VAL-03: Preflight validation
- RCPT-01: Receipt emission
- INC-01: Kill switch
"""

from csp_gateway.types import DecisionResult, ReasonCode


class TestAuthentication:
    """MUST 2: AuthN on every request."""

    def test_auth_01_missing_token_denied(self, gateway):
        """AUTH-01: Missing token returns DENY_NO_AUTHN."""
        tools, decision, receipt = gateway.handle_tools_list(token=None)

        assert tools is None
        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_NO_AUTHN in decision.reason_codes

    def test_auth_02_invalid_token_denied(self, gateway, invalid_token):
        """AUTH-02: Invalid token returns DENY_NO_AUTHN."""
        tools, decision, receipt = gateway.handle_tools_list(token=invalid_token)

        assert tools is None
        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_NO_AUTHN in decision.reason_codes


class TestDiscovery:
    """MUST 3: Identity-bound tool discovery."""

    def test_disc_01_unpermitted_tool_excluded(self, gateway, alice_token):
        """DISC-01: Unpermitted tool excluded from tools/list."""
        tools, decision, receipt = gateway.handle_tools_list(token=alice_token)

        assert decision.result == DecisionResult.ALLOW
        tool_names = [t.tool_name for t in tools]

        # Alice has permission for tool_x, tool_y, fs_read
        # tool_z is NOT in her permissions
        assert "tool_z" not in tool_names

    def test_disc_02_permitted_tool_included(self, gateway, alice_token):
        """DISC-02: Permitted tool included in tools/list."""
        tools, decision, receipt = gateway.handle_tools_list(token=alice_token)

        assert decision.result == DecisionResult.ALLOW
        tool_names = [t.tool_name for t in tools]

        # Alice has permission for tool_x
        assert "tool_x" in tool_names

    def test_disc_different_principals_see_different_tools(self, gateway, alice_token, bob_token):
        """Different principals see different tool sets."""
        alice_tools, _, _ = gateway.handle_tools_list(token=alice_token)
        bob_tools, _, _ = gateway.handle_tools_list(token=bob_token)

        alice_names = {t.tool_name for t in alice_tools}
        bob_names = {t.tool_name for t in bob_tools}

        # Alice sees tool_x, tool_y, fs_read
        assert "tool_x" in alice_names
        assert "tool_z" not in alice_names

        # Bob sees tool_z only
        assert "tool_z" in bob_names
        assert "tool_x" not in bob_names


class TestAuthorization:
    """MUST 4: Runtime AuthZ per invocation."""

    def test_authz_01_unknown_tool_denied(self, gateway, alice_token):
        """AUTHZ-01: Unknown tool returns DENY_TOOL_NOT_FOUND."""
        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="nonexistent_tool",
            arguments={},
        )

        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_TOOL_NOT_FOUND in decision.reason_codes

    def test_authz_02_no_matching_rule_denied(self, gateway, bob_token):
        """AUTHZ-02: No matching rule returns DENY_NO_MATCHING_RULE."""
        # Bob tries to call tool_x (which he has no permission for)
        decision, receipt = gateway.handle_tools_call(
            token=bob_token,
            tool_name="tool_x",
            arguments={"input": "test"},
        )

        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_NO_MATCHING_RULE in decision.reason_codes

    def test_authz_permitted_tool_allowed(self, gateway, alice_token):
        """Permitted tool is allowed."""
        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_x",
            arguments={"input": "test"},
        )

        assert decision.result == DecisionResult.ALLOW


class TestCredentials:
    """MUST 5: Credential boundary (no token passthrough)."""

    def test_cred_01_upstream_token_not_client_token(self, gateway, alice_token):
        """CRED-01: Upstream token != client token."""
        # Configure server with exchange
        gateway.credentials.configure_exchange("test_server", audience="test_server")

        credential, handling = gateway.credentials.get_upstream_credential(
            alice_token, "test_server"
        )

        # Upstream token should be different from client token
        assert credential.token != alice_token
        assert credential.token.startswith("exchanged:")
        assert handling.passthrough_detected is False

    def test_cred_02_upstream_token_has_correct_audience(self, gateway, alice_token):
        """CRED-02: Upstream token has correct audience."""
        credential, handling = gateway.credentials.get_upstream_credential(
            alice_token, "server_b"
        )

        assert credential.audience == "server_b"
        assert handling.audience == "server_b"

    def test_cred_passthrough_blocked(self, gateway, alice_token):
        """Passthrough attempt is blocked."""
        # Try to get credential for unconfigured server
        credential, handling = gateway.credentials.get_upstream_credential(
            alice_token, "unconfigured_server"
        )

        assert credential is None
        assert handling.passthrough_detected is True

    def test_cred_passthrough_blocked_in_request(self, gateway, alice_token):
        """Passthrough blocked during tools/call returns DENY_PASSTHROUGH_BLOCKED."""
        # Register a tool on unconfigured server
        gateway.registry.register("unconfigured_server", "dangerous_tool")
        gateway.authz.grant("alice", ["dangerous_tool"])

        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="dangerous_tool",
            arguments={},
            server_id="unconfigured_server",
        )

        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_PASSTHROUGH_BLOCKED in decision.reason_codes
        assert receipt.token_handling.passthrough_detected is True


class TestValidation:
    """MUST 7: Preflight validation."""

    def test_val_01_unknown_fields_rejected(self, gateway, alice_token):
        """VAL-01: Unknown fields rejected."""
        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_x",
            arguments={"input": "test", "unknown_field": "bad"},
        )

        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_UNKNOWN_FIELDS in decision.reason_codes

    def test_val_02_payload_too_large_rejected(self, gateway, alice_token):
        """VAL-02: Oversized payload rejected."""
        # Gateway configured with 10KB limit
        large_payload = {"input": "x" * 20_000}

        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_x",
            arguments=large_payload,
        )

        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_PAYLOAD_TOO_LARGE in decision.reason_codes

    def test_val_03_path_traversal_rejected(self, gateway, alice_token):
        """VAL-03: Path traversal rejected."""
        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="fs_read",
            arguments={"path": "../../../etc/passwd"},
        )

        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_PATH_TRAVERSAL in decision.reason_codes

    def test_val_valid_path_allowed(self, gateway, alice_token, workspace):
        """Valid workspace path is allowed."""
        # Create a file in workspace
        test_file = workspace / "test.txt"
        test_file.write_text("hello")

        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="fs_read",
            arguments={"path": "test.txt"},
        )

        assert decision.result == DecisionResult.ALLOW


class TestReceipts:
    """MUST 9: Audit receipts."""

    def test_rcpt_01_every_request_emits_receipt(self, gateway, alice_token):
        """RCPT-01: Every request emits a receipt with required fields."""
        gateway.receipts.clear()

        # Make a request
        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_x",
            arguments={"input": "test"},
        )

        # Verify receipt
        assert receipt is not None
        assert receipt.ts is not None
        assert receipt.receipt_id is not None
        assert receipt.trace_id is not None
        assert receipt.principal is not None
        assert receipt.principal.sub == "alice"
        assert receipt.decision is not None
        assert receipt.decision.result == DecisionResult.ALLOW
        assert receipt.token_handling is not None
        assert receipt.token_handling.passthrough_detected is False

    def test_rcpt_deny_emits_receipt(self, gateway, invalid_token):
        """Denied requests also emit receipts."""
        gateway.receipts.clear()

        decision, receipt = gateway.handle_tools_call(
            token=invalid_token,
            tool_name="tool_x",
            arguments={},
        )

        assert receipt is not None
        assert receipt.decision.result == DecisionResult.DENY

    def test_rcpt_stored(self, gateway, alice_token):
        """Receipts are stored and retrievable."""
        gateway.receipts.clear()

        gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_x",
            arguments={"input": "1"},
        )
        gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_y",
            arguments={"input": "2"},
        )

        receipts = gateway.receipts.get_receipts()
        assert len(receipts) == 2


class TestIncident:
    """MUST 9: Incident response."""

    def test_inc_01_kill_switch_denies_tool(self, gateway, alice_token):
        """INC-01: Kill switch denies with DENY_KILL_SWITCH."""
        # Activate kill switch for tool_x
        gateway.authz.activate_kill_switch(["tool_x"])

        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_x",
            arguments={"input": "test"},
        )

        assert decision.result == DecisionResult.DENY
        assert ReasonCode.DENY_KILL_SWITCH in decision.reason_codes

    def test_inc_kill_switch_other_tools_unaffected(self, gateway, alice_token):
        """Kill switch only affects specified tools."""
        gateway.authz.activate_kill_switch(["tool_x"])

        # tool_y should still work
        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_y",
            arguments={"input": "test"},
        )

        assert decision.result == DecisionResult.ALLOW

    def test_inc_kill_switch_deactivate(self, gateway, alice_token):
        """Kill switch can be deactivated."""
        gateway.authz.activate_kill_switch(["tool_x"])
        gateway.authz.deactivate_kill_switch(["tool_x"])

        decision, receipt = gateway.handle_tools_call(
            token=alice_token,
            tool_name="tool_x",
            arguments={"input": "test"},
        )

        assert decision.result == DecisionResult.ALLOW
