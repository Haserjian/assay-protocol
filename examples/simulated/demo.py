#!/usr/bin/env python3
"""
CSP Tool Safety Demo - Proof of Concept

Demonstrates:
1. CRITICAL without plan -> REFUSED (amendment_vii_no_plan)
2. Plan + Guardian ALLOW -> EXECUTED_SIMULATED
3. Scope mismatch -> REFUSED (amendment_vii_scope_mismatch)
4. Plan but missing verdict -> REFUSED (amendment_vii_no_guardian_verdict)

All receipts are written to .csp_demo_receipts/<episode_id>/
"""
from __future__ import annotations

from pathlib import Path
from csp_demo.tool_safety import CSPToolSafetyDemo, ToolAction, ToolPlan, PlanStep, GuardianVerdict


def main() -> None:
    receipts_root = Path(".csp_demo_receipts")
    demo = CSPToolSafetyDemo(mode="standard", receipts_root=receipts_root)
    ep = demo.new_episode()

    print(f"\nEpisode: {ep.episode_id}")
    print(f"Receipts: {receipts_root.resolve() / ep.episode_id}\n")

    # Scenario 1: CRITICAL without plan -> refuse
    print("=== 1) CRITICAL without plan (expect REFUSED: amendment_vii_no_plan) ===")
    out1 = demo.attempt_action(ep, ToolAction(tool="shell", command="rm -rf /", scope="/"))
    print(f"   {out1['status']} {out1.get('reason', '')}")

    # Prepare an approved plan + verdict
    plan = ToolPlan(
        summary="Delete old cache files under /var/cache/old/*",
        steps=[PlanStep(tool="shell", command="rm -rf /var/cache/old/*", scope="/var/cache/old/*", risk="CRITICAL")],
    )
    plan_rcpt = demo.submit_plan(ep, plan)
    verdict_rcpt = demo.guardian_verdict(ep, plan_rcpt, GuardianVerdict(verdict="ALLOW", rationale="Scoped cache cleanup approved."))

    # Scenario 2: Allowed action within plan scope -> execute simulated
    print("\n=== 2) Plan + Guardian ALLOW (expect EXECUTED_SIMULATED) ===")
    out2 = demo.attempt_action(
        ep,
        ToolAction(tool="shell", command="rm -rf /var/cache/old/*", scope="/var/cache/old/tmp123"),
        plan_receipt=plan_rcpt,
        verdict_receipt=verdict_rcpt,
    )
    print(f"   {out2['status']}")

    # Scenario 3: Scope mismatch -> refuse
    print("\n=== 3) Scope mismatch (expect REFUSED: amendment_vii_scope_mismatch) ===")
    out3 = demo.attempt_action(
        ep,
        ToolAction(tool="shell", command="rm -rf /etc/*", scope="/etc/*"),
        plan_receipt=plan_rcpt,
        verdict_receipt=verdict_rcpt,
    )
    print(f"   {out3['status']} {out3.get('reason', '')}")

    # Scenario 4: Plan but missing verdict -> refuse
    print("\n=== 4) Plan but missing verdict (expect REFUSED: amendment_vii_no_guardian_verdict) ===")
    out4 = demo.attempt_action(
        ep,
        ToolAction(tool="shell", command="rm -rf /var/cache/old/*", scope="/var/cache/old/tmp456"),
        plan_receipt=plan_rcpt,
        verdict_receipt=None,
    )
    print(f"   {out4['status']} {out4.get('reason', '')}")

    print("\nDone. Verify receipts with:")
    print(f"   python3 examples/simulated/verify_episode.py {receipts_root / ep.episode_id}\n")


if __name__ == "__main__":
    main()
