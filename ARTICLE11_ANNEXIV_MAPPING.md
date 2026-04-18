# Assay Proof Packs And EU AI Act Article 11 / Annex IV

**Working map, not legal advice.**

This note answers a narrow question:

> If you hand an Assay proof pack to an assessor, auditor, or buyer, which parts of
> EU AI Act Article 11 / Annex IV does it help with, and which parts still need
> ordinary documentation outside Assay?

Short answer:

- **Assay helps with technical evidence**
- **Assay does not replace the full technical documentation package**

That distinction is the whole point.

## What Assay Is Good For

Assay proof packs are strongest when you need to prove that a specific AI run or decision:

- happened at a specific time
- was bound to a specific signer
- carried a specific policy hash or control context
- has not been modified since creation
- can be verified outside the operator's environment

This makes Assay a good fit for:

- audit appendices
- vendor response packets
- regulator response supplements
- post-incident evidence preservation
- test and validation evidence for consequential workflows

## What Assay Does Not Replace

Assay does **not** generate the full Annex IV documentation set by itself.
You still need ordinary provider documentation for items such as:

- intended purpose and scope statement
- provider identity and product description
- system architecture narrative
- training and validation data documentation
- risk management process
- human oversight design rationale
- cybersecurity design documentation
- post-market monitoring plan
- EU declaration of conformity

Assay should be positioned as **supporting evidence inside that package**, not as the package itself.

## Proof-Pack Fields That Matter

An Assay proof pack typically includes:

- `pack_manifest.json`
  - `pack_id`
  - `attestation.run_id`
  - `attestation.policy_hash`
  - `attestation.timestamp_start`
  - `attestation.timestamp_end`
  - `attestation.n_receipts`
  - `attestation.time_authority`
  - `signer_id`
  - `signer_pubkey`
  - file hashes
- `receipt_pack.jsonl`
  - action or model-call receipts
  - timestamps
  - callsites
  - provider/model identifiers
  - token or latency metadata when present
- `verify_report.json`
  - pass/fail result
  - receipt count
  - verifier version
- `verify_transcript.md`
  - human-readable verification summary

Those fields make the evidence portable and independently checkable.

## Working Map To Annex IV

The table below is intentionally conservative.

| Annex IV item | Where Assay helps | What Assay does **not** cover by itself |
|---|---|---|
| `1(a)` Intended purpose, provider, version | Pack and receipt metadata can support versioned run evidence and release-specific verification artifacts | Intended purpose statement, product description, provider narrative |
| `1(b)` Interactions with other software / AI systems | Receipts can show model providers, tool calls, integration sources, and callsites for the instrumented run | Full system interaction inventory and architectural explanation |
| `1(c)` Relevant software versions and update requirements | `run_id`, verifier version, policy hash, and CI binding can support version traceability for a given run | Full software bill of materials, release process, update requirements |
| `1(d)` Forms of placement on the market / service | Proof packs can evidence API or packaged-run behavior in the form actually exercised | Commercial packaging description and deployment forms |
| `1(g)` / `1(h)` User interface and deployer instructions | Verification transcript can support reviewer understanding of what happened in a run | User manuals, operating instructions, deployer-facing controls documentation |
| `2(a)` Development methods and third-party tools | Receipts can show which provider/model/tool path was actually used in a run | Full development methodology and supplier integration narrative |
| `2(b)` Design specifications, logic, rationale, assumptions | Policy hash and decision receipts can bind a run to a specific control state | Design rationale, optimization choices, trade-offs, assumptions |
| `2(c)` System architecture and component integration | Receipts and callsites can support claims about runtime paths | Full architecture description and compute-resource documentation |
| `2(d)` Data requirements, provenance, selection, labeling, cleaning | Assay can hash or reference external artifacts if you choose to include them | Training / validation / test data documentation itself |
| `2(e)` Human oversight measures | Decision or policy receipts can support evidence that a gate, review, or approval path ran | The full human-oversight design and operational procedure |
| `2(f)` Pre-determined changes and continuous compliance | Repeated proof packs can show versioned evidence over time | Formal change-control documentation and pre-determined change specification |
| `2(g)` Validation/testing procedures, metrics, logs, signed test reports | This is one of Assay's strongest fits: signed run receipts, verifier reports, and transcripts are directly useful here | The full test plan, test coverage rationale, and non-Assay test artifacts |
| `2(h)` Cybersecurity measures | Assay can prove integrity of the evidence artifact and bind it to a signer | Full cybersecurity architecture and control set |
| `3` Monitoring, functioning, control, limitations, oversight | Receipts and verification artifacts can support claims about observed behavior and control execution | Full limitations analysis, risk descriptions, and deployer guidance |
| `4` Appropriateness of performance metrics | Assay can preserve signed outputs of metric-evaluation runs | The substantive justification that the chosen metrics are appropriate |
| `5` Risk management system | Assay can evidence that specific gates or policies executed in a run | The provider's Article 9 risk management system |
| `6` Relevant lifecycle changes | Multiple versioned proof packs can show before/after evidence over time | Full lifecycle change log and governance narrative |
| `7` Standards and technical specifications applied | Policy hash, verifier version, and referenced artifacts can support standards claims for a run | The formal standards register and conformity rationale |
| `8` EU declaration of conformity | None directly | The declaration itself |
| `9` Post-market monitoring system and plan | Assay can generate run-level monitoring evidence and preserve honest failures over time | The post-market monitoring plan and operating process |

## Practical Framing For Buyers And Assessors

The most honest external sentence is:

> Assay gives you signed, independently verifiable technical evidence that can
> sit inside an Article 11 / Annex IV documentation package. It does not replace
> the package.

That framing is stronger than over-claiming.

## Best Use In A Pilot

For a first pilot, use Assay to attach a proof pack to one consequential workflow:

- hiring-screening recommendation
- insurance or credit decision support
- clinical decision support output

Then provide:

1. the proof pack
2. the verifier output
3. a short cover note explaining which Annex IV items this evidence supports
4. the surrounding ordinary documentation outside Assay

That is a credible package a real reviewer can react to.

## What To Ask An Assessor

Use a single question:

> If this proof pack arrived with a vendor questionnaire response or regulator
> packet, would it shorten your review, and what is missing for it to be
> admissible in your workflow?

That question is better than asking whether they “like the protocol.”

## Boundaries To Preserve

Do not claim that Assay proves:

- model correctness
- fairness by itself
- completeness of instrumentation
- signer honesty
- full Annex IV compliance on its own

Those claims are not needed to win the actual buyer conversation.
