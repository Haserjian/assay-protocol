#!/usr/bin/env python3
"""
CSP Receipt Verifier

Verifies:
1. Each receipt's hash is correct (integrity)
2. parent_hash forms a valid chain (ordering)
3. Verdicts bind to plans (plan_hash matches)

Usage:
    python3 examples/python_demo/verify_episode.py .csp_demo_receipts/<episode_id>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from csp_demo.tool_safety import compute_receipt_hash


def load_receipts(ep_dir: Path) -> List[Dict[str, Any]]:
    files = sorted(ep_dir.glob("*.json"))
    receipts = []
    for f in files:
        receipts.append(json.loads(f.read_text(encoding="utf-8")))
    return receipts


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 examples/python_demo/verify_episode.py .csp_demo_receipts/<episode_id>")
        sys.exit(2)

    ep_dir = Path(sys.argv[1])
    if not ep_dir.exists() or not ep_dir.is_dir():
        print(f"Not a directory: {ep_dir}")
        sys.exit(2)

    receipts = load_receipts(ep_dir)
    if not receipts:
        print("No receipts found.")
        sys.exit(1)

    print(f"Verifying {len(receipts)} receipts in {ep_dir}...\n")

    # 1) Verify receipt_hash correctness
    for r in receipts:
        expected = compute_receipt_hash(r)
        if r.get("receipt_hash") != expected:
            print(f"FAIL: BAD HASH on {r.get('receipt_id')}")
            print(f"      expected: {expected}")
            print(f"      got:      {r.get('receipt_hash')}")
            sys.exit(1)
    print(f"[OK] All {len(receipts)} receipt hashes valid")

    # 2) Verify parent_hash chain (sequential)
    prev = None
    for r in receipts:
        if r.get("parent_hash") != prev:
            print(f"FAIL: BAD CHAIN at {r.get('receipt_id')}")
            print(f"      parent_hash={r.get('parent_hash')}")
            print(f"      expected={prev}")
            sys.exit(1)
        prev = r.get("receipt_hash")
    print(f"[OK] Receipt chain valid (parent_hash linkage)")

    # 3) Verify verdict binds to plan (if both exist)
    plan_hashes = {r["receipt_hash"] for r in receipts if r.get("receipt_type") == "csp.tool_safety.plan.v1"}
    verdicts = [r for r in receipts if r.get("receipt_type") == "csp.tool_safety.verdict.v1"]
    for v in verdicts:
        if v.get("plan_hash") not in plan_hashes:
            print(f"FAIL: VERDICT NOT BOUND to plan")
            print(f"      verdict: {v.get('receipt_id')}")
            print(f"      plan_hash: {v.get('plan_hash')}")
            sys.exit(1)
    if verdicts:
        print(f"[OK] {len(verdicts)} verdict(s) correctly bound to plans")

    print(f"\nVERIFIED: hashes valid, chain valid, verdicts bound.")


if __name__ == "__main__":
    main()
