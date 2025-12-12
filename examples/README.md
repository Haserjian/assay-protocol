# CSP Tool Safety Examples

Two proof-of-concept demos showing CSP Tool Safety behaviors.

## Choose Your Demo

| Folder | What It Does | Risk Level |
|--------|--------------|------------|
| [`simulated/`](./simulated/) | Simulates tool execution (no real commands run) | **None** - safe to run anywhere |
| [`sandbox/`](./sandbox/) | Actually deletes files inside a sandbox | **Low** - confined to `/tmp` by default |

## Quick Start

### Simulated Demo (recommended first)

```bash
cd examples/simulated
python3 demo.py
python3 verify_episode.py .csp_demo_receipts/<episode_id>
```

### Sandbox Demo (real deletes)

```bash
cd examples/sandbox
mkdir -p /tmp/csp_sandbox/old
echo "test" > /tmp/csp_sandbox/old/test.txt
python3 real_runner.py --mode basic --sandbox-root /tmp/csp_sandbox \
  fs_delete --path /tmp/csp_sandbox/old
```

## What These Prove

Both demos show the same CSP Tool Safety behaviors:

1. **CRITICAL actions blocked** without plan + guardian approval
2. **Scope enforcement** - actions outside plan scope refused
3. **Receipt chain** - every action receipted with hash verification
4. **Guardian verdicts** - ALLOW required for HIGH/CRITICAL risk

For production implementations, see [IMPLEMENTORS.md](../IMPLEMENTORS.md).
