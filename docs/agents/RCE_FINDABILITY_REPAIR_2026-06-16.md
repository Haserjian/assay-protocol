# RCE Findability Repair — 2026-06-16

**Type:** incident / repair note (historical record).
**Repos touched:** `assay-protocol`, `assay-ledger`, `founder-ops-private`.
**Status:** closed — all fixes landed on the respective `main` branches via PR.

---

## Symptom

Two agent sessions running on different machines disagreed about whether
`RCE_V0_NORMATIVE_SPEC.md` existed. One session ran an AUDIT scoped to git
repositories and concluded the spec did **not** exist; another, reading the
filesystem directly, found it (43,839 bytes) and could quote and hash it. An
existence claim about a 43 KB file proved unresolvable by argument and was
settled only by `path + bytes + sha256`.

## Root cause

The RCE normative spec and three related doctrine documents were **untracked
loose files** in the home directory:

- `~/RCE_V0_NORMATIVE_SPEC.md`
- `~/RCE_BOUNDARY_AMENDMENT_V0.md`
- `~/docs/agents/TIER_ROSETTA.md`
- `~/docs/agents/MOLT_PROTOCOL_V0.md`

Neither `~` nor `~/docs/agents` is a git repository, so a repo-rooted session
could not see them and they did not sync across hosts. A divergent, **older**
tracked copy of the spec also existed in
`founder-ops-private/docs/m2-handoff-20260407/` (715 vs 716 lines), so drift
was already real.

Two adjacent defects surfaced while fixing the above, both in the
`assay-ledger` trust spine: `assurance_level` was a tier field with **no
defined member set** (a grade with no grades), and the sibling `mode` field
was likewise unpinned and value-divergent from the attestation contract.

## Fix

1. **Relocation — `assay-protocol`.** Moved the four docs into version
   control: spec and boundary amendment at repo root (beside `RCE_PROFILE.md`,
   which remains *implementation authority* — the spec is *design provenance*;
   the profile wins on divergence); rosetta and molt under `docs/agents/`.
   Layout chosen so the docs' repo-relative cross-references resolve from repo
   root; fixed one stale `~/` self-reference in the rosetta. Replaced the loose
   `~` originals with redirect stubs to close the drift vector.
   Commits `20fbf8c` (relocation) and `47630a1` (rosetta follow-up).

2. **Ledger enum pins — `assay-ledger`.** Pinned `assurance_level` to
   `[L0, L1, L2, L3]` in both the schema and the validator. The validator does
   manual field checks and does **not** load the schema, so the validator
   check — not the schema enum — is the enforcing surface. Values sourced from
   `assay-toolkit/src/assay/schemas/attestation.schema.json`; six regression
   tests added. `mode` subsequently pinned to `[shadow, enforced, breakglass]`
   the same way. Landed via PR #23 (`assay-ledger` commits `26f93ff`,
   `1296ead`, `e72c5fe`).

3. **Duplicate retirement — `founder-ops-private`.** Retired the divergent
   older handoff copy of the spec into a canonical-location stub pointing at
   `assay-protocol`. Commit `440c628`.

History note: a local `assay-ledger` commit duplicated a workflow fix already
merged on origin via PR #22. The duplicate (`d3b847e`) was confirmed to orphan
zero work (one file byte-identical on origin, the other superseded by the
stronger `4a6837a`), then dropped during a rebase onto `origin/main`; the three
real commits replayed cleanly and landed via PR #23.

### Scope note (stated plainly)

`assay-protocol` **PR #9 merged the entire `feat/rce-profile-v0-1` branch into
`main`, not only the two relocation commits.** This was intentional and is the
branch-level findability closure — but it widened the action from *"publish the
relocation"* to *"land the feature branch that contains the relocation."*
Anyone reviewing the merge should expect the full branch's contents on `main`,
not only the relocation diff.

## Verification

- **`assay-protocol`** — `main == origin/main == c1d1dfe`. All four docs
  tracked on `main`: `RCE_V0_NORMATIVE_SPEC.md`, `RCE_BOUNDARY_AMENDMENT_V0.md`,
  `docs/agents/TIER_ROSETTA.md`, `docs/agents/MOLT_PROTOCOL_V0.md`. Required
  checks passed: `qa-contract`, `test 3.10`, `test 3.11`, `test 3.12`.
- **`assay-ledger`** — `main == origin/main == 870730c`. Live ledger validates
  `PASS: 20`. Both enums enforced (bad `assurance_level` and bad `mode`
  rejected; live values accepted). Post-merge `assay-receipt` workflow passed.
  PR-gate checks `checkpoint-trust` and `validate` passed.
- **`founder-ops-private`** — `main == origin/main == 1927cc1`. The handoff
  path is now a `MOVED` stub pointing to `assay-protocol`.

## Remaining residue

- Pre-existing untracked files intentionally left alone: `assay-protocol/
  DO_NOT_USE.md` and `founder-ops-private/sales/`.
- Tier Rosetta crosswalk rows remain `[INFERRED]` pending each vocabulary
  owner's ratification (by design, not a defect).
- Other open rosetta fractures unchanged: cross-repo `proof_tier` name
  collision (receipt-substrate vs epistemic dialects); Loom `A (Court)` vs
  `receipt_tier` `court` marked `[NEEDS CHECK]`.
- `assay-ledger` `mode` and `assurance_level` are now pinned; no further ledger
  enum gaps known at time of writing.

## Meta

Every item here is evidence debt in the infrastructure meant to *detect*
evidence debt: a spec that "existed" but was not findable, a tier with no
members, a commit that duplicated another. The triggering dispute was settled
by receipts (`path + bytes + sha256`), not by argument — the discipline applied
to its own toolchain.
