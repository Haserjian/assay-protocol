# CSP Tool Safety Demo

A minimal proof-of-concept demonstrating CSP Tool Safety behaviors.

> **Note:** The core demo simulates execution (no real commands). For a sandboxed real delete runner, see `real_exec/real_runner.py`. For production wrappers that intercept real tool boundaries, see [IMPLEMENTORS.md](../../IMPLEMENTORS.md).

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

## Optional: sandboxed real deletes

Run real filesystem deletes inside a sandbox (no sudo, defaults to `/tmp/csp_sandbox`):

```bash
cd examples/python_demo
mkdir -p /tmp/csp_sandbox/old
echo "hello" > /tmp/csp_sandbox/old/hello.txt

# Basic: CRITICAL (sandbox root) is blocked; HIGH (inside) is allowed
python3 real_exec/real_runner.py --mode basic \
  --sandbox-root /tmp/csp_sandbox \
  fs_delete --path /tmp/csp_sandbox/old

# Standard: requires plan + ALLOW verdict
python3 real_exec/real_runner.py make_plan \
  --scope "/tmp/csp_sandbox/old/*" \
  --out /tmp/csp_plan.json

python3 real_exec/real_runner.py make_allow \
  --plan /tmp/csp_plan.json \
  --out /tmp/csp_verdict.json \
  --rationale "Scoped cleanup approved"

python3 real_exec/real_runner.py --mode standard \
  --sandbox-root /tmp/csp_sandbox \
  --plan /tmp/csp_plan.json \
  --verdict /tmp/csp_verdict.json \
  fs_delete --path /tmp/csp_sandbox/old
```

Receipts are written to `.csp_real_receipts/<episode_id>/`.

## Demo limitations

This is a **demo-grade** implementation for proof-of-concept purposes:

- **Simulated vs real execution** — `demo.py` simulates (never runs commands); `real_exec/real_runner.py` performs actual deletes in a sandbox
- **Demo-grade canonicalization** — stable sort + compact JSON, not full RFC 8785 JCS (sufficient for local hash verification, not for cross-implementation interop)
- **Simple scope matching** — uses glob/fnmatch, not path canonicalization
- **Pattern-based classification** — regex only, no semantic analysis
- **Timestamp ordering** — microsecond precision; extremely tight emission could theoretically collide (low risk)

For production implementations, see [IMPLEMENTORS.md](../../IMPLEMENTORS.md).
