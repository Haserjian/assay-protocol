# Simulated Demo

Demonstrates CSP Tool Safety behaviors **without executing any real commands**.

Safe to run anywhere - no filesystem changes, no network calls, no side effects.

## Quick Start

```bash
python3 demo.py
```

Expected output:
```
Episode: ep-<id>
Receipts: .csp_demo_receipts/ep-<id>

=== 1) CRITICAL without plan (expect REFUSED: amendment_vii_no_plan) ===
   REFUSED amendment_vii_no_plan

=== 2) Plan + Guardian ALLOW (expect EXECUTED_SIMULATED) ===
   EXECUTED_SIMULATED

=== 3) Scope mismatch (expect REFUSED: amendment_vii_scope_mismatch) ===
   REFUSED amendment_vii_scope_mismatch

=== 4) Plan but missing verdict (expect REFUSED: amendment_vii_no_guardian_verdict) ===
   REFUSED amendment_vii_no_guardian_verdict
```

## Verify Receipts

```bash
python3 verify_episode.py .csp_demo_receipts/<episode_id>
```

Checks:
- Receipt hash integrity (sha256)
- Parent hash chain (sequential ordering)
- Verdict-to-plan binding (plan_hash matches)

## Run Tests

```bash
python3 -m pytest test_classifier.py -v
```

## Files

| File | Purpose |
|------|---------|
| `demo.py` | Main demo runner (4 scenarios) |
| `verify_episode.py` | Receipt chain verifier |
| `test_classifier.py` | Unit tests for risk classification |
| `csp_demo/tool_safety.py` | Core CSP logic (classification, receipts, enforcement) |

## Limitations

- **Simulated only** - commands are never executed
- **Demo-grade canonicalization** - stable sort + compact JSON (not RFC 8785 JCS)
- **Pattern-based classification** - regex only, no semantic analysis

For real execution, see [`../sandbox/`](../sandbox/).
