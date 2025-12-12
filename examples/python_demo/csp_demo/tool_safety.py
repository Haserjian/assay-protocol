from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Risk = str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"


# -------------------- helpers --------------------

def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_filename_ts() -> str:
    """Timestamp safe for filenames on all platforms (no colons)."""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def canonical_json(obj: Any) -> bytes:
    # Demo-grade canonicalization (stable keys + compact separators).
    # Not full RFC 8785 JCS, but deterministic for local proof.
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def compute_receipt_hash(receipt_dict: Dict[str, Any]) -> str:
    # Hash is computed over receipt without the receipt_hash field (avoids circularity).
    d = dict(receipt_dict)
    d.pop("receipt_hash", None)
    return f"sha256:{sha256_hex(canonical_json(d))}"


# -------------------- patterns (minimum baseline) --------------------
# NOTE: Demo-grade patterns. Production implementations should use more
# comprehensive pattern sets and consider context-aware classification.

CRITICAL_PATTERNS = [
    # Root/home deletion - can't use \b after / or ~ (not word chars)
    r"rm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f[a-zA-Z]*\s+/\s*$",  # rm -rf /
    r"rm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f[a-zA-Z]*\s+~\s*$",  # rm -rf ~
    r"rm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f[a-zA-Z]*\s+/[^v\s]",  # rm -rf /etc, /usr, etc. (but not /var/cache/...)
    r"\bDROP\s+DATABASE\b",
    r"\bDROP\s+TABLE\b",
    r"\bmkfs\b|\bfdisk\b",
    r"\bdd\s+if=/dev/zero\b",
    r"\b(curl|wget)\b.*\|\s*(ba)?sh\b",
    r"\bchmod\s+.*-R\s+.*777\s+/\s*$",
]

HIGH_PATTERNS = [
    r"\brm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f",  # any rm -rf (but not root, caught above)
    r"\bgit\s+push\s+.*--force\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)",
    r"\bTRUNCATE\s+TABLE\b",
    r"\brsync\b.*--delete\b",
]


def classify(tool: str, command: str) -> Tuple[Risk, Optional[str]]:
    s = command.strip()
    for pat in CRITICAL_PATTERNS:
        if re.search(pat, s, flags=re.IGNORECASE):
            return "CRITICAL", pat
    for pat in HIGH_PATTERNS:
        if re.search(pat, s, flags=re.IGNORECASE):
            return "HIGH", pat
    # Simple demo heuristic:
    if tool in {"shell", "db", "http"}:
        return "MEDIUM", None
    return "LOW", None


# -------------------- domain types --------------------

@dataclass(frozen=True)
class ToolAction:
    tool: str               # "shell" | "db" | "http" etc.
    command: str
    scope: Optional[str] = None  # path/host/db/table/namespace


@dataclass(frozen=True)
class PlanStep:
    tool: str
    command: str
    scope: str
    risk: Risk


@dataclass(frozen=True)
class ToolPlan:
    summary: str
    steps: List[PlanStep]
    subject: str = "user"
    signature: Optional[str] = None  # Court-grade later


@dataclass(frozen=True)
class GuardianVerdict:
    verdict: str  # "ALLOW" | "DENY" | "ESCALATE"
    rationale: str
    authority: str = "guardian:demo"


# -------------------- receipts store --------------------

class ReceiptStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, episode_id: str, receipt: Dict[str, Any]) -> Path:
        ep_dir = self.root / episode_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        # Filename uses safe timestamp (no colons) for Windows compatibility
        safe_ts = safe_filename_ts()
        out = ep_dir / f"{safe_ts}.{receipt['receipt_type']}.{receipt['receipt_id']}.json"
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return out


class Episode:
    def __init__(self, store: ReceiptStore, episode_id: str):
        self.store = store
        self.episode_id = episode_id
        self.parent_hash: Optional[str] = None

    def emit(self, receipt_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "receipt_id": new_id("rcpt"),
            "receipt_type": receipt_type,
            "ts": iso_utc_now(),
            "episode_id": self.episode_id,
            "parent_hash": self.parent_hash,
            **payload,
        }
        base["receipt_hash"] = compute_receipt_hash(base)
        self.store.write(self.episode_id, base)
        self.parent_hash = base["receipt_hash"]
        return base


# -------------------- tool safety wrapper (demo-grade) --------------------

class CSPToolSafetyDemo:
    """
    Demo-grade Tool Safety Wrapper.
    - Does NOT execute real commands.
    - Simulates execution and emits receipts.
    """

    def __init__(self, mode: str, receipts_root: Path):
        assert mode in {"basic", "standard"}, "mode must be basic|standard"
        self.mode = mode
        self.store = ReceiptStore(receipts_root)

    def new_episode(self) -> Episode:
        return Episode(self.store, episode_id=new_id("ep"))

    def submit_plan(self, ep: Episode, plan: ToolPlan) -> Dict[str, Any]:
        return ep.emit(
            "csp.tool_safety.plan.v1",
            {
                "plan_id": new_id("plan"),
                "subject": plan.subject,
                "summary": plan.summary,
                "steps": [
                    {"tool": s.tool, "command": s.command, "scope": s.scope, "risk": s.risk}
                    for s in plan.steps
                ],
                "signature": plan.signature,
            },
        )

    def guardian_verdict(self, ep: Episode, plan_receipt: Dict[str, Any], verdict: GuardianVerdict) -> Dict[str, Any]:
        return ep.emit(
            "csp.tool_safety.verdict.v1",
            {
                "verdict_id": new_id("verdict"),
                "plan_id": plan_receipt["plan_id"],
                "plan_hash": plan_receipt["receipt_hash"],  # binding
                "verdict": verdict.verdict,
                "rationale": verdict.rationale,
                "authority": verdict.authority,
            },
        )

    def attempt_action(
        self,
        ep: Episode,
        action: ToolAction,
        plan_receipt: Optional[Dict[str, Any]] = None,
        verdict_receipt: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        risk, matched = classify(action.tool, action.command)
        action_id = new_id("act")

        # Always emit attempt receipt
        ep.emit(
            "csp.tool_safety.action.v1",
            {
                "action_id": action_id,
                "tool": action.tool,
                "command": action.command,
                "scope": action.scope,
                "risk_level": risk,
                "pattern_matched": matched,
                "outcome": "attempted",
            },
        )

        if self.mode == "basic":
            # Basic: block CRITICAL patterns, allow otherwise (audit-only)
            if risk == "CRITICAL":
                return self._refuse(ep, action_id, action, risk, matched, "amendment_vii_no_plan",
                                    "CRITICAL blocked in Basic. Upgrade to Standard for plan+guardian.")
            return self._execute(ep, action_id, action, risk, plan_id=None, verdict_id=None)

        # Standard: HIGH/CRITICAL require plan + Guardian ALLOW + scope match
        if risk in {"HIGH", "CRITICAL"}:
            if plan_receipt is None:
                return self._refuse(ep, action_id, action, risk, matched, "amendment_vii_no_plan",
                                    "Provide ToolPlanReceipt and obtain Guardian ALLOW.")
            if verdict_receipt is None or verdict_receipt.get("verdict") != "ALLOW":
                return self._refuse(ep, action_id, action, risk, matched, "amendment_vii_no_guardian_verdict",
                                    "Missing Guardian ALLOW verdict.")
            if verdict_receipt.get("plan_hash") != plan_receipt.get("receipt_hash"):
                return self._refuse(ep, action_id, action, risk, matched, "amendment_vii_no_guardian_verdict",
                                    "Verdict not bound to this plan (plan_hash mismatch).")
            if not self._scope_allows(plan_receipt, action):
                return self._refuse(ep, action_id, action, risk, matched, "amendment_vii_scope_mismatch",
                                    "Action not covered by plan scope/tool/risk.")
            return self._execute(ep, action_id, action, risk, plan_id=plan_receipt["plan_id"], verdict_id=verdict_receipt["verdict_id"])

        # LOW/MEDIUM: allowed
        return self._execute(ep, action_id, action, risk, plan_id=None, verdict_id=None)

    def _scope_allows(self, plan_receipt: Dict[str, Any], action: ToolAction) -> bool:
        """
        Demo-grade scope check using glob/fnmatch.
        Production implementations should use stricter path canonicalization
        and consider symlink attacks, path traversal, etc.
        """
        if action.scope is None:
            return False
        for step in plan_receipt.get("steps", []):
            if step["tool"] != action.tool:
                continue
            step_scope = step.get("scope")
            if not step_scope:
                continue
            # glob matching allowed
            if fnmatch(action.scope, step_scope) or fnmatch(step_scope, action.scope) or action.scope.startswith(step_scope.rstrip("*")):
                # risk ceiling: action risk must not exceed planned risk
                action_risk, _ = classify(action.tool, action.command)
                if self._rank(action_risk) <= self._rank(step["risk"]):
                    return True
        return False

    def _rank(self, r: Risk) -> int:
        return {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}[r]

    def _refuse(self, ep: Episode, action_id: str, action: ToolAction, risk: Risk, matched: Optional[str], reason: str, hint: str) -> Dict[str, Any]:
        receipt = ep.emit(
            "csp.tool_safety.refusal.v1",
            {
                "refusal_id": new_id("ref"),
                "action_id": action_id,
                "reason": reason,
                "amendment_cited": "VII",
                "risk_level": risk,
                "pattern_matched": matched,
                "tool": action.tool,
                "command": action.command,
                "scope": action.scope,
                "remediation_hint": hint,
            },
        )
        return {"status": "REFUSED", "reason": reason, "receipt": receipt}

    def _execute(self, ep: Episode, action_id: str, action: ToolAction, risk: Risk, plan_id: Optional[str], verdict_id: Optional[str]) -> Dict[str, Any]:
        receipt = ep.emit(
            "csp.tool_safety.execution.v1",
            {
                "execution_id": new_id("exec"),
                "action_id": action_id,
                "tool": action.tool,
                "command": action.command,
                "scope": action.scope,
                "risk_level": risk,
                "outcome": "executed_simulated",
                "plan_id": plan_id,
                "verdict_id": verdict_id,
            },
        )
        return {"status": "EXECUTED_SIMULATED", "receipt": receipt}
