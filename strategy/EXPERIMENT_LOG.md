# Experiment Log

Tracking adoption experiments with receipts and metrics.

---

## EXP-MSG-001: Outcome Language A/B

**Status:** ACTIVE
**Started:** 2025-12-14
**Principle:** Sell the hole, not the drill

### Variants Deployed

| Location | Variant A (Feature) | Variant B (Outcome) |
|----------|---------------------|---------------------|
| README tagline | "Safety controls for AI agents" | "Proof your agent didn't go rogue" |
| README subtitle | "Reference implementation + conformance tests" | "When your agent does something unexpected, you'll wish you had receipts" |
| Twitter bio | TBD | "Agents talk via MCP. Agents prove via CSP." |

### Baseline Metrics (Pre-experiment)

| Metric | Value | Date |
|--------|-------|------|
| GitHub stars | TBD | 2025-12-14 |
| README scroll depth | TBD | - |
| Clone rate (7d) | TBD | - |

### Hypothesis
Outcome language ("proof when things go wrong") outperforms feature language ("emit receipts for every decision").

### Receipt
```json
{
  "experiment_id": "EXP-MSG-001",
  "variant_deployed": "B",
  "deployment_date": "2025-12-14",
  "changes": [
    {"file": "README.md", "line": 5, "before": "Safety controls for AI agents using tools", "after": "Proof your agent didn't go rogue"}
  ]
}
```

---

## EXP-FRICTION-001: Reassurance Microcopy

**Status:** ACTIVE
**Started:** 2025-12-14
**Principle:** Dare to be trivial

### Implementation

Added reassurance messages to CLI output at key friction points:

1. After successful test run
2. After receipt minting
3. After Guardian approval

### Changes Made

| Location | Before | After |
|----------|--------|-------|
| pytest output | "22 passed" | "22 passed - Guardian verified all controls" |
| csp_validate | "Overall: [PASS]" | "Overall: [PASS] - Your implementation is CSP conformant" |
| Receipt emission | (silent) | "Receipt minted. This proof exists forever." |

### Hypothesis
Single reassurance line at friction point increases completion and trust.

---

## EXP-ONBOARD-003: Deny-by-Default Messaging

**Status:** ACTIVE
**Started:** 2025-12-14
**Principle:** Dangerous default inversion

### Implementation

Positioned deny-by-default as a safety feature, not a limitation:

| Location | Message |
|----------|---------|
| README "What You Get" | "Deny-by-default protection: Nothing executes without explicit policy approval" |
| FOR_HUMANS.md | "Your agent can't go rogue. Nothing runs without your permission." |
| Error messages | "Guardian blocked this action. No policy permits it." |

### Hypothesis
Emphasizing restriction as safety feature increases trust among security-conscious users.

---

## EXP-CONTENT-001: Anti-Demo

**Status:** SCAFFOLDED
**Started:** 2025-12-14
**Principle:** Drama of prevention > boredom of success

### Demo Script

See: `examples/anti_demo/` (created below)

### Key Moments

1. Agent attempts `rm -rf /var/log/old`
2. Guardian intercepts with dramatic RED block
3. Receipt minted with hash
4. Narrator: "Your agent tried. CSP stopped it. Here's your proof."

### Hypothesis
Demo showing blocked dangerous command outperforms successful command demo.

---

## Metrics Dashboard

| Experiment | Primary Metric | Current | Target | Status |
|------------|----------------|---------|--------|--------|
| MSG-001 | Stars (7d) | - | +10% | Tracking |
| FRICTION-001 | Completion rate | - | +5% | Tracking |
| ONBOARD-003 | Security segment activation | - | +15% | Tracking |
| CONTENT-001 | Watch completion | - | 80% | Not started |

---

## Next Review: 2025-12-21
