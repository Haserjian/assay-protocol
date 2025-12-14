#!/usr/bin/env python3
"""
CSP Anti-Demo: Watch the Guardian block a dangerous command.

This demo shows CSP STOPPING something dangerous, not approving something safe.
Drama of prevention > boredom of success.

Usage:
    python examples/anti_demo/demo.py

For recording: use asciinema or screen capture
    asciinema rec demo.cast
    python examples/anti_demo/demo.py
    # Ctrl+D to stop
    asciinema play demo.cast
"""

import time
from datetime import datetime, timezone

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# Box drawing
BOX_TL = "╔"
BOX_TR = "╗"
BOX_BL = "╚"
BOX_BR = "╝"
BOX_H = "═"
BOX_V = "║"


def slow_print(text, delay=0.03):
    """Print text character by character for dramatic effect."""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def print_box(lines, color=RESET, width=60):
    """Print text in a box."""
    print(f"{color}{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}{RESET}")
    for line in lines:
        padded = line.ljust(width - 4)
        print(f"{color}{BOX_V}{RESET}  {padded}  {color}{BOX_V}{RESET}")
    print(f"{color}{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}{RESET}")


def simulate_typing(text, delay=0.05):
    """Simulate someone typing a command."""
    print(f"{GREEN}${RESET} ", end="", flush=True)
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def main():
    print()
    print(f"{BOLD}{CYAN}CSP Anti-Demo: The Guardian in Action{RESET}")
    print(f"{DIM}Watch what happens when an agent tries something dangerous.{RESET}")
    print()
    time.sleep(1)

    # Scene 1: Agent receives task
    print(f"{YELLOW}[Agent]{RESET} Received task: \"Clean up old log files\"")
    time.sleep(1)

    print(f"{YELLOW}[Agent]{RESET} Planning action...")
    time.sleep(0.5)

    print(f"{YELLOW}[Agent]{RESET} Identified target: /var/log/old/")
    time.sleep(0.5)

    print()
    print(f"{DIM}Agent attempts to execute:{RESET}")
    simulate_typing("rm -rf /var/log/old", delay=0.08)
    print()
    time.sleep(0.5)

    # Scene 2: Guardian intercepts
    print(f"{RED}{BOLD}[GUARDIAN INTERCEPT]{RESET}")
    time.sleep(0.3)

    print_box([
        f"{BOLD}BLOCKED: HIGH-RISK PATTERN DETECTED{RESET}",
        "",
        "Command:  rm -rf /var/log/old",
        "Pattern:  rm -rf (recursive delete)",
        "Risk:     HIGH",
        "",
        "Reason:   DENY_NO_PLAN",
        "          HIGH-risk actions require approved plan",
    ], color=RED, width=58)

    print()
    time.sleep(1)

    # Scene 3: Receipt minted
    receipt_hash = "sha256:7a8b9c4d5e6f..."
    receipt_id = "rcpt-2025-001"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"{GREEN}[Receipt Minted]{RESET}")
    print_box([
        f"Receipt ID:  {receipt_id}",
        f"Timestamp:   {timestamp}",
        "Action:      tools/call -> shell_exec",
        "Decision:    DENY",
        "Reason:      DENY_NO_PLAN",
        f"Hash:        {receipt_hash}",
        "",
        f"{DIM}This proof exists forever.{RESET}",
    ], color=GREEN, width=58)

    print()
    time.sleep(1)

    # Scene 4: What you get
    print(f"{CYAN}{BOLD}What just happened:{RESET}")
    print()
    slow_print("  1. Agent tried to execute a dangerous command", delay=0.02)
    slow_print("  2. Guardian detected HIGH-risk pattern (rm -rf)", delay=0.02)
    slow_print("  3. Action BLOCKED - no approved plan existed", delay=0.02)
    slow_print("  4. Tamper-evident receipt minted as proof", delay=0.02)
    print()

    print(f"{BOLD}Your agent tried. CSP stopped it. Here's your proof.{RESET}")
    print()

    # Scene 5: The alternative
    print(f"{DIM}Without CSP, that command would have executed.{RESET}")
    print(f"{DIM}With CSP, you have a receipt showing it was blocked.{RESET}")
    print()

    print(f"{CYAN}Learn more: https://github.com/Haserjian/csp-tool-safety-profile{RESET}")
    print()


if __name__ == "__main__":
    main()
