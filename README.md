# Assay Protocol

> Assay Protocol defines the verification contract for MCP gateways in the [Assay](https://github.com/Haserjian/assay) ecosystem.

![Tests](https://img.shields.io/badge/tests-52%20passed-brightgreen)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-blue)](LICENSE)

Assay Protocol is the spec and reference implementation for MCP gateways that can prove what tool-using AI systems did. It defines deny-by-default controls, tamper-evident receipts, and incident-response hooks for gateway-layer enforcement.

It also hosts companion normative profiles when replay-verifiable Assay artifacts need a stable protocol home.

> *"Agents talk via MCP. Agents prove via Assay."*

**What this is:** A specification and reference implementation for MCP gateway conformance - the gateway-side control profile for deny-by-default tool use, filtered discovery, validation boundaries, receipts, and incident response - plus companion replay profiles that define portable evidence contracts.

**What this isn't:** An agent framework. If you want to build agents, look elsewhere. If you want to prove what your agents did, you're home.

**Use this repo when:** you are building or auditing an MCP gateway and need to know what controls, receipts, and conformance hooks are required.

> **Spec status:** v1.0.0-rc1 — **Release Candidate, pre-release.** Dated 2025-12-10. The contract may change before 1.0.0. See [SPEC.md](./SPEC.md) for the normative version.

**Companion Profile:** RCE v0.1 draft ([RCE_PROFILE.md](RCE_PROFILE.md))

## Repo Map

- `assay` = core evidence product/runtime
- `assay-protocol` = normative protocol + conformance/spec layer
- `assay-verify-action`, `assay-ledger`, `assay-scorecard`, `assay-agent-demo` = ecosystem satellites
- `agentmesh` = adjacent provenance/coordination engine
- Local folder `csp-tool-safety-profile` is legacy naming; the canonical remote identity is `assay-protocol`

See [docs/REPO_MAP.md](docs/REPO_MAP.md) for the repo-local map.

## Quick Start

Fastest path: run the reference conformance tests, then read `FOR_HUMANS.md` if you want the plain-English version before diving into the spec.

```bash
cd reference/python_gateway
python3 -m venv .venv && source .venv/bin/activate   # Windows: py -m venv .venv && .venv\Scripts\activate
pip install pytest
PYTHONPATH=src pytest tests/ -v

# 52 tests, ~0.05s
```

## What You Get

- **Proof when things go wrong:** Every tool action gets a receipt with timestamp, decision, and hash
- **Deny-by-default protection:** Nothing executes without explicit policy approval
- **Incident response:** Kill switch to disable compromised tools instantly
- **Auditable trail:** Signed receipts with hash chains (Ed25519, JCS-canonical)

It is not a general agent framework and it is not the buyer-facing Assay artifact path.

## Documents

**Normative:**

| File | Purpose |
|------|---------|
| [SPEC.md](SPEC.md) | Full RFC-style specification |
| [MCP_MINIMUM_PROFILE.md](MCP_MINIMUM_PROFILE.md) | 9 MUSTs for MCP gateway conformance |
| [RCE_PROFILE.md](RCE_PROFILE.md) | Replay-Constrained Episode profile for replay-verifiable work units |
| [schemas/rce_episode_contract.schema.json](schemas/rce_episode_contract.schema.json) | Machine-readable Episode Contract schema for RCE |

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
| [CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md](CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md) | Receipt format spec (JCS, Ed25519, anchoring) |

## Reference Implementation

```text
reference/python_gateway/
├── src/assay_gateway/
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
    ├── test_conformance.py  # 22 conformance tests (9 MUSTs)
    └── test_pccap.py        # 30 PCCap capability tests
```

## Tooling

### assay-validate: Conformance Checker

```bash
# Validate receipts and generate report + badge
python scripts/assay_validate.py path/to/receipts/ -o report.json --badge badge.svg

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

## Who This Is For

- **Security engineers** who need to prove agent behavior to their CISO
- **Platform teams** building tool-using AI that needs guardrails
- **Compliance teams** preparing for EU AI Act and SOC 2 AI audit requirements

## Related Repos


| Repo | Purpose |
|------|---------|
| [assay](https://github.com/Haserjian/assay) | Core CLI + SDK — evidence compiler for AI systems |
| [assay-verify-action](https://github.com/Haserjian/assay-verify-action) | GitHub Action for CI evidence verification |
| [assay-ledger](https://github.com/Haserjian/assay-ledger) | Public transparency ledger |
| [agentmesh](https://github.com/Haserjian/agentmesh) | Multi-agent coordination and provenance |

## Links

- [assay-ai on PyPI](https://pypi.org/project/assay-ai/)
- [Assay source](https://github.com/Haserjian/assay)
- [Assay Verify Action](https://github.com/Haserjian/assay-verify-action)

---

*Part of the [Assay](https://github.com/Haserjian/assay) ecosystem. Created by Tim B. Haserjian.*

## License

CC BY 4.0 (specification text), MIT (reference implementation code).
