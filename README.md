# CSP Tool Safety Profile

Safety controls for AI agents using tools. Reference implementation + conformance tests.

**Spec:** v1.0.0-rc1 | **License:** CC BY 4.0 (text), MIT (code)

## Quick Start

```bash
# Run conformance tests
cd reference/python_gateway
python3 -m venv .venv && source .venv/bin/activate
pip install pytest
PYTHONPATH=src pytest tests/ -v

# 22 tests, ~0.04s
```

## What This Is

A spec + reference implementation for MCP gateways that:
- Filter `tools/list` by principal permissions (MUST 3)
- Deny-by-default on `tools/call` (MUST 4)
- Never passthrough client tokens upstream (MUST 5)
- Validate schemas, size limits, path boundaries (MUST 7)
- Emit receipts for every decision (MUST 9)
- Kill switch for incident response (MUST 9)

## Documents

| File | Purpose |
|------|---------|
| [SPEC.md](SPEC.md) | Full RFC-style specification |
| [MCP_MINIMUM_PROFILE.md](MCP_MINIMUM_PROFILE.md) | 9 MUSTs for MCP gateway conformance |
| [CONTROL_MAP.md](CONTROL_MAP.md) | MUST → Hook → Module → Test mapping |
| [REASON_CODES.md](REASON_CODES.md) | Canonical reason codes |
| [conformance/](conformance/) | How to claim conformance |

## Reference Implementation

```
reference/python_gateway/
├── src/csp_gateway/
│   ├── gateway.py      # Main orchestration
│   ├── types.py        # Core types + enums
│   ├── registry.py     # MUST 1: Tool inventory
│   ├── authn.py        # MUST 2: Authentication
│   ├── authz.py        # MUST 3+4: Discovery + AuthZ
│   ├── credentials.py  # MUST 5: No token passthrough
│   ├── preflight.py    # MUST 7: Validation
│   ├── sandbox.py      # MUST 8: Boundaries
│   ├── receipts.py     # MUST 9: Receipts
│   └── incident.py     # MUST 9: Kill switch
└── tests/
    └── test_conformance.py  # 22 conformance tests
```

## Conformance Tests

| ID | MUST | Assertion |
|----|------|-----------|
| AUTH-01 | 2 | Missing token denied |
| AUTH-02 | 2 | Invalid token denied |
| DISC-01 | 3 | Unpermitted tool excluded from list |
| DISC-02 | 3 | Permitted tool included in list |
| AUTHZ-01 | 4 | Unknown tool denied |
| AUTHZ-02 | 4 | No matching rule denied |
| CRED-01 | 5 | Upstream token != client token |
| CRED-02 | 5 | Correct audience on exchanged token |
| VAL-01 | 7 | Unknown fields rejected |
| VAL-02 | 7 | Oversized payload rejected |
| VAL-03 | 7 | Path traversal rejected |
| RCPT-01 | 9 | Every request emits receipt |
| INC-01 | 9 | Kill switch denies tool |

## Design Partners

Building an MCP gateway, agent runtime, or tool-using AI? I help teams implement CSP.

**Available:**
- CSP Basic Pilot (2-3 days): CRITICAL blocking + receipts
- CSP Standard Pilot (1-2 weeks): Full 9 MUSTs + conformance tests
- Court-Grade Upgrade: Signed receipts + audit export

[Open an issue](https://github.com/Haserjian/csp-tool-safety-profile/issues) with label `design-partner`.

---

*Created by Tim B. Haserjian. Part of the Constitutional Safety Protocol (CSP-1.0) project.*
