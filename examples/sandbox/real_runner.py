#!/usr/bin/env python3
"""
Real-execution sandbox runner for CSP Tool Safety.

Runs **real filesystem deletes** inside a sandbox directory, gated by:
- Basic: block CRITICAL deletes (sandbox root), allow HIGH deletes with receipts
- Standard: require plan + Guardian ALLOW for HIGH/CRITICAL deletes

Outputs receipts to .csp_real_receipts/<episode_id>/.

SAFETY:
- Never run with sudo.
- Sandbox root defaults to /tmp/csp_sandbox.
- By default, only /tmp (or /private/tmp on macOS) sandbox roots are allowed.
- Use --unsafe-allow-any-sandbox-root to override (dangerous!).
"""
from __future__ import annotations

import argparse
import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Optional


# -------------------- helpers --------------------

def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_filename_ts() -> str:
    # Windows-safe timestamp (no colons)
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def canonical_json(obj: Any) -> bytes:
    # Demo-grade canonicalization (deterministic). Not full RFC 8785 JCS.
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def receipt_hash(d: Dict[str, Any]) -> str:
    dd = dict(d)
    dd.pop("receipt_hash", None)
    return "sha256:" + sha256(canonical_json(dd)).hexdigest()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# -------------------- receipts --------------------

class ReceiptStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, episode_id: str, r: Dict[str, Any]) -> Path:
        ep = self.root / episode_id
        ep.mkdir(parents=True, exist_ok=True)
        p = ep / f"{safe_filename_ts()}.{r['receipt_type']}.{r['receipt_id']}.json"
        p.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return p


@dataclass
class Context:
    mode: str                      # "basic" | "standard"
    episode_id: str
    receipts_root: Path
    sandbox_root: Path
    parent_hash: Optional[str] = None


def emit(store: ReceiptStore, ctx: Context, receipt_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = {
        "receipt_id": new_id("rcpt"),
        "receipt_type": receipt_type,
        "ts": iso_utc_now(),
        "episode_id": ctx.episode_id,
        "parent_hash": ctx.parent_hash,
        **payload,
    }
    r["receipt_hash"] = receipt_hash(r)
    store.write(ctx.episode_id, r)
    ctx.parent_hash = r["receipt_hash"]
    return r


# -------------------- classification --------------------

SAFE_SANDBOX_PREFIXES = ("/tmp", "/private/tmp", "/var/tmp")


def validate_sandbox_root(sandbox_root: Path, allow_unsafe: bool) -> None:
    """Refuse dangerous sandbox roots unless --unsafe-allow-any-sandbox-root is set."""
    resolved = sandbox_root.resolve()
    if allow_unsafe:
        return
    for prefix in SAFE_SANDBOX_PREFIXES:
        try:
            resolved.relative_to(prefix)
            return  # Safe
        except ValueError:
            continue
    raise SystemExit(
        f"ERROR: Sandbox root '{resolved}' is outside safe prefixes {SAFE_SANDBOX_PREFIXES}.\n"
        f"Use --unsafe-allow-any-sandbox-root to override (DANGEROUS)."
    )


def ensure_under_root(root: Path, target: Path) -> Path:
    root = root.resolve()
    target = target.resolve()
    if root == target:
        return target
    if root not in target.parents:
        raise ValueError(f"Path escapes sandbox root: {target} (root={root})")
    return target


def classify_fs_delete(target: Path, sandbox_root: Path) -> str:
    # In demo: deleting sandbox root is CRITICAL; deleting inside is HIGH.
    target = target.resolve()
    if target == sandbox_root.resolve():
        return "CRITICAL"
    return "HIGH"


# -------------------- receipts emitters --------------------

def refuse(store: ReceiptStore, ctx: Context, action_id: str, reason: str, risk: str, tool: str, scope: str, hint: str) -> Dict[str, Any]:
    return emit(
        store,
        ctx,
        "csp.tool_safety.refusal.v1",
        {
            "action_id": action_id,
            "reason": reason,
            "amendment_cited": "VII",
            "risk_level": risk,
            "tool": tool,
            "scope": scope,
            "remediation_hint": hint,
        },
    )


def execute_delete_real(store: ReceiptStore, ctx: Context, target: Path, plan_id: Optional[str], verdict_id: Optional[str]) -> Dict[str, Any]:
    # REAL deletion (only allowed inside sandbox)
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink(missing_ok=True)

    return emit(
        store,
        ctx,
        "csp.tool_safety.execution.v1",
        {
            "tool": "fs_delete",
            "scope": str(target),
            "risk_level": "HIGH",
            "outcome": "executed_real",
            "plan_id": plan_id,
            "verdict_id": verdict_id,
        },
    )


# -------------------- plan handling --------------------

def load_json(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


RISK_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def plan_allows_delete(plan: Dict[str, Any], target: Path, action_risk: str) -> tuple[bool, str]:
    """
    Check if plan allows the delete action.
    Returns (allowed: bool, reason: str).
    Enforces: scope match AND action_risk <= plan_risk (risk ceiling).
    """
    target_resolved = target.resolve()
    steps = plan.get("steps") or []
    for s in steps:
        if s.get("tool") != "fs_delete":
            continue
        scope = s.get("scope")
        if not scope:
            continue
        # Normalize scope for /tmp -> /private/tmp differences
        scope_match = False
        if scope.endswith("*"):
            prefix = Path(scope[:-1]).resolve()
            try:
                target_resolved.relative_to(prefix)
                scope_match = True
            except ValueError:
                continue
        else:
            if target_resolved == Path(scope).resolve():
                scope_match = True

        if scope_match:
            # Enforce risk ceiling: action risk must not exceed planned risk
            plan_risk = s.get("risk", "HIGH")
            if RISK_RANK.get(action_risk, 0) > RISK_RANK.get(plan_risk, 0):
                return False, f"action risk {action_risk} exceeds plan risk {plan_risk}"
            return True, ""
    return False, "target not covered by plan scope"


# -------------------- main --------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="CSP Tool Safety real-execution demo (sandboxed filesystem delete).")
    ap.add_argument("--mode", choices=["basic", "standard"], default="basic")
    ap.add_argument("--sandbox-root", default="/tmp/csp_sandbox")
    ap.add_argument("--receipts-root", default=".csp_real_receipts")
    ap.add_argument("--episode", default=None)
    ap.add_argument("--unsafe-allow-any-sandbox-root", action="store_true",
                    help="Allow sandbox roots outside /tmp (DANGEROUS)")

    ap.add_argument("--plan", default=None, help="Path to ToolPlanReceipt JSON (standard for HIGH/CRITICAL)")
    ap.add_argument("--verdict", default=None, help="Path to GuardianVerdictReceipt JSON (standard for HIGH/CRITICAL)")

    sub = ap.add_subparsers(dest="cmd", required=True)

    p_del = sub.add_parser("fs_delete", help="Delete a file/dir (REAL), sandboxed")
    p_del.add_argument("--path", required=True)

    p_mkplan = sub.add_parser("make_plan", help="Create a minimal ToolPlanReceipt JSON for a delete scope")
    p_mkplan.add_argument("--scope", required=True, help='e.g. "/tmp/csp_sandbox/old/*"')
    p_mkplan.add_argument("--risk", choices=["HIGH", "CRITICAL"], default="HIGH", help="Risk level for the plan step")
    p_mkplan.add_argument("--out", required=True)

    p_allow = sub.add_parser("make_allow", help="Create a minimal GuardianVerdictReceipt (ALLOW) bound to a plan")
    p_allow.add_argument("--plan", required=True)
    p_allow.add_argument("--out", required=True)
    p_allow.add_argument("--rationale", default="Demo ALLOW")

    args = ap.parse_args()

    receipts_root = Path(args.receipts_root)
    sandbox_root = Path(args.sandbox_root)

    episode_id = args.episode or new_id("ep")
    store = ReceiptStore(receipts_root)
    ctx = Context(mode=args.mode, episode_id=episode_id, receipts_root=receipts_root, sandbox_root=sandbox_root)

    if args.cmd == "make_plan":
        plan = {
            "receipt_type": "csp.tool_safety.plan.v1",
            "receipt_id": new_id("plan"),
            "ts": iso_utc_now(),
            "episode_id": episode_id,
            "steps": [
                {
                    "tool": "fs_delete",
                    "scope": args.scope,
                    "risk": args.risk,
                }
            ],
        }
        plan["receipt_hash"] = receipt_hash(plan)
        Path(args.out).write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote plan: {args.out}")
        print(f"Episode: {episode_id}")
        return

    if args.cmd == "make_allow":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        v = {
            "receipt_type": "csp.tool_safety.verdict.v1",
            "receipt_id": new_id("verdict"),
            "ts": iso_utc_now(),
            "episode_id": episode_id,
            "plan_id": plan.get("receipt_id"),
            "plan_hash": plan.get("receipt_hash"),
            "verdict": "ALLOW",
            "rationale": args.rationale,
        }
        v["receipt_hash"] = receipt_hash(v)
        Path(args.out).write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote verdict: {args.out}")
        print(f"Episode: {episode_id}")
        return

    if args.cmd == "fs_delete":
        # Validate sandbox root before any file operations
        validate_sandbox_root(sandbox_root, args.unsafe_allow_any_sandbox_root)

        action_id = new_id("act")
        target = ensure_under_root(sandbox_root, Path(args.path))
        risk = classify_fs_delete(target, sandbox_root)

        emit(
            store,
            ctx,
            "csp.tool_safety.action.v1",
            {
                "action_id": action_id,
                "tool": "fs_delete",
                "scope": str(target),
                "risk_level": risk,
                "outcome": "attempted",
            },
        )

        # Basic: block CRITICAL deletes, allow HIGH deletes (still receipted)
        if args.mode == "basic":
            if risk == "CRITICAL":
                refuse(
                    store,
                    ctx,
                    action_id,
                    "amendment_vii_no_plan",
                    risk,
                    "fs_delete",
                    str(target),
                    "CRITICAL blocked in Basic. Use Standard with plan+verdict.",
                )
                print("REFUSED (basic): CRITICAL delete blocked")
                print(f"Receipts: {receipts_root.resolve() / episode_id}")
                return
            execute_delete_real(store, ctx, target, plan_id=None, verdict_id=None)
            print("EXECUTED REAL (basic) delete:", target)
            print(f"Receipts: {receipts_root.resolve() / episode_id}")
            return

        # Standard: HIGH/CRITICAL require plan + ALLOW
        plan = load_json(args.plan)
        verdict = load_json(args.verdict)

        if not plan:
            refuse(
                store,
                ctx,
                action_id,
                "amendment_vii_no_plan",
                risk,
                "fs_delete",
                str(target),
                "Provide ToolPlanReceipt + Guardian ALLOW.",
            )
            print("REFUSED (standard): no plan")
            print(f"Receipts: {receipts_root.resolve() / episode_id}")
            return

        if not verdict or verdict.get("verdict") != "ALLOW":
            refuse(
                store,
                ctx,
                action_id,
                "amendment_vii_no_guardian_verdict",
                risk,
                "fs_delete",
                str(target),
                "Provide Guardian ALLOW verdict.",
            )
            print("REFUSED (standard): no ALLOW verdict")
            print(f"Receipts: {receipts_root.resolve() / episode_id}")
            return

        if verdict.get("plan_hash") != plan.get("receipt_hash"):
            refuse(
                store,
                ctx,
                action_id,
                "amendment_vii_no_guardian_verdict",
                risk,
                "fs_delete",
                str(target),
                "Verdict not bound to this plan (plan_hash mismatch).",
            )
            print("REFUSED (standard): plan_hash mismatch")
            print(f"Receipts: {receipts_root.resolve() / episode_id}")
            return

        allowed, reason = plan_allows_delete(plan, target, risk)
        if not allowed:
            refuse(
                store,
                ctx,
                action_id,
                "amendment_vii_scope_mismatch",
                risk,
                "fs_delete",
                str(target),
                f"Plan check failed: {reason}",
            )
            print(f"REFUSED (standard): {reason}")
            print(f"Receipts: {receipts_root.resolve() / episode_id}")
            return

        execute_delete_real(
            store,
            ctx,
            target,
            plan_id=plan.get("receipt_id"),
            verdict_id=verdict.get("receipt_id"),
        )
        print("EXECUTED REAL (standard) delete:", target)
        print(f"Receipts: {receipts_root.resolve() / episode_id}")
        return


if __name__ == "__main__":
    main()
