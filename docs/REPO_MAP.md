# Assay Protocol Repo Map

Canonical reference for how this repository fits into the Assay ecosystem.

## Repo Lineage

- `assay-protocol` is the public verification contract, specification, schemas, and conformance layer.
- `assay` is the core CLI and SDK for generating and verifying proof packs.
- `assay-verify-ts` is the independent TypeScript verifier.
- `assay-proof-gallery` hosts public specimen packs and the browser verifier.
- `assay-ledger` is an optional transparency anchor, not required for offline verification.
- `agentmesh` is an adjacent provenance and coordination system that can feed evidence into Assay.

## What Ships From Here

This repository defines the verification-facing shape of Assay proof packs:

- `SPEC.md` -- full protocol specification
- `schemas/` -- machine-readable schemas
- `reference/python_gateway/` -- reference gateway implementation
- `reference/python_membrane/` -- reference executor membrane implementation
- `conformance/` -- conformance framing and claims
- `MCP_MINIMUM_PROFILE.md` -- MCP gateway control profile
- `EXECUTOR_MEMBRANE_PROFILE.md` -- executor membrane profile
- `RCE_PROFILE.md` -- replay-constrained episode profile

This repo is not the main runtime repository and should not be treated as a
separate product surface from Assay. It is the portable evidence contract layer.
