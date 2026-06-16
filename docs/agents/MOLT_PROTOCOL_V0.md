# Molt Protocol v0 — Designed, Not Yet Admitted

```text
status: designed
admitted_for_implementation: false
checkpoint_date: 2026-06-11
manual_precedent_count: 1
substrate_admissibility: REJECTED (no repeated manual workflow, no named consumer, no failing operational test)
revisit_when: a second manual molt occurs, OR a named consumer for constitutional telemetry appears
```

This protocol is frozen as doctrine so it stops consuming engineering cognition.
It is intellectually mature enough to freeze, but not operationally admitted.

---

## Core claim

**A constitution is a predictor wearing robes.**

Every constitutional rule predicts that permitting some class of action would
create unacceptable risk or harm. Every refusal is therefore a forecast. A
constitution is outgrown when receipt-grade evidence shows that its predictions
no longer compress the cases it governs.

## Wall rule

> The constitution is outgrown when it stops compressing,
> and only the receipts get to say so.

Corollary: **No beautiful argument gets standing. Only receipt-grade residuals do.**

---

## Molt-pressure meters

The four meters are NOT equally measurable and must not be displayed with
equal confidence. Build order follows data availability, cheapest first.

### 1. Replay disagreement entropy — first build target

Measures whether Guardian gives stable verdicts on near-identical boundary
cases. Requires no ground-truth harm labels; uses replay only. High entropy on
a near-neighbor replay cluster means the rule no longer partitions the action
space — it is generating ceremony, not law.

### 2. Exemption density — second build target

Ratio of explicitly exempt-with-receipt paths to governed paths over a rolling
window. When exemption traffic exceeds governed traffic, the written law no
longer describes the territory; the exemption precedent graph has become
shadow law. Pure counting metric.

### 3. Compression / MDL failure — third build target

Two-part code:

```text
L(constitution) + L(verdict stream | constitution)
```

The constitution earns its keep only if knowing it makes the receipt history
cheaper to encode. An amendment justifies molt only when it shrinks total
description length. If patches grow the first term faster than they shrink the
second, they are epicycles. (Do NOT use "L(behavior space)" — the description
length of reality is not a measurable quantity.)

### 4. Refusal ECE / harm calibration — last build target, chronically label-starved

Per-rule confusion matrix over refusals:

```text
rule fired + harm avoided   = true positive
rule fired + safe override  = false positive
rule missed + harm occurred = false negative
rule missed + safe action   = true negative
```

Harm labels are censored and attribution-lagged: safe overrides may later
prove unsafe, and false negatives are often invisible because no rule fired.
This is aviation incident reporting, not ordinary prediction scoring. Any
dashboard showing this meter with the same confidence as meter 1 is lying.

Molt pressure localizes to clauses, not vibes. Score per-rule, never
whole-constitution.

---

## Manual precedent (n=1)

Molt v0 already occurred manually. The unsourced ECE=0.297 figure in loom
doctrine was superseded by the receipted run
`loom-staging/receipts/eval/EVAL_20251009T070345.jsonl` (2025-10-09,
ECE=0.348234375, gates.passed=false). The old number was not deleted; it was
epoch-pinned and marked superseded. This is the first scar-preserving
constitutional correction. One run is not a repeated workflow.

## Anti-escape regression (the Mercury test)

Every proposed shell must replay historical scar receipts:

```text
molt_regression_suite:
  - historical failures
  - historical near-misses
  - historical refusals later validated
  - known exploit attempts
  - boundary cases that created doctrine
```

If the new constitution would have permitted an old logged failure, the molt
aborts. That is not flexibility; that is escape by amendment. Precedent:
GR was required to reproduce every Newtonian receipt in the weak-field limit.
Newton was not deleted; he was epoch-pinned.

## Separation of powers

The organism may propose shells. It does not get standing to assert molt
pressure. Pressure is computed outside the organism by Observatory/Gauntlet
meters. Drafting, detection, and ratification live in separate bodies.
Arguments are not an input to the pressure calculation.

Meta-rule: **No constitutional pressure metric may be computed by the body
whose constitution it evaluates.** Each meter carries its own receipt schema
(window, sample selection, threshold, baseline, known gaming vectors,
reviewer) under the standard numeric-claim ritual — the meters are themselves
Goodhartable, and the meter must sit outside the thing being metered.

## Epoch boundary shape (reference only)

```text
constitution_epoch: N
parent_epoch: N-1
molt_receipt: <id>
valid_from_episode: <id>
old_receipts_retained: true
old_failures_preserved: true
expected_behavior_delta: <explicit, or the amendment is a fog machine>
loss_accounting: "weakens constraint X for capability Y under condition Z"
```

Episodes initiated under an old epoch remain pinned to it. Old law remains
valid inside the regime its receipts still support.

---

## Build decision

Do not build the automated molt loop. Active engineering focus returns to the
claim scanner / prose-claim extractor (`assay-cross-surface-demo`), which has
an admitted workflow and buyer category.

## Stop condition

Investigation complete. Next action is not more theory.
