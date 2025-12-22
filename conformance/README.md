# Assay Conformance Testing

How to verify your MCP gateway conforms to Assay Protocol.

## Quick Check

Run the reference tests against your implementation:

```bash
# Using reference implementation as baseline
cd reference/python_gateway
pip install -e ".[dev]"
pytest tests/test_conformance.py -v
```

## Required Tests

Your gateway MUST pass all tests in the following categories:

| Category | Test IDs | MUST |
|----------|----------|------|
| Authentication | AUTH-01, AUTH-02 | 2 |
| Discovery | DISC-01, DISC-02 | 3 |
| Authorization | AUTHZ-01, AUTHZ-02 | 4 |
| Credentials | CRED-01, CRED-02 | 5 |
| Validation | VAL-01, VAL-02, VAL-03 | 7 |
| Receipts | RCPT-01 | 9 |
| Incident | INC-01 | 9 |

## Test Descriptions

### AUTH-01: Missing token denied
Request without authentication token returns `DENY_NO_AUTHN`.

### AUTH-02: Invalid token denied
Request with invalid token returns `DENY_NO_AUTHN`.

### DISC-01: Unpermitted tool excluded
Principal without permission to a tool does NOT see it in `tools/list`.

### DISC-02: Permitted tool included
Principal with permission to a tool sees it in `tools/list`.

### AUTHZ-01: Unknown tool denied
Request for non-existent tool returns `DENY_TOOL_NOT_FOUND`.

### AUTHZ-02: No matching rule denied
Request that matches no policy rule returns `DENY_NO_MATCHING_RULE`.

### CRED-01: No token passthrough
Upstream credential is NOT the same as client token.

### CRED-02: Correct audience
Exchanged token has correct `aud` for target server.

### VAL-01: Unknown fields rejected
Request with fields not in tool schema returns `DENY_UNKNOWN_FIELDS`.

### VAL-02: Payload too large rejected
Request exceeding size limit returns `DENY_PAYLOAD_TOO_LARGE`.

### VAL-03: Path traversal rejected
File tool request with path outside workspace returns `DENY_PATH_TRAVERSAL`.

### RCPT-01: Receipt emitted
Every request emits a receipt with required fields.

### INC-01: Kill switch works
Tool disabled by kill switch returns `DENY_KILL_SWITCH`.

## Integration Tests (Optional)

These require container/network infrastructure:

| Test ID | Description |
|---------|-------------|
| TLS-01 | Non-TLS connections rejected |
| NET-01 | Non-allowlisted egress blocked |
| SAND-01 | Write outside workspace fails at OS level |

## Claiming Conformance

To claim Assay conformance:

1. Run all required tests
2. Document any N/A items (e.g., MUST 6 if not doing OAuth proxying)
3. Generate conformance report

```bash
pytest tests/test_conformance.py -v --tb=short > conformance_report.txt
```

Include in your documentation:
- Assay version: `1.0.0-rc1`
- MCP Minimum Profile version: `0.1`
- Test date and commit hash
- Any N/A items with rationale
