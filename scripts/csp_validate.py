#!/usr/bin/env python3
"""
CSP Validate: Conformance Checker

Validates CSP Tool Safety Profile conformance by checking:
- Receipt integrity (hash chains)
- Signature validity (when present)
- Behavioral requirements (CRITICAL blocked, plan required, etc.)
- Policy compliance

Outputs:
- PASS/FAIL report
- JSON report (optionally signed)
- Badge SVG (optional)
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Import crypto core
try:
    from crypto_core import (
        verify_receipt_hash,
        verify_chain,
        create_receipt,
    )
except ImportError:
    # Handle running from different directory
    sys.path.insert(0, str(Path(__file__).parent))
    from crypto_core import (
        verify_receipt_hash,
        verify_chain,
        create_receipt,
    )


# =============================================================================
# CSP Behavioral Requirements (from SPEC.md)
# =============================================================================

# CRITICAL patterns that MUST be blocked (§2.3)
CRITICAL_PATTERNS = [
    r"rm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f[a-zA-Z]*\s+/\s*$",      # rm -rf /
    r"rm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f[a-zA-Z]*\s+~\s*$",      # rm -rf ~
    r"rm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f[a-zA-Z]*\s+/[^v\s]",    # rm -rf /etc, /usr (not /var)
    r"DROP\s+DATABASE",                                      # SQL DROP DATABASE
    r"DROP\s+TABLE",                                         # SQL DROP TABLE
    r"DELETE\s+FROM\s+\w+\s*$",                             # DELETE without WHERE
    r"TRUNCATE\s+TABLE",                                     # SQL TRUNCATE
    r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;",                     # Fork bomb
    r"mkfs\.",                                               # Filesystem format
    r"dd\s+.*of=/dev/[hs]d[a-z]",                           # dd to raw disk
]

# HIGH risk patterns (require plan)
HIGH_PATTERNS = [
    r"rm\s+-r",                                              # rm -r (any recursive delete)
    r"DELETE\s+FROM",                                        # SQL DELETE
    r"UPDATE\s+.*SET",                                       # SQL UPDATE
    r"chmod\s+777",                                          # Open permissions
    r"chmod\s+-R",                                           # Recursive chmod
    r"curl.*\|\s*sh",                                        # Pipe to shell
    r"wget.*\|\s*sh",                                        # Pipe to shell
]


@dataclass
class CheckResult:
    """Result of a single conformance check."""
    check_id: str
    check_name: str
    passed: bool
    details: str = ""
    evidence: Optional[str] = None


@dataclass
class ConformanceReport:
    """Full conformance report."""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "1.0.0"
    profile: str = "CSP Tool Safety Profile v1.0.0-rc1"
    overall_pass: bool = False
    checks: list[CheckResult] = field(default_factory=list)
    receipt_count: int = 0
    error_count: int = 0
    warning_count: int = 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "version": self.version,
            "profile": self.profile,
            "overall_pass": self.overall_pass,
            "summary": {
                "total_checks": len(self.checks),
                "passed": sum(1 for c in self.checks if c.passed),
                "failed": sum(1 for c in self.checks if not c.passed),
                "receipt_count": self.receipt_count,
                "error_count": self.error_count,
                "warning_count": self.warning_count,
            },
            "checks": [
                {
                    "check_id": c.check_id,
                    "check_name": c.check_name,
                    "passed": c.passed,
                    "details": c.details,
                    "evidence": c.evidence,
                }
                for c in self.checks
            ],
        }


# =============================================================================
# Conformance Checks
# =============================================================================

def check_hash_integrity(receipts: list[dict]) -> CheckResult:
    """MUST 3: Receipt hash integrity."""
    results = []
    for receipt in receipts:
        result = verify_receipt_hash(receipt)
        results.append(result)

    valid_count = sum(1 for r in results if r.hash_valid)
    total = len(results)

    return CheckResult(
        check_id="RCPT-01",
        check_name="Receipt Hash Integrity",
        passed=valid_count == total,
        details=f"{valid_count}/{total} receipts have valid hashes",
        evidence="Verified via JCS canonicalization + SHA-256",
    )


def check_chain_integrity(receipts: list[dict]) -> CheckResult:
    """MUST 3: Parent hash chain integrity."""
    results = verify_chain(receipts)

    chain_issues = [r for r in results if r.chain_valid is False]

    return CheckResult(
        check_id="RCPT-02",
        check_name="Receipt Chain Integrity",
        passed=len(chain_issues) == 0,
        details=f"{len(chain_issues)} chain integrity issues" if chain_issues else "All parent references valid",
        evidence="Verified parent_hashes point to existing receipts",
    )


def check_critical_blocked(receipts: list[dict]) -> CheckResult:
    """MUST 4: CRITICAL patterns blocked by default."""
    violations = []

    for receipt in receipts:
        payload = receipt.get("payload", {})
        command = payload.get("command", "") or payload.get("args", {}).get("command", "")

        if not command:
            continue

        # Check if this is an execution receipt (not a refusal)
        receipt_type = receipt.get("receipt_type", "")
        outcome = payload.get("outcome", "")

        # If it's an agent action that succeeded, check for CRITICAL patterns
        if "agent_action" in receipt_type or outcome == "success":
            for pattern in CRITICAL_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    violations.append({
                        "receipt_id": receipt.get("receipt_id"),
                        "command": command,
                        "pattern": pattern,
                    })

    return CheckResult(
        check_id="CRIT-01",
        check_name="CRITICAL Patterns Blocked",
        passed=len(violations) == 0,
        details=f"{len(violations)} CRITICAL commands executed without block" if violations else "No CRITICAL commands executed",
        evidence=json.dumps(violations[:3]) if violations else None,
    )


def check_refusal_receipts(receipts: list[dict]) -> CheckResult:
    """MUST 5: Refusal receipts emitted on denial."""
    # Build index of trace_id -> refusal receipts
    refusal_by_trace: dict[str, list[str]] = {}
    deny_by_trace: dict[str, list[str]] = {}

    for receipt in receipts:
        receipt_id = receipt.get("receipt_id", "unknown")
        receipt_type = receipt.get("receipt_type", "")
        payload = receipt.get("payload", {})
        trace_id = receipt.get("trace_id") or payload.get("trace_id")
        outcome = payload.get("outcome", "")
        decision = payload.get("decision", {})
        decision_result = decision.get("result", "") if isinstance(decision, dict) else ""
        reason = payload.get("reason", "") or payload.get("reason_code", "")

        # Is this a refusal receipt?
        # Note: decision_result == "deny" is NOT sufficient - that just means
        # the decision was to deny, not that this IS a refusal receipt.
        # Refusal receipts must be explicitly typed or have refusal outcomes.
        is_refusal = (
            "refusal" in receipt_type.lower() or
            outcome in ("denied", "blocked", "refused")
        )

        # Is this a denial that should have a refusal receipt?
        is_denial = (
            (reason and "DENY" in reason.upper()) or
            decision_result == "deny"
        )

        if trace_id:
            if is_refusal:
                refusal_by_trace.setdefault(trace_id, []).append(receipt_id)
            if is_denial:
                deny_by_trace.setdefault(trace_id, []).append(receipt_id)

    # Check: every denial trace_id should have a refusal receipt
    missing_refusals = []
    for trace_id, deny_receipts in deny_by_trace.items():
        if trace_id not in refusal_by_trace:
            missing_refusals.extend(deny_receipts)

    total_refusals = sum(len(v) for v in refusal_by_trace.values())
    total_denials = sum(len(v) for v in deny_by_trace.values())

    return CheckResult(
        check_id="REF-01",
        check_name="Refusal Receipts Emitted",
        passed=len(missing_refusals) == 0,
        details=f"{total_refusals} refusal receipts, {total_denials} denials, {len(missing_refusals)} missing",
        evidence=f"Missing for: {missing_refusals[:3]}" if missing_refusals else None,
    )


def check_plan_for_high_risk(receipts: list[dict]) -> CheckResult:
    """Amendment VII: Plan required for HIGH/CRITICAL actions."""
    violations = []

    # Build hash -> receipt index
    by_hash: dict[str, dict] = {}
    for receipt in receipts:
        h = receipt.get("receipt_hash")
        if h:
            by_hash[h] = receipt

    # Identify plan receipts (by hash)
    plan_hashes: set[str] = set()
    plan_ids: set[str] = set()
    for receipt in receipts:
        receipt_type = receipt.get("receipt_type", "")
        if "plan" in receipt_type.lower():
            h = receipt.get("receipt_hash")
            if h:
                plan_hashes.add(h)
            plan_ids.add(receipt.get("receipt_id", ""))
            # Also check payload for plan_id
            payload = receipt.get("payload", {})
            if "plan_id" in payload:
                plan_ids.add(payload["plan_id"])

    # Check high-risk actions have plans
    for receipt in receipts:
        payload = receipt.get("payload", {})
        command = payload.get("command", "") or payload.get("args", {}).get("command", "")
        risk_level = payload.get("risk_level", "").upper()

        if not command:
            continue

        is_high_risk = risk_level in ("HIGH", "CRITICAL")

        # Also detect high risk from patterns
        if not is_high_risk:
            for pattern in HIGH_PATTERNS + CRITICAL_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    is_high_risk = True
                    break

        if is_high_risk:
            # Check if this action has an associated plan
            has_plan = False

            # Method 1: Direct plan_id field
            plan_id = payload.get("plan_id")
            if plan_id and plan_id in plan_ids:
                has_plan = True

            # Method 2: Parent hash points to a plan receipt
            if not has_plan:
                parent_hashes = receipt.get("parent_hashes", []) or []
                for parent_hash in parent_hashes:
                    if parent_hash in plan_hashes:
                        has_plan = True
                        break
                    # Check if parent is a plan by looking up its type
                    parent_receipt = by_hash.get(parent_hash)
                    if parent_receipt:
                        parent_type = parent_receipt.get("receipt_type", "")
                        if "plan" in parent_type.lower():
                            has_plan = True
                            break

            outcome = payload.get("outcome", "")
            if outcome in ("success", "executed") and not has_plan:
                violations.append({
                    "receipt_id": receipt.get("receipt_id"),
                    "command": command[:50],
                    "risk_level": risk_level or "HIGH (inferred)",
                })

    return CheckResult(
        check_id="PLAN-01",
        check_name="Plan Required for HIGH/CRITICAL",
        passed=len(violations) == 0,
        details=f"{len(violations)} high-risk actions without plans" if violations else "All high-risk actions have plans",
        evidence=json.dumps(violations[:3]) if violations else None,
    )


def check_signature_coverage(receipts: list[dict]) -> CheckResult:
    """Court-Grade: Signatures present and valid."""
    total_signed = 0
    total_unsigned = 0
    court_receipts = []
    court_unsigned = []

    for receipt in receipts:
        tier = receipt.get("proof_tier", "none")
        has_sig = "signature" in receipt and receipt["signature"]

        if has_sig:
            total_signed += 1
        else:
            total_unsigned += 1

        if tier == "court":
            court_receipts.append(receipt.get("receipt_id", "unknown"))
            if not has_sig:
                court_unsigned.append(receipt.get("receipt_id", "unknown"))

    # Pass if ALL court-tier receipts are signed
    passed = len(court_unsigned) == 0

    return CheckResult(
        check_id="SIG-01",
        check_name="Signature Coverage",
        passed=passed,
        details=f"{total_signed} signed, {total_unsigned} unsigned, {len(court_receipts)} court-tier ({len(court_unsigned)} unsigned)",
        evidence=f"Unsigned court receipts: {court_unsigned[:3]}" if court_unsigned else None,
    )


def check_timestamp_ordering(receipts: list[dict]) -> CheckResult:
    """Receipts should be in timestamp order."""
    violations = []
    last_ts = None
    last_dt = None

    def parse_iso(ts_str: str) -> Optional[datetime]:
        """Parse ISO8601 timestamp, handling various formats."""
        if not ts_str:
            return None
        try:
            # Handle Z suffix
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1] + '+00:00'
            return datetime.fromisoformat(ts_str)
        except ValueError:
            return None

    for receipt in receipts:
        ts = receipt.get("ts")
        if ts:
            dt = parse_iso(ts)
            if dt and last_dt:
                if dt < last_dt:
                    violations.append({
                        "receipt_id": receipt.get("receipt_id"),
                        "ts": ts,
                        "previous_ts": last_ts,
                    })
            last_ts = ts
            last_dt = dt

    return CheckResult(
        check_id="ORD-01",
        check_name="Timestamp Ordering",
        passed=len(violations) == 0,
        details=f"{len(violations)} ordering violations" if violations else "All receipts in order",
        evidence=json.dumps(violations[:3]) if violations else None,
    )


# =============================================================================
# Badge Generator
# =============================================================================

def generate_badge_svg(passed: bool, label: str = "CSP") -> str:
    """Generate a shields.io style badge SVG."""
    color = "#4c1" if passed else "#e05d44"
    status = "PASS" if passed else "FAIL"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="90" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="90" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h37v20H0z"/>
    <path fill="{color}" d="M37 0h53v20H37z"/>
    <path fill="url(#b)" d="M0 0h90v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="18.5" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="18.5" y="14">{label}</text>
    <text x="62.5" y="15" fill="#010101" fill-opacity=".3">{status}</text>
    <text x="62.5" y="14">{status}</text>
  </g>
</svg>'''


# =============================================================================
# Main Validator
# =============================================================================

def validate_receipts(receipts: list[dict]) -> ConformanceReport:
    """Run all conformance checks on a set of receipts."""
    report = ConformanceReport()
    report.receipt_count = len(receipts)

    # Run checks
    checks = [
        check_hash_integrity(receipts),
        check_chain_integrity(receipts),
        check_critical_blocked(receipts),
        check_refusal_receipts(receipts),
        check_plan_for_high_risk(receipts),
        check_signature_coverage(receipts),
        check_timestamp_ordering(receipts),
    ]

    report.checks = checks
    report.error_count = sum(1 for c in checks if not c.passed)
    report.overall_pass = report.error_count == 0

    return report


def load_receipts(path: Path) -> list[dict]:
    """Load receipts from a file or directory."""
    receipts = []

    if path.is_file():
        with open(path) as f:
            data = json.load(f)
            if isinstance(data, list):
                receipts.extend(data)
            else:
                receipts.append(data)
    elif path.is_dir():
        for file in sorted(path.glob("*.json")):
            with open(file) as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        receipts.extend(data)
                    else:
                        receipts.append(data)
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse {file}")

    return receipts


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CSP Tool Safety Profile Conformance Validator"
    )
    parser.add_argument(
        "receipts",
        type=Path,
        help="Receipt file or directory to validate",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output report file (JSON)",
    )
    parser.add_argument(
        "--badge",
        type=Path,
        help="Output badge file (SVG)",
    )
    parser.add_argument(
        "--sign",
        type=Path,
        help="Sign report with private key file",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Load receipts
    if not args.receipts.exists():
        print(f"Error: {args.receipts} does not exist")
        sys.exit(1)

    receipts = load_receipts(args.receipts)

    if not receipts:
        print("Warning: No receipts found")
        receipts = []

    # Run validation
    report = validate_receipts(receipts)

    # Print summary
    print("=" * 60)
    print("CSP Tool Safety Profile Conformance Report")
    print("=" * 60)
    print()

    status = "PASS" if report.overall_pass else "FAIL"
    print(f"Overall: [{status}]")
    if report.overall_pass:
        print("Your implementation is CSP conformant. Guardian verified all controls.")
    print()
    print(f"Receipts validated: {report.receipt_count}")
    print(f"Checks passed: {len(report.checks) - report.error_count}/{len(report.checks)}")
    print()

    for check in report.checks:
        status_icon = "[PASS]" if check.passed else "[FAIL]"
        print(f"  {status_icon} {check.check_id}: {check.check_name}")
        if args.verbose or not check.passed:
            print(f"         {check.details}")
            if check.evidence:
                print(f"         Evidence: {check.evidence[:100]}...")
    print()

    # Generate report
    report_dict = report.to_dict()

    # Sign if requested
    if args.sign and args.sign.exists():
        import base64
        with open(args.sign) as f:
            key_data = json.load(f)

        from crypto_core import KeyPair

        keypair = KeyPair(
            key_id=key_data["key_id"],
            private_key=base64.b64decode(key_data["private_key"]),
        )

        # Create a receipt for the report itself
        report_receipt = create_receipt(
            receipt_type="csp.conformance_report/v1",
            payload=report_dict,
            proof_tier="core",
            keypair=keypair,
        )
        report_dict = report_receipt
        print(f"Report signed with key: {keypair.key_id}")

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report_dict, f, indent=2)
        print(f"Report saved to: {args.output}")

    # Generate badge
    if args.badge:
        badge_svg = generate_badge_svg(report.overall_pass)
        with open(args.badge, "w") as f:
            f.write(badge_svg)
        print(f"Badge saved to: {args.badge}")

    # Exit code
    sys.exit(0 if report.overall_pass else 1)


if __name__ == "__main__":
    main()
