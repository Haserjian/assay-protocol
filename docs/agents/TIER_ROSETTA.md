# Tier Rosetta — crosswalk of existing proof-tier vocabularies

**Status:** reference / `[DESIGNED]` mappings — correspondences below are
`[INFERRED]` until ratified by each vocabulary's owner.
**Date:** 2026-06-11
**Seed law:** `assay-cross-surface-demo/docs/tier_axes_v1.md` (epistemic vs
receipt axes, non-collapse rule). This document extends that law
ecosystem-wide; it does not replace it.

## The core line

**Assay proof language is multi-axis. Do not collapse evidence strength,
carrier strength, capture fidelity, replay maturity, falsification status,
and settlement status into one universal ladder.**

Corollary: **no new ladders.** A new tier vocabulary may be introduced only as
a versioned amendment to an existing axis, never as a parallel ladder.

## The axes and their vocabularies (with sources)

| Axis | Question | Vocabulary | Source |
|---|---|---|---|
| Claim grounding (epistemic) | How well-grounded is the claim? | `P0 / P1 / P2 / P3` | `assay-cross-surface-demo/docs/tier_axes_v1.md` (from organism-schemas) |
| Claim grounding (kernel) | same axis, kernel dialect | `DRAFT / CHECKED / TOOL_VERIFIED / ADVERSARIAL / CONSTITUTIONAL` | `assay-toolkit/src/assay/epistemic_kernel.py::PROOF_TIERS` |
| Claim grounding (Loom) | same axis, Loom dialect | `C (Claim) / B (Core) / A (Court)` | `~/.claude/rules/loom-doctrine.md` |
| Evidence posture (preflight) | What evidence stands behind this prose claim? | `unsupported / inferred / witnessed / reproducible` | `assay-toolkit/docs/packets/CLAIM_PREFLIGHT_PACKET_TEMPLATE.md` |
| Receipt substrate | How tamper-resistant is the evidence carrier? | `none / simulated / core / court` | `tier_axes_v1.md`; CRS v0.1 |
| Capture fidelity | What was recorded? | `FULL / HASH_ONLY / SUMMARY_ONLY / OPAQUE_VENDOR_REF` | `open-agent-episode/schema` |
| Replay maturity | Can it be re-run, and how strictly? | `NONE / BEST_EFFORT / BOUNDED / DETERMINISTIC` | `open-agent-episode/schema` |
| Replay basis × comparator | What kind of replay produced the verdict? | `recorded_trace / live_reexecution` × comparator tier `A` | `RCE_V0_NORMATIVE_SPEC.md` §replay |
| Falsification status | Was disproof attempted? | `not_required / absent / named / executed_passed / executed_failed` | `assay-toolkit/src/assay/claim_verifier.py::FALSIFIER_STATUSES` |
| Claim support / settlement | What happened to the claim over time? | `ASSERTED / SUPPORTED / WEAKENED / CONTRADICTED / RETRACTED`; doc-claim statuses `implemented / designed / speculative / aspirational`; numeric-claim statuses `active / superseded / disputed / retired` | `epistemic_kernel.py::CLAIM_SUPPORT_STATUSES`; compact-doctrine; loom-doctrine |
| Institutional assurance | What assurance class did the ledger record? | `L0 / L1 / L2 / L3` — pinned 2026-06-15 | `assay-ledger/ledger.schema.json` (enum), sourced from `attestation.schema.json` |

## Grounding-axis crosswalk (all rows `[INFERRED]`, pending owner ratification)

| organism P-ladder | kernel | Loom | preflight posture |
|---|---|---|---|
| `P0` noise / insufficient | `DRAFT` | `C` (Claim) | `unsupported` |
| `P1` plausible / self-consistent | `CHECKED` | `C` (Claim) | `inferred` |
| `P2` tool-grounded | `TOOL_VERIFIED` | `B` (Core) | `witnessed` |
| `P3` externally verified + replay-validated | `ADVERSARIAL` / `CONSTITUTIONAL` | `A` (Court) | `reproducible` |

Caveats on this table:

- These are correspondences, not identities. Each dialect carries semantics
  the others lack (`CONSTITUTIONAL` implies governance binding; `A (Court)`
  implies receipt-substrate strength as well — see Fracture 2).
- The 2026-06-11 design thread's proposed `P0–P4` ladder is rejected as a
  vocabulary, but its semantics are already covered: thread-`P4`
  ("adversarially challenged") ≈ kernel `ADVERSARIAL` + falsifier
  `executed_passed`. Extending the organism P-ladder to P4 would require a
  versioned amendment to organism-schemas, not a new ladder — and the
  existing coverage means there is currently no need.

## Fractures found while building this crosswalk

1. **`proof_tier` name collision (live, CROSS-REPO ONLY).** Within
   `assay-cross-surface-demo` this is NOT a fracture: the
   `proof_tier`→`epistemic_tier` surface-rename is documented in
   `tier_axes_v1.md` and ladder-vocabulary disjointness is test-enforced
   (`tests/test_claim_boundary_artifact.py`, `EPISTEMIC ∩ RECEIPT == ∅`) —
   adjudicated 2026-06-12 against an independent audit. The fracture is
   strictly cross-repo: RCE spec receipt examples
   (`RCE_V0_NORMATIVE_SPEC.md`, repo-root) carry `proof_tier` with *receipt
   substrate* values (`"core"`). Same field name, different axis, different
   repos — and no test can reach across them. Resolution candidates: rename
   one, or pin a per-repo field registry. Until resolved, any cross-repo
   consumer reading `proof_tier` MUST check which dialect it is reading.
2. **Loom `A (Court)` vs receipt_tier `court`.** The shared word suggests the
   Loom ladder partially fuses epistemic strength with carrier strength.
   Mark `[NEEDS CHECK]` with Loom doctrine owner before any tooling maps
   them automatically.
3. **Ledger `assurance_level` — RESOLVED 2026-06-15.** Was a free string
   ("L0, L1, etc.") with no enum — a tier vocabulary with no defined members,
   coherence debt in the trust spine. Pinned to `[L0, L1, L2, L3]` in
   `assay-ledger` commit `8a1779b` (schema enum + enforced validator check +
   6 regression tests), sourced from the attestation contract
   (`assay-toolkit/src/assay/schemas/attestation.schema.json`). Adjacent
   finding, NOT resolved: the ledger's sibling `mode` field is still a free
   string anticipating "active", while the attestation contract pins `mode`
   to `shadow / enforced / breakglass` — a value-set divergence on a
   non-tier field. Flagged for follow-on reconciliation.
4. **Near-collision risk demonstrated.** The design thread independently
   minted `P0–P4` with different semantics under labels identical to the
   existing P-ladder (thread-`P1` "Observed" ≈ existing `P2`
   "tool-grounded"). Identical labels with shifted semantics are the most
   expensive form of tier drift; this rosetta exists to make that visible.

## Usage rules

1. Any doc, receipt, or buyer-facing artifact using a tier label MUST name
   the axis and source vocabulary (e.g., "epistemic_tier P2 per
   tier_axes_v1").
2. No consumer may collapse axes into a single scalar without an explicit,
   written mapping rule (inherited verbatim from `tier_axes_v1.md`).
3. Crosswalk rows above may be cited as `[INFERRED]` only. Promoting a row to
   `[KNOWN]` requires sign-off recorded next to the row with a date.
4. New tier words in any repo trigger a rosetta update in the same change.
