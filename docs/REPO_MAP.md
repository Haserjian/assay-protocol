# Assay Protocol Repo Map

Canonical reference for what lives where and how this repo fits into the
Assay ecosystem.

## Repo Lineage

- `assay` = core evidence product/runtime
- `assay-protocol` = normative protocol + conformance/spec layer
- `assay-verify-action`, `assay-ledger`, `assay-scorecard`, `assay-agent-demo` = ecosystem satellites
- `agentmesh` = adjacent provenance/coordination engine

## What Ships From Here

### Haserjian/assay-protocol (this repo)

The protocol/spec layer. This repo defines the gateway conformance rules and
receipt contracts:

- `SPEC.md` -- normative Assay Protocol
- `MCP_MINIMUM_PROFILE.md` -- minimum conformance profile
- `CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md` -- portable receipt format
- `reference/python_gateway/` -- reference gateway implementation
- `conformance/` -- conformance framing and claims

### Haserjian/assay

Core CLI and SDK. It is the product/runtime layer that generates and verifies
evidence.

### Haserjian/agentmesh

Provenance and coordination system. It tracks claims, episodes, and lineage
and can feed evidence into Assay.

## Naming Note

- Local folder `csp-tool-safety-profile` is legacy naming
- Remote/canonical identity is `assay-protocol`
- Treat this repo as the spec/conformance layer, not the main implementation repo
