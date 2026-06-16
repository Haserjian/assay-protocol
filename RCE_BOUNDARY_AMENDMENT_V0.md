# RCE Boundary Amendment v0 — Runtime Boundary Law (Appendix)

**Status:** `[DESIGNED]` — paper-only. No runtime, sandbox, parser, or schema
implementation is authorized by this document.
**Date:** 2026-06-11
**Normative home:** appendix to `RCE_V0_NORMATIVE_SPEC.md`. This amendment does
not create a second Episode truth. Where this amendment and
`RCE_PROFILE.md` (Haserjian/assay-protocol) diverge, the profile wins.
**Provenance:** design conversation 2026-06-11 (boundary-law branch), audited
against the local ecosystem census of the same date.
**Tier language:** this amendment introduces NO new tier vocabulary. All
evidence-strength language defers to existing axes; see
`docs/agents/TIER_ROSETTA.md`.

---

## 0. The two pinned laws

> **A boundary violation may generate evidence for a successor episode, but it
> may not expand the authority of the current episode.**

> **Undeclared reads are denied before bytes move; violation receipts may
> disclose the attempted path, never the forbidden contents.**

Everything below is machinery for these two sentences.

---

## 1. Declared state boundary

An episode that mutates state MUST declare its boundary. Whole-filesystem or
whole-repo hashing is rejected: it is noisy, slow, and dishonest — it makes
the proof look stronger while making replay less meaningful.

```json
"state_boundary": {
  "mode": "scoped_git_worktree",
  "read":  ["src/assay/receipt_validator.py", "tests/...", "pyproject.toml"],
  "write": ["src/assay/receipt_validator.py", "tests/..."],
  "exclude": [".git/**", ".venv/**", "__pycache__/**", "artifacts/**"]
}
```

Rules:

- `write` ⊆ effective mutation surface. Any observed mutation outside `write`
  is a violation.
- `read` is the declared dependency surface. Reads outside `read` are
  violations (see §3). An episode may read more than it may write; the two
  lists are independent.
- The boundary law: **hash the smallest complete state needed to justify the
  episode, not the biggest state you can technically hash.**

Three hashes, not one (extends the §1 identity triangle of the RCE spec;
does not replace it):

| Hash | Question it answers |
|---|---|
| `repo_anchor_hash` | Where was the repo before the episode? (git tree/commit anchor — lean on git's content-addressable object model, do not reinvent it) |
| `boundary_pre_hash` | What exact in-boundary state did this episode depend on? |
| `boundary_post_hash` | What exact in-boundary state existed after commit? |

Prior-art alignment (not novelty claims): in-toto materials/products rules,
SLSA provenance attestations, WASI capability-based resource access. The RCE
delta is applying that discipline to agentic state transitions rather than
package builds.

## 2. Ambient context pinning

Files are not the only reads. An episode's replay claims are capped unless
ambient dependencies are pinned:

```json
"ambient_context": {
  "env_allowlist": ["PATH", "PYTHONPATH"],
  "mock_time": "2026-06-11T00:00:00Z",
  "rng_seed": 42,
  "dependency_anchors": { "lockfile": "uv.lock@sha256:..." },
  "network": "deny"
}
```

- Unpinned ambient dependency observed during execution → replay-maturity
  language MUST be downgraded per the existing axes (e.g., OAE replay
  fidelity `BEST_EFFORT`, not `BOUNDED`/`DETERMINISTIC`). No new tier is
  minted for this.
- Lockfile-anchor mismatch at replay time → the replay verdict MUST refuse
  strict comparison and flag environment mismatch.
- If read isolation is not enforced by the executing runtime, the receipt
  MUST carry the caveat verbatim:
  `"read isolation not enforced; only write boundary was checked."`
  This caveat is the honesty mechanism, not a weakness.

## 3. Undeclared-read violation receipt

Detection of an undeclared read hard-faults the episode. The runtime denies
the read **before bytes are returned**, then emits:

```json
{
  "violation_type": "undeclared_read",
  "episode_id": "ep_...",
  "attempted_path": "pyproject.toml",
  "attempted_mode": "read",
  "bytes_returned": false,
  "severity": "boundary_missing_dependency",
  "suggested_amendment": {
    "read_boundary_add": ["pyproject.toml"],
    "reason": "test execution inspected project metadata"
  },
  "current_episode_result": "ADMISSIBLE_FALSE"
}
```

- `bytes_returned: false` is mandatory and load-bearing: a violation receipt
  that quotes forbidden content is itself a leak channel.
- `suggested_amendment` is **non-authoritative**. The runtime may suggest a
  wider boundary; only an authorized actor may grant it.

Three severity classes, three response postures:

| Class | Examples | Posture |
|---|---|---|
| Ordinary dependency miss | `pyproject.toml`, lockfiles, `pytest.ini` | Hard-fault; emit amendment candidate; successor episode allowed |
| Sensitive boundary breach | `.env`, `~/.ssh/**`, `~/.aws/**`, `secrets/**`, browser/mail state | Hard-fault; NO auto-amendment; escalate to Guardian/human; path itself may be redacted in the receipt |
| Ambient/temporal dependency | `time()`, `random()`, hostname, DNS, env vars | Hard-fault or downgrade replay-maturity language; suggest `ambient_context` amendment |

Sensitive-class reads are never self-authorizable by the agent. The consent
posture inherits from Compact doctrine: closed by default.

## 4. Supersession state machine

```text
DRAFT → PRECHECKED → EXECUTING → COMMITTED
                          │
                          └→ VIOLATION_RECORDED
                                → AMENDMENT_PROPOSED
                                  → SUPERSEDED_BY_NEW_EPISODE
```

- **There is no resume-after-boundary-expansion transition.** The phrase is
  forbidden. Resuming creates ambiguity about what was actually authorized.
- The failed episode is immutable. The successor is a new signed episode:

```json
{
  "episode_id": "ep_..._002",
  "supersedes": "ep_..._001",
  "amendment_reason": "undeclared read during test execution",
  "boundary_diff": { "read_added": ["pyproject.toml"], "write_added": [] },
  "prior_violation_receipt": "sha256:..."
}
```

- A failed episode never becomes admissible retroactively. It becomes a
  receipt-pinned negative example — violation evidence is governance data,
  adjacent to the epistemic kernel's `denial_record` and contradiction
  receipts, and must remain distinguishable from admissible commit evidence.

## 5. Policy posture (sketch, non-normative)

```rego
default allow_boundary_auto_expand := false

allow_amendment_proposal if {
  input.violation.type == "undeclared_read"
  input.violation.bytes_returned == false
  not sensitive_path(input.violation.path)
}

require_human_review if { sensitive_path(input.violation.path) }
require_new_episode  if { input.violation.type == "undeclared_read" }
```

## 6. Implementation gates

This amendment is admissible as paper only. Implementation requires at least
one declared traction path per the substrate-admissibility doctrine:

- **Named trigger 1:** a buyer/commercial claim requires converting a current
  claim-sheet non-claim into a claim — the OpenClaw v1 claim sheet's "does
  not prove complete coverage of all runtime activity" is the named surface
  where read isolation would do exactly that.
- **Named trigger 2:** a second real boundary-violation incident with
  receipts (one manual run is design fuel; two is a workflow).
- **Named trigger 3:** RCE moves from `[DESIGNED]` to `[IMPLEMENTED]` and a
  wired consumer demands boundary enforcement.

Until a trigger fires: no runtime, no VFS/eBPF/WASI sandbox work, no new
repo, no new EpisodeSpec, no parser, no syntax.

## 7. What this amendment does not claim

- It does not claim read isolation is currently enforced anywhere in the
  ecosystem (it is not).
- It does not claim the violation-receipt schema is final (`v0`, unratified).
- It does not claim hash-chaining alone makes evidence trustworthy — receipts
  become tamper-evident only when hash-chained, signed, append-only,
  schema-pinned, and independently replayable. Otherwise this is a fancy log
  with better manners.
- It does not introduce or extend any proof-tier ladder.
