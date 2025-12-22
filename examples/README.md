# Assay Examples

Two proof-of-concept demos showing Assay behaviors.

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
python3 verify_episode.py .assay_demo_receipts/<episode_id>
```

### Sandbox Demo (real deletes)

```bash
cd examples/sandbox
mkdir -p /tmp/assay_sandbox/old
echo "test" > /tmp/assay_sandbox/old/test.txt
python3 real_runner.py --mode basic --sandbox-root /tmp/assay_sandbox \
  fs_delete --path /tmp/assay_sandbox/old
```

## What These Prove

Both demos show the same Assay behaviors:

1. **CRITICAL actions blocked** without plan + guardian approval
2. **Scope enforcement** - actions outside plan scope refused
3. **Receipt chain** - every action receipted with hash verification
4. **Guardian verdicts** - ALLOW required for HIGH/CRITICAL risk

For production implementations, see [IMPLEMENTORS.md](../IMPLEMENTORS.md).
