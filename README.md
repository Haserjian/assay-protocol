# Assay Protocol

**Portable, independently verifiable evidence packs for AI decisions.**

Assay turns AI activity into signed proof packs another party can verify offline.
That matters when you need to answer boring, expensive questions:

- What happened?
- What policy ran?
- Was the evidence changed after the fact?
- Can an assessor or buyer verify it without trusting our server?

This repo is the public verification contract and documentation layer for Assay evidence packs.

It is **not** an agent framework.
It is **not** a runtime governance platform.
It is **not** a claim that cryptography replaces compliance work.

It is the part that makes evidence portable.

## Start Here

- **Need the commercial shape first?** Read [Article 11 / Annex IV working map](ARTICLE11_ANNEXIV_MAPPING.md)
- **Want to verify a specimen pack right now?** Try [assay-agent-demo](https://github.com/Haserjian/assay-agent-demo)
- **Want a browser verifier?** Use the [proof gallery verifier](https://haserjian.github.io/assay-proof-gallery/verify.html)
- **Need the formal spec?** Read [SPEC.md](SPEC.md)

> **Spec status:** v1.0.0-rc1 — **Release Candidate, pre-release.** Dated 2025-12-10. The contract may change before 1.0.0. See [SPEC.md](./SPEC.md) for the normative version.

## What Assay Evidence Packs Give You

- **Tamper evidence**: change one byte after signing and verification fails
- **Offline verification**: no vendor server required
- **Signer identity**: the pack carries the public key needed to verify the signature
- **Execution context**: run identifiers, timestamps, receipt counts, and policy hashes travel with the pack
- **Human-readable summary**: the same pack includes a verifier transcript a reviewer can read without parsing JSON

## What This Repo Covers

This repo defines the verification-facing shape of an Assay proof pack:

- signed manifest
- receipt bundle
- verification report
- verification transcript
- schema and canonicalization expectations

For regulated buyers, auditors, and assessors, the key point is simple:

> Assay does not ask you to trust our dashboard.
> It gives you an artifact you can verify yourself.

## What It Does Not Claim

Assay proof packs do **not** by themselves prove:

- that the signer was honest
- that every system action was instrumented
- that the model output was correct, fair, or safe
- that a proof pack alone satisfies all of Article 11 / Annex IV

Those boundaries matter. Assay is strongest as **supporting technical evidence** inside a wider compliance, audit, or incident workflow.

## Evidence Pack Anatomy

Typical pack contents:

```text
proof_pack/
  receipt_pack.jsonl
  verify_report.json
  verify_transcript.md
  pack_manifest.json
  pack_signature.sig
```

At minimum, these files let a third party answer:

- did the evidence change?
- who signed it?
- when was it created?
- how many receipts are in scope?
- did verification pass?

## Where Assay Helps

Assay is useful anywhere another party needs more than logs:

- **regulated sales**: vendor packets attached to security, compliance, or trust reviews
- **audits**: technical evidence that can be checked outside the operator's environment
- **incidents**: a stable, signed packet that survives post-hoc scrutiny
- **internal assurance**: proving policy execution and retaining honest failures

## Documents

### Buyer- and Assessor-Facing

| File | Purpose |
|------|---------|
| [ARTICLE11_ANNEXIV_MAPPING.md](ARTICLE11_ANNEXIV_MAPPING.md) | Working map from Assay proof-pack artifacts to EU AI Act Article 11 / Annex IV expectations |

### Normative And Implementor Docs

| File | Purpose |
|------|---------|
| [SPEC.md](SPEC.md) | Full protocol specification |
| [FOR_HUMANS.md](FOR_HUMANS.md) | Plain-English explainer for the broader protocol surface |
| [CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md](CONSTITUTIONAL_RECEIPT_STANDARD_v0.1.md) | Receipt-format notes for signed evidence artifacts |
| [schemas/](schemas/) | Machine-readable schemas |
| [reference/python_gateway](reference/python_gateway) | Reference implementation |
| [MCP_MINIMUM_PROFILE.md](MCP_MINIMUM_PROFILE.md) | MCP gateway control profile |
| [EXECUTOR_MEMBRANE_PROFILE.md](EXECUTOR_MEMBRANE_PROFILE.md) | Executor membrane profile |
| [RCE_PROFILE.md](RCE_PROFILE.md) | Replay-constrained episode profile |
| [CONTROL_MAP.md](CONTROL_MAP.md) | MUST-to-hook mapping |
| [MCP_GATEWAY_MAP.md](MCP_GATEWAY_MAP.md) | Gateway enforcement hooks and code patterns |

## Quick Technical Start

If you want to exercise the reference implementation:

```bash
cd reference/python_gateway
python3 -m venv .venv && source .venv/bin/activate
pip install pytest
PYTHONPATH=src pytest tests/ -v
```

If you want to verify a real pack:

```bash
pipx install assay-ai
assay verify-pack proof_pack/
```

## Related Repos

| Repo | Purpose |
|------|---------|
| [assay](https://github.com/Haserjian/assay) | Core CLI and SDK for generating and verifying proof packs |
| [assay-verify-ts](https://github.com/Haserjian/assay-verify-ts) | Independent TypeScript verifier |
| [assay-proof-gallery](https://github.com/Haserjian/assay-proof-gallery) | Public specimen packs and browser verifier |
| [assay-ledger](https://github.com/Haserjian/assay-ledger) | Optional transparency anchor, not required for offline verification |

## License

CC BY 4.0 for specification text. MIT for reference implementation code.
