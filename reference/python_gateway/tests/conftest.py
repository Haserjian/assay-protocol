"""Pytest fixtures for conformance tests."""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from csp_gateway.gateway import GatewayConfig, MCPGateway
from csp_gateway.types import TrustLevel


@pytest.fixture
def workspace(tmp_path):
    """Create a temporary workspace."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def gateway(workspace):
    """Create a configured gateway instance."""
    config = GatewayConfig(
        workspace=str(workspace),
        max_payload_bytes=10_000,
        network_allowlist=["api.example.com"],
    )
    gw = MCPGateway(config)

    # Configure trust levels
    gw.registry.configure_trust("server_a", TrustLevel.INTERNAL)
    gw.registry.configure_trust("server_b", TrustLevel.VERIFIED)

    # Register tools
    gw.registry.register("server_a", "tool_x", schema={"properties": {"input": {}}})
    gw.registry.register("server_a", "tool_y", schema={"properties": {"input": {}}})
    gw.registry.register("server_a", "fs_read", schema={"properties": {"path": {}}})
    gw.registry.register("server_a", "fs_write", schema={"properties": {"path": {}, "content": {}}})
    gw.registry.register("server_b", "tool_z", schema={"properties": {"data": {}}})

    # Add valid tokens
    gw.authn.add_valid_token("token_alice", {
        "sub": "alice",
        "actor_type": "user",
        "client_id": "client_1",
    })
    gw.authn.add_valid_token("token_bob", {
        "sub": "bob",
        "actor_type": "agent",
        "client_id": "client_2",
    })

    # Configure permissions
    # Alice can access tool_x, tool_y, fs_read
    gw.authz.grant("alice", ["tool_x", "tool_y", "fs_read"])
    # Bob can only access tool_z
    gw.authz.grant("bob", ["tool_z"])

    # Configure credentials
    gw.credentials.configure_vault("server_a", "vault_secret_a")
    gw.credentials.configure_exchange("server_b", audience="server_b")

    # Register schemas with preflight validator
    gw.preflight.register_schema("tool_x", {"properties": {"input": {}}})
    gw.preflight.register_schema("tool_y", {"properties": {"input": {}}})
    gw.preflight.register_schema("fs_read", {"properties": {"path": {}}})
    gw.preflight.register_schema("fs_write", {"properties": {"path": {}, "content": {}}})
    gw.preflight.register_schema("tool_z", {"properties": {"data": {}}})

    return gw


@pytest.fixture
def alice_token():
    return "token_alice"


@pytest.fixture
def bob_token():
    return "token_bob"


@pytest.fixture
def invalid_token():
    return "invalid_token_xyz"
