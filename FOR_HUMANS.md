# Assay Protocol In Plain English

This file is the short explanation of what Assay Protocol is for.

> **Status: Release Candidate.** This guide describes Assay Protocol v1.0.0-rc1 (dated 2025-12-10). The specification is pre-release; the contract may change before 1.0.0. See [SPEC.md](./SPEC.md) for the normative version.

---

If you only need one sentence, use this:

> Assay Protocol defines the portable evidence shape that lets another party verify an AI decision packet offline.

## What problem does it solve?

Most AI systems already have logs, traces, or dashboards.
Those are useful, but they still require the reviewer to trust the operator's system.

Assay focuses on a narrower problem:

- package the evidence
- sign the package
- make tampering visible
- let another party verify it without calling back to the operator

## What does that mean in practice?

An Assay proof pack usually gives a reviewer:

- a signed manifest
- a receipt bundle
- a machine-readable verification result
- a human-readable verification transcript
- the public key needed for offline verification

If one byte changes after signing, verification fails.

## What is it good for?

Assay is strongest in workflows where another party needs technical evidence:

- vendor diligence
- audit review
- regulator response supplements
- incident preservation
- validation and test evidence

## What it does not do by itself

Assay does **not** replace the rest of your compliance or technical documentation.

It does **not** by itself prove:

- model correctness
- dataset provenance
- fairness or bias performance
- completeness of instrumentation
- signer honesty
- full legal compliance

It is best understood as **supporting technical evidence inside a wider packet**.

## If you need more than this page

- Start with [README.md](README.md)
- For the Article 11 / Annex IV working map, read [ARTICLE11_ANNEXIV_MAPPING.md](ARTICLE11_ANNEXIV_MAPPING.md)
- For the normative details, read [SPEC.md](SPEC.md)
- For schemas and implementor details, see [schemas/](schemas/) and [reference/python_gateway](reference/python_gateway)
