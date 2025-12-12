# CSP Tool Safety Demo

A minimal proof-of-concept demonstrating CSP Tool Safety behaviors.

## What this proves

1. **CRITICAL without plan** → REFUSED (amendment_vii_no_plan)
2. **Plan + Guardian ALLOW** → EXECUTED_SIMULATED
3. **Scope mismatch** → REFUSED (amendment_vii_scope_mismatch)
4. **Plan but missing verdict** → REFUSED (amendment_vii_no_guardian_verdict)

All receipts are hash-verified and chain-linked.

## Run the demo

```bash
cd examples/python_demo
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

## Verify receipts

```bash
python3 verify_episode.py .csp_demo_receipts/<episode_id>
```

This checks:
- Receipt hash integrity (sha256)
- Parent hash chain (sequential ordering)
- Verdict → plan binding (plan_hash matches)

## Run classifier tests

```bash
python3 -m pytest test_classifier.py -v
```

## Demo limitations

This is a **demo-grade** implementation for proof-of-concept purposes:

- **No real execution** — commands are simulated, never run
- **Demo-grade canonicalization** — not full RFC 8785 JCS
- **Simple scope matching** — uses glob/fnmatch, not path canonicalization
- **Pattern-based classification** — regex only, no semantic analysis

For production implementations, see [IMPLEMENTORS.md](../../IMPLEMENTORS.md).
