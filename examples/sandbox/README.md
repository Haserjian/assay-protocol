# Sandbox Demo

Demonstrates CSP Tool Safety with **real filesystem deletes** inside a sandbox.

**This actually deletes files.** By default, confined to `/tmp/csp_sandbox`.

## Safety Features

- **Default sandbox root:** `/tmp` prefixes only (`/tmp`, `/private/tmp`, `/var/tmp`)
- **Risk ceiling enforcement:** Action risk cannot exceed plan risk
- **Scope enforcement:** Deletes outside plan scope are refused
- **Receipt trail:** Every action receipted to `.csp_real_receipts/`

## Quick Start (Basic Mode)

```bash
# Setup sandbox
mkdir -p /tmp/csp_sandbox/old
echo "hello" > /tmp/csp_sandbox/old/hello.txt

# Basic mode: CRITICAL blocked, HIGH allowed
python3 real_runner.py --mode basic \
  --sandbox-root /tmp/csp_sandbox \
  fs_delete --path /tmp/csp_sandbox/old

# Verify file was deleted
ls /tmp/csp_sandbox/old  # Should fail (deleted)
```

## Standard Mode (Plan + Guardian Required)

```bash
# Create plan
python3 real_runner.py make_plan \
  --scope "/tmp/csp_sandbox/old/*" \
  --risk HIGH \
  --out /tmp/csp_plan.json

# Create guardian verdict
python3 real_runner.py make_allow \
  --plan /tmp/csp_plan.json \
  --out /tmp/csp_verdict.json \
  --rationale "Cleanup approved by operator"

# Execute with plan + verdict
python3 real_runner.py --mode standard \
  --sandbox-root /tmp/csp_sandbox \
  --plan /tmp/csp_plan.json \
  --verdict /tmp/csp_verdict.json \
  fs_delete --path /tmp/csp_sandbox/old
```

## Commands

| Command | Purpose |
|---------|---------|
| `fs_delete --path <path>` | Delete file or directory (real!) |
| `make_plan --scope <glob> --risk <level> --out <file>` | Create a plan JSON |
| `make_allow --plan <file> --out <file> --rationale <text>` | Create an ALLOW verdict |

## Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--mode` | `basic` | `basic` or `standard` |
| `--sandbox-root` | (required) | Root directory for sandbox |
| `--risk` | `HIGH` | Risk level for plan (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) |
| `--unsafe-allow-any-sandbox-root` | off | Allow non-`/tmp` roots (dangerous!) |

## Receipts

Written to `.csp_real_receipts/<episode_id>/`:
- `*_plan.json` - Plan receipt
- `*_verdict.json` - Guardian verdict receipt
- `*_action.json` - Action attempt receipt
- `*_execution.json` - Execution result receipt
- `*_refusal.json` - Refusal receipt (if denied)

## Safety Invariants

1. **No root deletes** - `/` and `~` always classified CRITICAL and refused
2. **Sandbox-only** - Non-`/tmp` roots require explicit `--unsafe-*` flag
3. **Risk ceiling** - Action risk must be <= plan risk (e.g., HIGH plan can't authorize CRITICAL action)
4. **Scope match** - Action path must match plan scope glob

For simulated demo (no real side effects), see [`../simulated/`](../simulated/).
