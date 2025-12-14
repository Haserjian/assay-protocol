#!/usr/bin/env python3
"""RitualLint: Prevent Cathedral failure modes in CSP.

The Three Laws as Lint Rules:
  L1 - PasswordLint: Every slogan must cash out into a test
  L2 - MythLint: Every narrative claim must have an implementation path
  L3 - ContradictionLint: If holding A and ~A, it must be documented

Usage:
  python scripts/ritual_lint.py

Exit codes:
  0 - All checks pass
  1 - Lint failures detected
"""

import re
import sys
from pathlib import Path

import yaml


def load_control_map(repo_root: Path) -> dict:
    """Load canonical control map."""
    control_map_path = repo_root / "control_map.yaml"
    if not control_map_path.exists():
        raise FileNotFoundError(f"control_map.yaml not found at {control_map_path}")

    with open(control_map_path) as f:
        return yaml.safe_load(f)


def extract_test_ids_from_yaml(control_map: dict) -> set[str]:
    """Extract all test IDs from control_map.yaml."""
    test_ids = set()
    for must in control_map.get("musts", []):
        for test in must.get("unit_tests", []):
            test_ids.add(test["id"])
        for test in must.get("integration_tests", []):
            test_ids.add(test["id"])
    return test_ids


def extract_test_ids_from_code(repo_root: Path) -> set[str]:
    """Extract test IDs from test_conformance.py docstrings."""
    test_file = repo_root / "reference/python_gateway/tests/test_conformance.py"
    if not test_file.exists():
        raise FileNotFoundError(f"Test file not found at {test_file}")

    content = test_file.read_text()

    # Match patterns like AUTH-01, DISC-02, VAL-03, etc.
    pattern = r'"""([A-Z]+-\d+):'
    matches = re.findall(pattern, content)
    return set(matches)


def extract_reason_codes_from_tests(repo_root: Path) -> set[str]:
    """Extract reason codes used in tests."""
    test_file = repo_root / "reference/python_gateway/tests/test_conformance.py"
    content = test_file.read_text()

    # Match ReasonCode.DENY_* or ReasonCode.ALLOW_*
    pattern = r'ReasonCode\.([A-Z_]+)'
    return set(re.findall(pattern, content))


def extract_reason_codes_from_docs(repo_root: Path) -> set[str]:
    """Extract reason codes from REASON_CODES.md."""
    reason_file = repo_root / "REASON_CODES.md"
    if not reason_file.exists():
        raise FileNotFoundError(f"REASON_CODES.md not found at {reason_file}")

    content = reason_file.read_text()

    # Match `CODE_NAME` pattern in table rows
    pattern = r'\| `([A-Z_]+)` \|'
    return set(re.findall(pattern, content))


def check_internal_links(repo_root: Path) -> list[str]:
    """Check that internal markdown links resolve."""
    errors = []

    # Files to check for internal links
    files_to_check = [
        "README.md",
        "SPEC.md",
        "FOR_HUMANS.md",
        "IMPLEMENTORS.md",
        "CONTROL_MAP.md",
    ]

    for filename in files_to_check:
        filepath = repo_root / filename
        if not filepath.exists():
            continue

        content = filepath.read_text()

        # Match relative links like [text](./path) or [text](path)
        pattern = r'\[([^\]]+)\]\((\./)?([^)#]+)(?:#[^)]*)?\)'
        matches = re.findall(pattern, content)

        for _, prefix, path in matches:
            # Skip external links
            if path.startswith("http://") or path.startswith("https://"):
                continue

            target = repo_root / path
            if not target.exists():
                errors.append(f"{filename}: broken link to '{path}'")

    return errors


def check_tensions_documented(repo_root: Path) -> list[str]:
    """Check that TENSIONS.md exists for documenting contradictions."""
    errors = []
    tensions_file = repo_root / "TENSIONS.md"

    if not tensions_file.exists():
        errors.append("TENSIONS.md not found - contradictions must be documented")

    return errors


def lint_password_rule(control_map: dict, test_ids_in_code: set[str]) -> list[str]:
    """L1: Every slogan must cash out into a test."""
    errors = []

    yaml_test_ids = extract_test_ids_from_yaml(control_map)
    expected_unit_count = control_map.get("meta", {}).get("unit_test_count", 0)

    # Check: every mapped test ID exists in code
    for test_id in yaml_test_ids:
        # Skip integration tests (marked with notes about environment)
        is_integration = any(
            any(t.get("id") == test_id for t in must.get("integration_tests", []))
            for must in control_map.get("musts", [])
        )
        if is_integration:
            continue

        if test_id not in test_ids_in_code:
            errors.append(f"L1-PASSWORD: Test ID '{test_id}' in control_map.yaml but not in test_conformance.py")

    # Check: every test ID in code is mapped
    for test_id in test_ids_in_code:
        if test_id not in yaml_test_ids:
            errors.append(f"L1-PASSWORD: Test ID '{test_id}' in test_conformance.py but not in control_map.yaml")

    # Check: unit test count matches documentation
    unit_test_ids = set()
    for must in control_map.get("musts", []):
        for test in must.get("unit_tests", []):
            unit_test_ids.add(test["id"])

    actual_count = len(test_ids_in_code)
    if actual_count != expected_unit_count:
        errors.append(
            f"L1-PASSWORD: Unit test count mismatch - "
            f"control_map.yaml says {expected_unit_count}, "
            f"test_conformance.py has {actual_count}"
        )

    return errors


def lint_myth_rule(repo_root: Path, control_map: dict) -> list[str]:
    """L2: Every narrative claim must have an implementation path."""
    errors = []

    # Check: module files exist
    for must in control_map.get("musts", []):
        module = must.get("module")
        if module is None:
            continue

        # Handle "module.py" and "module.py:function()" formats
        module_name = module.split(":")[0]
        if module_name == "N/A":
            continue

        # Check multiple possible locations
        if "," in module_name:
            # Handle "receipts.py, incident.py"
            module_names = [m.strip() for m in module_name.split(",")]
        else:
            module_names = [module_name]

        for mod in module_names:
            module_path = repo_root / "reference/python_gateway/src/csp_gateway" / mod
            if not module_path.exists():
                errors.append(f"L2-MYTH: Module '{mod}' declared for {must['id']} does not exist")

    # Check: test file exists
    test_file = control_map.get("meta", {}).get("test_file")
    if test_file:
        test_path = repo_root / test_file
        if not test_path.exists():
            errors.append(f"L2-MYTH: Test file '{test_file}' declared in control_map.yaml does not exist")

    return errors


def lint_contradiction_rule(repo_root: Path) -> list[str]:
    """L3: If holding A and ~A, label it."""
    errors = []

    # Check TENSIONS.md exists
    errors.extend(check_tensions_documented(repo_root))

    # Check for known footgun phrases that indicate undocumented contradictions
    footgun_phrases = [
        # These phrases suggest contradictions that should be documented
        (r"ALLOW or ESCALATE.*before execution", "ESCALATE as approval ambiguity"),
    ]

    spec_file = repo_root / "SPEC.md"
    if spec_file.exists():
        content = spec_file.read_text()
        for pattern, description in footgun_phrases:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(f"L3-CONTRADICTION: Potential undocumented tension: {description}")

    return errors


def lint_reason_codes(repo_root: Path) -> list[str]:
    """Check reason code consistency between tests and docs."""
    errors = []

    codes_in_tests = extract_reason_codes_from_tests(repo_root)
    codes_in_docs = extract_reason_codes_from_docs(repo_root)

    # Check: reason codes in tests should be documented
    for code in codes_in_tests:
        if code not in codes_in_docs:
            errors.append(f"REASON-CODE: '{code}' used in tests but not documented in REASON_CODES.md")

    return errors


def main():
    """Run all lint checks."""
    # Find repo root (look for control_map.yaml)
    repo_root = Path(__file__).parent.parent
    if not (repo_root / "control_map.yaml").exists():
        repo_root = Path.cwd()

    print("=" * 60)
    print("RitualLint: Preventing Cathedral Failure Modes")
    print("=" * 60)
    print()

    all_errors = []

    try:
        control_map = load_control_map(repo_root)
        print(f"Loaded control_map.yaml (version {control_map.get('meta', {}).get('version', 'unknown')})")
    except FileNotFoundError as e:
        print(f"FATAL: {e}")
        sys.exit(1)

    try:
        test_ids_in_code = extract_test_ids_from_code(repo_root)
        print(f"Found {len(test_ids_in_code)} test IDs in test_conformance.py")
    except FileNotFoundError as e:
        print(f"FATAL: {e}")
        sys.exit(1)

    print()

    # L1: Password Lint
    print("[L1] PasswordLint: Every slogan must cash out into a test")
    password_errors = lint_password_rule(control_map, test_ids_in_code)
    if password_errors:
        for err in password_errors:
            print(f"  FAIL: {err}")
        all_errors.extend(password_errors)
    else:
        print("  PASS: All test IDs mapped and counts match")
    print()

    # L2: Myth Lint
    print("[L2] MythLint: Every narrative claim must have an implementation path")
    myth_errors = lint_myth_rule(repo_root, control_map)
    if myth_errors:
        for err in myth_errors:
            print(f"  FAIL: {err}")
        all_errors.extend(myth_errors)
    else:
        print("  PASS: All modules and paths exist")
    print()

    # L3: Contradiction Lint
    print("[L3] ContradictionLint: If holding A and ~A, label it")
    contradiction_errors = lint_contradiction_rule(repo_root)
    if contradiction_errors:
        for err in contradiction_errors:
            print(f"  FAIL: {err}")
        all_errors.extend(contradiction_errors)
    else:
        print("  PASS: TENSIONS.md exists, no undocumented footguns")
    print()

    # Bonus: Reason code consistency
    print("[BONUS] Reason code consistency")
    reason_errors = lint_reason_codes(repo_root)
    if reason_errors:
        for err in reason_errors:
            print(f"  FAIL: {err}")
        all_errors.extend(reason_errors)
    else:
        print("  PASS: All reason codes documented")
    print()

    # Bonus: Internal links
    print("[BONUS] Internal link validation")
    link_errors = check_internal_links(repo_root)
    if link_errors:
        for err in link_errors:
            print(f"  FAIL: {err}")
        all_errors.extend(link_errors)
    else:
        print("  PASS: All internal links resolve")
    print()

    # Summary
    print("=" * 60)
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s) found")
        sys.exit(1)
    else:
        print("PASSED: All ritual lint checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
