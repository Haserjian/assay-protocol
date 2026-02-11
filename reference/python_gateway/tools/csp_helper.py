#!/usr/bin/env python3
"""CSP Helper CLI — Quickstart and demo tools for CSP Tool Safety.

This CLI provides easy entry points for:
1. Quickstart: Spin up a CSP gateway for evaluation
2. Demo: Interactive demonstration of PCCap (Proof-Carrying Capabilities)

Usage:
    python tools/csp_helper.py quickstart
    python tools/csp_helper.py demo --scenario fs-delete

Part of CSP Tool Safety Profile reference implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from csp_gateway.pccap import (
    Keyring,
    PCCapPolicyEngine,
    PCCapScope,
    enforce_pccap_for_fs_delete,
    mint_pccap_fs_delete,
)
from csp_gateway.types import Principal, RiskCategory


def cmd_quickstart(args: argparse.Namespace) -> int:
    """Quickstart: Initialize a CSP environment for evaluation."""
    print("=" * 60)
    print("CSP Tool Safety Profile — Quickstart")
    print("=" * 60)
    print()

    # Create a temporary directory for the demo
    work_dir = Path(args.work_dir) if args.work_dir else Path(tempfile.mkdtemp(prefix="csp_"))
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"Work directory: {work_dir}")
    print()

    # Initialize keyring
    key_file = work_dir / ".csp_key"
    if key_file.exists():
        print(f"Loading existing key from {key_file}")
        keyring = Keyring(secret_key=key_file.read_bytes())
    else:
        print("Generating new signing key...")
        keyring = Keyring()
        key_file.write_bytes(keyring._secret)
        print(f"Key saved to {key_file}")

    # Create sample policy
    policy_file = work_dir / "policy.json"
    policy = {
        "version": "1.0",
        "description": "CSP quickstart policy",
        "tools": {
            "fs.read": {"risk": "LOW", "allow": True},
            "fs.write": {"risk": "MEDIUM", "allow": True, "max_bytes": 1024 * 1024},
            "fs.delete": {"risk": "CRITICAL", "allow": False, "requires_pccap": True},
            "shell.exec": {"risk": "CRITICAL", "allow": False},
        },
        "pccap": {
            "default_ttl_seconds": 300,
            "max_ttl_seconds": 3600,
        },
    }
    policy_file.write_text(json.dumps(policy, indent=2))
    print(f"Policy written to {policy_file}")
    print()

    # Create scratch directory for fs operations
    scratch_dir = work_dir / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    (scratch_dir / "test_file.txt").write_text("This is a test file for CSP demos.\n")
    print(f"Scratch directory: {scratch_dir}")
    print()

    print("Quickstart complete!")
    print()
    print("Next steps:")
    print(f"  1. Run: python tools/csp_helper.py demo --work-dir {work_dir}")
    print("  2. Read IMPLEMENTORS.md for integration guidance")
    print("  3. Run: pytest tests/ to verify the implementation")

    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Interactive demo of CSP capabilities."""
    print("=" * 60)
    print("CSP Tool Safety Profile — PCCap Demo")
    print("=" * 60)
    print()

    scenario = args.scenario
    if scenario == "fs-delete":
        return demo_fs_delete(args)
    elif scenario == "capability-mint":
        return demo_capability_mint(args)
    elif scenario == "full-flow":
        return demo_full_flow(args)
    else:
        print(f"Unknown scenario: {scenario}")
        print("Available scenarios: fs-delete, capability-mint, full-flow")
        return 1


def demo_fs_delete(args: argparse.Namespace) -> int:
    """Demo: fs.delete with PCCap authorization."""
    print("Scenario: fs.delete with PCCap")
    print("-" * 40)
    print()

    # Setup
    work_dir = Path(args.work_dir) if args.work_dir else Path(tempfile.mkdtemp(prefix="csp_demo_"))
    work_dir.mkdir(parents=True, exist_ok=True)

    scratch_dir = work_dir / "scratch"
    scratch_dir.mkdir(exist_ok=True)

    test_file = scratch_dir / "deletable.txt"
    test_file.write_text("This file will be deleted by the demo.\n")

    print(f"Created test file: {test_file}")
    print()

    # Initialize keyring and engine
    keyring = Keyring()
    engine = PCCapPolicyEngine(keyring=keyring)

    # Define actors
    agent = Principal(sub="agent@demo.local", actor_type="agent")
    admin = "admin@demo.local"

    print("Step 1: Agent requests fs.delete without PCCap")
    print("-" * 40)

    allowed, reason, code = engine.evaluate_with_pccap(
        principal=agent,
        tool_name="fs.delete",
        arguments={"path": str(test_file)},
    )
    print(f"  Decision: {'ALLOW' if allowed else 'DENY'}")
    print(f"  Reason: {reason}")
    print(f"  Code: {code}")
    print()

    print("Step 2: Admin mints PCCap for agent")
    print("-" * 40)

    scope = PCCapScope(
        tool_name="fs.delete",
        path_prefix=str(scratch_dir),
    )
    token = engine.mint(
        principal=agent,
        scope=scope,
        issued_by=admin,
        ttl_seconds=60,
    )

    print(f"  Token ID: {token.token_id}")
    print(f"  Scope: {scope.to_dict()}")
    print(f"  Expires: {time.ctime(token.expires_at)}")
    print()

    print("Step 3: Agent requests fs.delete WITH PCCap")
    print("-" * 40)

    allowed, reason, code = engine.evaluate_with_pccap(
        principal=agent,
        tool_name="fs.delete",
        arguments={"path": str(test_file)},
        token_id=token.token_id,
    )
    print(f"  Decision: {'ALLOW' if allowed else 'DENY'}")
    print(f"  Reason: {reason}")
    print(f"  Code: {code}")
    print()

    if allowed:
        print("Step 4: Execute the delete (simulation)")
        print("-" * 40)
        if test_file.exists():
            test_file.unlink()
            print(f"  Deleted: {test_file}")
        else:
            print(f"  File already deleted: {test_file}")
        print()

    print("Step 5: Verify scope constraints")
    print("-" * 40)

    # Try to delete outside allowed path
    forbidden_path = "/etc/passwd"
    allowed2, reason2, code2 = engine.evaluate_with_pccap(
        principal=agent,
        tool_name="fs.delete",
        arguments={"path": forbidden_path},
        token_id=token.token_id,
    )
    print(f"  Attempt to delete {forbidden_path}:")
    print(f"  Decision: {'ALLOW' if allowed2 else 'DENY'}")
    print(f"  Reason: {reason2}")
    print()

    print("Demo complete!")
    print()
    print("Key takeaways:")
    print("  - CRITICAL operations are denied by default")
    print("  - PCCap tokens grant scoped, time-limited capabilities")
    print("  - Scope constraints prevent privilege escalation")

    return 0


def demo_capability_mint(args: argparse.Namespace) -> int:
    """Demo: Show PCCap minting and verification."""
    print("Scenario: PCCap Minting and Verification")
    print("-" * 40)
    print()

    keyring = Keyring()

    agent = Principal(sub="agent@demo.local", actor_type="agent")
    admin = "admin@demo.local"

    print("Minting PCCap token...")
    token = mint_pccap_fs_delete(
        principal=agent,
        path_prefix="/tmp/demo",
        issued_by=admin,
        keyring=keyring,
        ttl_seconds=300,
    )

    print()
    print("Token details:")
    print(json.dumps(token.to_dict(), indent=2, default=str))
    print()

    print("Verification tests:")
    print("-" * 40)

    # Valid verification
    allowed, reason, code = enforce_pccap_for_fs_delete(
        principal=agent,
        path="/tmp/demo/file.txt",
        token=token,
        keyring=keyring,
    )
    print(f"  Valid path: {code.value} - {reason}")

    # Invalid path
    allowed, reason, code = enforce_pccap_for_fs_delete(
        principal=agent,
        path="/etc/shadow",
        token=token,
        keyring=keyring,
    )
    print(f"  Invalid path: {code.value} - {reason}")

    # Wrong principal
    other = Principal(sub="other@demo.local", actor_type="agent")
    allowed, reason, code = enforce_pccap_for_fs_delete(
        principal=other,
        path="/tmp/demo/file.txt",
        token=token,
        keyring=keyring,
    )
    print(f"  Wrong principal: {code.value} - {reason}")

    return 0


def demo_full_flow(args: argparse.Namespace) -> int:
    """Demo: Complete flow from policy check to execution."""
    print("Scenario: Full PCCap Flow")
    print("-" * 40)
    print()

    print("This demo shows the complete flow:")
    print("  1. Policy evaluates request -> DENY (requires capability)")
    print("  2. Request escalated to human reviewer")
    print("  3. Human mints scoped PCCap")
    print("  4. Agent retries with PCCap -> ALLOW")
    print("  5. Action executed with receipt")
    print()

    # Setup
    keyring = Keyring()
    engine = PCCapPolicyEngine(keyring=keyring)

    agent = Principal(sub="agent@demo.local", actor_type="agent")
    human = "reviewer@demo.local"

    target_path = "/tmp/demo/important_file.txt"
    scope_prefix = "/tmp/demo"

    print("=" * 60)
    print("Phase 1: Initial Request")
    print("=" * 60)
    print(f"Agent requests: fs.delete(path={target_path})")
    print()

    allowed, reason, code = engine.evaluate_with_pccap(
        principal=agent,
        tool_name="fs.delete",
        arguments={"path": target_path},
    )

    print(f"Gateway decision: {code}")
    print(f"Reason: {reason}")
    print()

    if not allowed:
        print("=" * 60)
        print("Phase 2: Human Review")
        print("=" * 60)
        print(f"Request escalated to: {human}")
        print(f"Agent: {agent.sub}")
        print(f"Tool: fs.delete")
        print(f"Args: path={target_path}")
        print()
        print("[Human reviews and approves with scope constraint]")
        print(f"Approved scope: fs.delete under {scope_prefix}")
        print()

        scope = PCCapScope(tool_name="fs.delete", path_prefix=scope_prefix)
        token = engine.mint(
            principal=agent,
            scope=scope,
            issued_by=human,
            ttl_seconds=300,
        )

        print(f"PCCap minted: {token.token_id}")
        print(f"Expires: {time.ctime(token.expires_at)}")
        print()

        print("=" * 60)
        print("Phase 3: Retry with PCCap")
        print("=" * 60)

        allowed, reason, code = engine.evaluate_with_pccap(
            principal=agent,
            tool_name="fs.delete",
            arguments={"path": target_path},
            token_id=token.token_id,
        )

        print(f"Gateway decision: {code}")
        print(f"Reason: {reason}")
        print()

        if allowed:
            print("=" * 60)
            print("Phase 4: Execute with Receipt")
            print("=" * 60)

            receipt = {
                "receipt_id": "rcpt_demo_001",
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "principal": agent.to_dict(),
                "tool": "fs.delete",
                "args_hash": "sha256:...",
                "decision": "ALLOW",
                "pccap_token_id": token.token_id,
                "outcome": "success",
            }

            print("Receipt emitted:")
            print(json.dumps(receipt, indent=2))

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="CSP Tool Safety Helper CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize a CSP environment
  python tools/csp_helper.py quickstart

  # Run PCCap demo
  python tools/csp_helper.py demo --scenario fs-delete

  # Show full flow
  python tools/csp_helper.py demo --scenario full-flow
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Quickstart
    qs_parser = subparsers.add_parser("quickstart", help="Initialize CSP environment")
    qs_parser.add_argument(
        "--work-dir",
        help="Working directory (default: temp dir)",
    )

    # Demo
    demo_parser = subparsers.add_parser("demo", help="Run interactive demo")
    demo_parser.add_argument(
        "--scenario",
        default="fs-delete",
        choices=["fs-delete", "capability-mint", "full-flow"],
        help="Demo scenario to run",
    )
    demo_parser.add_argument(
        "--work-dir",
        help="Working directory for demo files",
    )

    args = parser.parse_args()

    if args.command == "quickstart":
        return cmd_quickstart(args)
    elif args.command == "demo":
        return cmd_demo(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
