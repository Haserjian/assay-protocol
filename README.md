# CSP Tool Safety Profile

Safety controls for AI agents using tools. Reference implementation + conformance tests.

**CSP** = Constitutional Safety Protocol (not Content Security Policy)

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

**Normative:**
| File | Purpose |
|------|---------|
| [SPEC.md](SPEC.md) | Full RFC-style specification |
| [MCP_MINIMUM_PROFILE.md](MCP_MINIMUM_PROFILE.md) | 9 MUSTs for MCP gateway conformance |

**Informative:**
| File | Purpose |
|------|---------|
| [FOR_HUMANS.md](FOR_HUMANS.md) | Plain-English explainer |
| [IMPLEMENTORS.md](IMPLEMENTORS.md) | Adoption checklists (Basic/Standard/Court-Grade) |
| [CONTROL_MAP.md](CONTROL_MAP.md) | MUST → Hook → Module → Test mapping |
| [MCP_GATEWAY_MAP.md](MCP_GATEWAY_MAP.md) | Enforcement hooks + code patterns |
| [REASON_CODES.md](REASON_CODES.md) | Canonical reason codes |
| [schemas/receipt.schema.json](schemas/receipt.schema.json) | JSON Schema for receipts |
| [conformance/](conformance/) | How to claim conformance |

**Strategic (CODE RED):**
| File | Purpose |
|------|---------|
| [CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md](CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md) | Open RFC for portable receipts (JCS, Ed25519, anchoring) |
| [ANTI_AGENT_MANIFESTO.md](ANTI_AGENT_MANIFESTO.md) | Positioning: "Agents are apps, governance is infrastructure" |

## Tooling

### csp-validate: Conformance Checker

```bash
# Validate receipts and generate report + badge
python scripts/csp_validate.py path/to/receipts/ -o report.json --badge badge.svg

# Output:
# - PASS/FAIL for 7 conformance checks
# - JSON report (optionally signed)
# - SVG badge for embedding
```

### crypto_core: Receipt Signing

```bash
# Generate Ed25519 keypair
python scripts/crypto_core.py keygen --key-id my-operator -o keys/

# Sign a receipt
python scripts/crypto_core.py sign receipt.json --key keys/my-operator.private.json

# Verify chain
python scripts/crypto_core.py verify r1.json r2.json r3.json --keys public_keys.json
```

> **Note:** Install `cryptography` for real Ed25519 signatures: `pip install cryptography`

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

## Conformance Tests (22 unit tests)

| ID | MUST | Assertion |
|----|------|-----------|
| AUTH-01/02 | 2 | Missing/invalid token denied |
| DISC-01/02/03 | 3 | Tool visibility filtered by principal |
| AUTHZ-01/02/03 | 4 | Unknown tool / no rule denied; permitted allowed |
| CRED-01/02/03/04 | 5 | No token passthrough; correct exchange |
| VAL-01/02/03/04 | 7 | Unknown fields / size / path traversal rejected |
| RCPT-01/02/03 | 9 | Every `tools/call` emits receipt; stored |
| INC-01/02/03 | 9 | Kill switch denies tool; deactivates |

See [CONTROL_MAP.md](CONTROL_MAP.md) for full test matrix.

## Design Partners

Building an MCP gateway, agent runtime, or tool-using AI? I help teams implement CSP.

**Available:**
- CSP Basic Pilot (2-3 days): CRITICAL blocking + receipts
- CSP Standard Pilot (1-2 weeks): Full 9 MUSTs + conformance tests
- Court-Grade Upgrade: Signed receipts + audit export

[Open an issue](https://github.com/Haserjian/csp-tool-safety-profile/issues) with label `design-partner`.

---

*Created by Tim B. Haserjian. Part of the Constitutional Safety Protocol (CSP-1.0) project.*
