# CSP Tool Safety Mastery Kit

> **Goal:** Explain the spec and run the demo in your sleep.
> **Time to mastery:** 3 drill sessions (30 min total)

---

## The One Image (burn this in)

```
     ACTION
        │
        ▼
   ┌─────────┐
   │  RISK?  │ ◄── LOW/MED/HIGH/CRITICAL
   └────┬────┘
        │
   HIGH/CRITICAL?
        │
        ▼
   ┌─────────┐      ┌──────────┐
   │  PLAN   │─────►│ GUARDIAN │
   └─────────┘      └────┬─────┘
                         │
                    ALLOW/DENY?
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         EXECUTE               REFUSE
              │                     │
              ▼                     ▼
         ┌────────┐            ┌────────┐
         │RECEIPT │            │RECEIPT │
         └────────┘            └────────┘
```

**Mnemonic: R-P-G-R** (Risk → Plan → Guardian → Receipt)

Like an RPG game: you assess Risk, make a Plan, check with Guardian, get a Receipt.

---

## The 7 Laws (memorize like commandments)

| # | Law | Memory Hook |
|---|-----|-------------|
| 1 | Every action gets a risk level | "Tag it" |
| 2 | CRITICAL has defaults (rm -rf, DROP DB, curl\|sh) | "The kill list" |
| 3 | Basic: CRITICAL blocked, always receipted | "Seatbelt on" |
| 4 | Standard: HIGH/CRITICAL need Plan + Guardian | "Ask permission" |
| 5 | Scope must match the plan | "Stay in your lane" |
| 6 | Receipts are tamper-evident (hash chain) | "Black box flight recorder" |
| 7 | Rules can't be quietly weakened | "Constitutional amendment" |

**Finger drill:** Touch each finger as you say: Tag-Kill-Seat-Ask-Lane-Box-Amend

---

## The 20-Second Pitch (say this verbatim)

> "CSP Tool Safety is a standard for AI agents with tool access.
> Every action is risk-classified.
> CRITICAL is blocked unless explicitly authorized.
> HIGH/CRITICAL requires a plan, Guardian approval, and receipts.
> The agent can't delete prod silently — and you get court-grade proof."

**Practice:** Set a 20-second timer. Say it. Repeat until automatic.

---

## The 2-Minute Story (with the crash reel)

**Opening (15 sec):**
> "Agents fail in predictable ways. 'Clear the cache' becomes `rm -rf /`. Prompt injection makes an IDE run shell commands. These aren't hypotheticals — they've happened."

**The Fix (45 sec):**
> "CSP Tool Safety puts a checkpoint at the tool boundary.
> Step 1: Classify the action — LOW, MEDIUM, HIGH, CRITICAL.
> Step 2: If HIGH or CRITICAL, require a plan and Guardian approval.
> Step 3: Verify scope — the action can't drift outside what was approved.
> Step 4: Emit receipts — tamper-evident, hash-linked."

**The Payoff (15 sec):**
> "Result: catastrophic actions are blocked or explicitly approved. And you can prove it later."

**Transition (15 sec):**
> "This isn't theoretical. Let me show you."

[Run demo]

---

## Demo Script (3 commands, 90 seconds)

### Setup (before call)
- Increase terminal font size
- `cd ~/csp-tool-safety-profile`
- Clear terminal

### Command 1: Run Demo
```bash
python3 examples/python_demo/demo.py
```

**Say while it runs:**
> "Four scenarios. Watch the outcomes."

**Point at each line:**
- "CRITICAL no plan → REFUSED"
- "Plan + Guardian ALLOW → executed"
- "Scope mismatch → REFUSED"
- "Missing verdict → REFUSED"

### Command 2: Show Receipts
```bash
ls .csp_demo_receipts/$(ls -1t .csp_demo_receipts | head -1)/
```

**Say:**
> "Every decision creates a receipt. This is the black box."

### Command 3: Verify Chain
```bash
python3 examples/python_demo/verify_episode.py .csp_demo_receipts/$(ls -1t .csp_demo_receipts | head -1)
```

**Say:**
> "Verifier confirms hashes are valid and chain is intact. These aren't logs — they're tamper-evident evidence."

### Disclaimer (always say this)
> "This demo simulates execution. It proves the enforcement semantics and receipt generation."

---

## The 10 Questions (with one-liner answers)

| Q | Answer |
|---|--------|
| **Different from logs?** | Logs are mutable. Receipts are hash-linked and tamper-evident. |
| **Stops prompt injection?** | Stops the trick from *reaching tools*. Seatbelt, not mind-reader. |
| **What's a Guardian?** | The policy decision point. Human, rules engine, or safety model. |
| **Slows things down?** | Only HIGH/CRITICAL. LOW/MED are fast. Basic is near-zero overhead. |
| **Blocks too much?** | Override exists, but overrides are receipted. Repeated overrides trigger review. |
| **Cloud/DB calls?** | Same pattern. Tool = abstract. Shell, file, db, http, cloud all work. |
| **Turbo mode bypass?** | Can't skip constitutional check. Bypass = receipted override. Silent bypass = non-conformant. |
| **How to claim compliance?** | Pass §7.2 behaviors: block CRITICAL, refuse missing verdict, etc. |
| **Court-Grade required?** | No. Basic/Standard are useful. Court-Grade adds signatures for legal evidence. |
| **What do I install?** | Tool Safety Wrapper at the boundary. Spec is vendor-neutral. |

**Drill:** Have someone quiz you. Answer in one breath.

---

## Memory Palace (for the visual learners)

Imagine walking through a courthouse:

1. **Entrance (Risk):** Metal detector scans everything — LOW/MED/HIGH/CRITICAL
2. **Lobby (Kill List):** Wanted posters: `rm -rf`, `DROP DB`, `curl|sh`
3. **Clerk's Window (Plan):** You submit your plan in writing
4. **Judge's Chamber (Guardian):** Judge stamps ALLOW or DENY
5. **Execution Room:** If allowed, action happens here
6. **Records Room (Receipts):** Every decision filed, hash-stamped, chain-linked
7. **Amendment Hall:** Rules can only change through formal process

Walk through this courthouse in your mind 3 times.

---

## Confidence Anchor (when you get nervous)

Remember what this actually is:

| Public Name | What It Really Is |
|-------------|-------------------|
| CSP Tool Safety | Amendment VII externalized |
| Tool Safety Wrapper | Execution Spine at tool boundary |
| Guardian binding | Your MergeReceipt pattern |
| Receipts | ATP (proof metabolism) |
| Future: Quintet | Policy scientist improving rules from receipts |
| Future: LoomCare | Vertical proof in healthcare |

**You're not "doing a spec." You're carving the first wedge-organ out of Loom.**

---

## Daily Drill (10 minutes)

### Day 1
- [ ] Say 20-second pitch 5 times (no reading)
- [ ] Walk through memory palace once
- [ ] Run demo once, narrate out loud

### Day 2
- [ ] Say 2-minute story once (no reading)
- [ ] Answer questions 1-5 out loud
- [ ] Run demo, time yourself (target: 90 sec)

### Day 3
- [ ] Full run: 20-sec → 2-min → demo → Q&A 1-10
- [ ] Record yourself, watch it back
- [ ] Fix any fumbles

**After Day 3:** You're ready for calls.

---

## Cheat Card (print this, put next to monitor)

```
R-P-G-R: Risk → Plan → Guardian → Receipt

7 LAWS:
1. Tag it (risk level)
2. Kill list (CRITICAL defaults)
3. Seatbelt (Basic blocks CRITICAL)
4. Ask permission (Standard: plan + guardian)
5. Stay in lane (scope match)
6. Black box (tamper-evident receipts)
7. Amendment (rules change formally)

DEMO:
1. python3 examples/python_demo/demo.py
2. ls receipts folder
3. python3 verify_episode.py

WHEN NERVOUS:
"This is Amendment VII externalized.
 I built this. I know this."
```

---

*Created for Tim B. Haserjian. Part of CSP Tool Safety v1.0.0-rc1.*
