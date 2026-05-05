# GLIMPS Profile v0

GLIMPS is a schema-first protocol profile for pre-claim hypothesis birth.

A glimpse is not a claim. A claim is not an invariant. GLIMPS admits candidate sight into the organism without granting authority.

## Doctrine

- GLIMPS births candidate sight.
- Claim Packets admit structured claims.
- Arena wounds candidates.
- Guardian scopes authority.
- Assay remembers.
- Quintet evolves the law.

GLIMPS lands protocol-first because it is upstream of authority. It must not mutate Loom runtime state, MemoryGraph, Guardian policy, or default routes.

## Core Law

- Fertility may request attention.
- Fertility may not allocate budget.
- Only receipts may buy confidence.
- Only wounds may buy authority.
- Beauty may point, but never testify.
- Ghosts may seed, but never govern.

## Artifact Chain

```text
Glimpse Packet -> Claim Packet -> Wound Receipt -> Guardian Decision -> Archive/Ghost
```

## Receipt Types

### `glimps.birth/v0`

Records a Glimpse Packet: the pressure, lens, candidate frame, rivals, first wound, permissions, attention request, lens debt, and negative duties.

### `glimps.emission_census/v0`

Audits the birth-side coverage of a GLIMPS run. It catches silent non-generation, frame monoculture, rival suppression, unwounded candidates, attention capture, and fertility-confidence confusion.

### `glimps.wound/v0`

Records an Arena probe against a glimpse candidate. A wound receipt links back to the birth receipt by `glimpse_id`.

## Object Ladder

```text
spark
pressure_note
lens
candidate_hypothesis
proof_program
```

Promotion to a Claim Packet does not require a candidate to survive its first wound. It requires woundability:

- pressure named
- lens blindness recorded
- at least one rival
- first wound specified
- cheap probe available
- permissions locked down
- promotion requirements declared

Surviving wounds belongs to Arena and Guardian, not GLIMPS.

## Non-Goals

- No LLM calls.
- No Guardian integration.
- No Loom MemoryGraph mutation.
- No runtime authority.
- No policy mutation.
- No claim that a glimpse proves truth.

## Adapter TODOs

- Map these profile receipts into the Constitutional Receipt Standard once the CRS profile registry is ready.
- Define the Claim Packet adapter boundary after `glimps.wound/v0` examples stabilize.
- Add optional Evidence Wire Protocol correlation fields without making this v0 depend on AgentMesh.
- Add Assay validator support for profile-level invariant checks.
