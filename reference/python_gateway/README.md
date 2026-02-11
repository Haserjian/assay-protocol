# Assay MCP Gateway Reference Implementation

Reference-quality Python implementation of Assay Protocol for MCP gateways.

**Status:** Reference implementation for conformance testing. Not production-hardened.

## Quick Start

```bash
cd reference/python_gateway

# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"

# Run conformance tests
pytest
```

## What This Implements

| MUST | Module | Description |
|------|--------|-------------|
| 1 | `registry.py` | Tool inventory + trust/risk classification |
| 2 | `authn.py` | Token verification (stub for testing) |
| 3 | `authz.py` | Identity-bound `tools/list` filtering |
| 4 | `authz.py` | Deny-by-default runtime authorization |
| 5 | `credentials.py` | Credential boundary (no passthrough) |
| 7 | `preflight.py` | Schema validation, size limits, path checks |
| 8 | `sandbox.py` | Workspace path boundary |
| 9 | `receipts.py`, `incident.py` | Receipt emission + kill switch |

## PCCap (CRITICAL Action Capabilities)

`csp_gateway.pccap` adds signed, scoped, expiring capability tokens for
high-risk actions that require explicit approval.

- Signature validation (integrity + principal binding)
- TTL expiry enforcement
- Scope enforcement (tool/args/path)
- Single-use replay protection (default-on)

Threat model notes: `docs/PCCAP_THREAT_MODEL.md`

## Conformance Tests

Tests in `tests/test_conformance.py` implement the test matrix from `CONTROL_MAP.md`:

```
AUTH-01, AUTH-02  - Authentication
DISC-01, DISC-02  - Discovery filtering
AUTHZ-01, AUTHZ-02 - Runtime authorization
CRED-01, CRED-02  - Credential boundary
VAL-01, VAL-02, VAL-03 - Preflight validation
RCPT-01 - Receipt emission
INC-01 - Kill switch
```

## Limitations

This is reference code, not production:

- AuthN uses in-memory token map (use proper JWT in production)
- Token exchange is simulated (implement RFC 8693 in production)
- Network isolation is documented but not enforced in-process
- No TLS termination (handled by infrastructure)

## Usage Example

```python
from assay_gateway.gateway import MCPGateway, GatewayConfig
from assay_gateway.types import TrustLevel

# Create gateway
config = GatewayConfig(
    workspace="/tmp/workspace",
    max_payload_bytes=1_000_000,
    network_allowlist=["api.example.com"],
)
gateway = MCPGateway(config)

# Register tools
gateway.registry.configure_trust("my_server", TrustLevel.VERIFIED)
gateway.registry.register("my_server", "my_tool")

# Configure auth
gateway.authn.add_valid_token("test_token", {"sub": "user1", "actor_type": "user"})

# Configure permissions
gateway.authz.grant("user1", ["my_tool"])

# Configure credentials
gateway.credentials.configure_vault("my_server", "vault_secret")

# Handle request
decision, receipt = gateway.handle_tools_call(
    token="test_token",
    tool_name="my_tool",
    arguments={"input": "hello"},
    server_id="my_server",
)
```

## See Also

- [SPEC.md](../../SPEC.md) - Full specification
- [MCP_MINIMUM_PROFILE.md](../../MCP_MINIMUM_PROFILE.md) - 9 MUSTs
- [CONTROL_MAP.md](../../CONTROL_MAP.md) - Enforcement mapping
