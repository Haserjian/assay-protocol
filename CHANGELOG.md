# Changelog

> Human summary. Agents ingest structured schemas for details.

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial Constitutional Safety Protocol (CSP) specification
- Receipt schema (JSON Schema Draft 2020-12) at `schemas/receipt.schema.json`
- Python reference implementation (`reference/python_gateway/`)
- Conformance test suite (22 tests)

### Specification Highlights
- **Deny-by-default policies**: All actions require explicit authorization
- **Tamper-evident receipts**: Ed25519 signed, JCS canonicalized
- **Kill switches**: Emergency action termination capability
- **Amendment pipeline**: 5-receipt law-change episodes
- **Guardian verdicts**: ALLOW/DENY/ESCALATE decision framework

### Receipt Types Defined
- `AgentActionReceipt` - Tool action attempted
- `RefusalReceipt` - Action blocked with reason and amendment cited
- `ToolPlanReceipt` - Planned actions with steps
- `GuardianVerdictReceipt` - Verdict, plan_hash, rationale
- `EmergencyOverrideReceipt` - Human override with justification
- `InvariantStressReceipt` - Override pattern exceeded threshold
- `ActionCheckpointReceipt` - Post-action state with rollback info

### Guardian MUSTs (Constitutional Requirements)
1. Receipts MUST be signed (Ed25519)
2. Hash chain MUST be continuous
3. Kill switches MUST be immediate
4. Dignity floor MUST be enforced (Genesis: 0.15)
5. Policy hash MUST bind plan to verdict
6. Overrides MUST trigger amendment review (3+ in 30 days)
7. All verdicts MUST be ALLOW, DENY, or ESCALATE

---

## [0.1.0] - 2026-02-04

### Added
- Initial repository setup
- SPEC.md with Constitutional Safety Protocol specification
- Reference Python gateway implementation
- JSON Schema for receipts
- GitHub Actions CI workflow
- Conformance test suite

### Notes
- This is the "thin wedge" candidate for the Assay Protocol
- Designed for framework-agnostic agent tool safety
- Compatible with LangChain, CrewAI, AutoGen, and other agent frameworks
