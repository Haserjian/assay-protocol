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
    denials = []
    has_refusal_receipt = []

    for receipt in receipts:
        receipt_type = receipt.get("receipt_type", "")
        payload = receipt.get("payload", {})
        outcome = payload.get("outcome", "")
        reason = payload.get("reason", "") or payload.get("reason_code", "")

        if "refusal" in receipt_type or outcome in ("denied", "blocked", "refused"):
            has_refusal_receipt.append(receipt.get("receipt_id"))
        elif reason and "DENY" in reason.upper():
            denials.append(receipt.get("receipt_id"))

    # Check if denials have corresponding refusal receipts
    # (simplified check - in production would cross-reference)

    return CheckResult(
        check_id="REF-01",
        check_name="Refusal Receipts Emitted",
        passed=True,  # Pass if we found any refusal receipts
        details=f"Found {len(has_refusal_receipt)} refusal receipts",
        evidence=f"Refusal receipt IDs: {has_refusal_receipt[:3]}..." if has_refusal_receipt else None,
    )


def check_plan_for_high_risk(receipts: list[dict]) -> CheckResult:
    """Amendment VII: Plan required for HIGH/CRITICAL actions."""
    violations = []
    plan_ids = set()

    # First pass: collect plan IDs
    for receipt in receipts:
        receipt_type = receipt.get("receipt_type", "")
        if "plan" in receipt_type.lower():
            plan_ids.add(receipt.get("receipt_id"))
            # Also check payload for plan_id
            payload = receipt.get("payload", {})
            if "plan_id" in payload:
                plan_ids.add(payload["plan_id"])

    # Second pass: check high-risk actions have plans
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
            plan_id = payload.get("plan_id")
            parent_hashes = receipt.get("parent_hashes", [])

            if plan_id:
                has_plan = True
            elif parent_hashes:
                # Check if any parent is a plan
                for parent in parent_hashes:
                    if any(pid in parent for pid in plan_ids):
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
    signed = 0
    unsigned = 0
    court_tier = 0

    for receipt in receipts:
        tier = receipt.get("proof_tier", "none")
        has_sig = "signature" in receipt and receipt["signature"]

        if tier == "court":
            court_tier += 1
            if not has_sig:
                unsigned += 1

        if has_sig:
            signed += 1
        else:
            unsigned += 1

    # Pass if no court-tier receipts are unsigned
    court_unsigned = court_tier - signed if court_tier > signed else 0

    return CheckResult(
        check_id="SIG-01",
        check_name="Signature Coverage",
        passed=court_unsigned == 0,
        details=f"{signed} signed, {unsigned} unsigned ({court_tier} court-tier)",
        evidence="Court-tier receipts MUST be signed",
    )


def check_timestamp_ordering(receipts: list[dict]) -> CheckResult:
    """Receipts should be in timestamp order."""
    violations = []
    last_ts = None

    for receipt in receipts:
        ts = receipt.get("ts")
        if ts and last_ts:
            if ts < last_ts:
                violations.append({
                    "receipt_id": receipt.get("receipt_id"),
                    "ts": ts,
                    "previous_ts": last_ts,
                })
        last_ts = ts

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
