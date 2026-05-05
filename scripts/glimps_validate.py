#!/usr/bin/env python3
"""Validate GLIMPS profile receipts.

This is a lightweight profile validator for:
- glimps.birth/v0
- glimps.emission_census/v0
- glimps.wound/v0

It intentionally validates profile shape and GLIMPS authority boundaries only.
It does not grant runtime authority, integrate Guardian, or mutate memory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SCHEMA_BY_RECEIPT_TYPE = {
    "glimps.birth/v0": "glimpse_birth_receipt.v0.json",
    "glimps.emission_census/v0": "glimpse_emission_census.v0.json",
    "glimps.wound/v0": "glimpse_wound_receipt.v0.json",
}

BEAUTY_TERMS = {
    "aesthetic",
    "beautiful",
    "beauty",
    "elegant",
    "elegance",
    "metaphor",
    "metaphorical",
    "analogy",
    "analogical",
}

CONCRETE_WOUND_TERMS = {
    "boundary",
    "case",
    "check",
    "compute",
    "counterexample",
    "fixture",
    "measure",
    "observe",
    "probe",
    "receipt",
    "replay",
    "test",
    "trace",
    "verify",
}


@dataclass
class GlimpsValidationResult:
    receipt_type: str
    passed: bool
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_type": self.receipt_type,
            "passed": self.passed,
            "errors": self.errors,
        }


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def schema_dir(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "profiles" / "glimps" / "schema"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_schema(receipt_type: str, root: Path | None = None) -> dict[str, Any]:
    schema_name = SCHEMA_BY_RECEIPT_TYPE.get(receipt_type)
    if schema_name is None:
        raise ValueError(f"unknown GLIMPS receipt_type: {receipt_type!r}")
    return load_json(schema_dir(root) / schema_name)


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def _validate_schema_fragment(
    value: Any,
    schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    expected_type = schema.get("type")
    if expected_type and not _type_matches(value, expected_type):
        errors.append(f"{path}: expected {expected_type}")
        return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum {schema['enum']!r}")

    if isinstance(value, int) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            errors.append(f"{path}: value {value!r} below minimum {minimum}")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(value) < min_length:
            errors.append(f"{path}: string shorter than minLength {min_length}")
        pattern = schema.get("pattern")
        if pattern and not re.match(pattern, value):
            errors.append(f"{path}: does not match pattern {pattern!r}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(value) < min_items:
            errors.append(f"{path}: array shorter than minItems {min_items}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema_fragment(item, item_schema, f"{path}[{index}]", errors)

    if isinstance(value, dict):
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        for key in required:
            if key not in value:
                errors.append(f"{path}.{key}: missing required field")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}.{key}: additional property not allowed")
        for key, child_schema in properties.items():
            if key in value:
                _validate_schema_fragment(value[key], child_schema, f"{path}.{key}", errors)


def validate_required_schema(receipt: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _validate_schema_fragment(receipt, schema, "$", errors)
    return errors


def _nested(receipt: dict[str, Any], path: str) -> Any:
    value: Any = receipt
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _is_non_empty(value: Any) -> bool:
    return value not in (None, "", [])


def _text_tokens(value: Any) -> set[str]:
    text = json.dumps(value).lower().replace("_", " ")
    return set(re.findall(r"[a-z_]+", text))


def _value_text_tokens(value: Any) -> set[str]:
    if isinstance(value, str):
        return set(re.findall(r"[a-z_]+", value.lower().replace("_", " ")))
    if isinstance(value, list):
        tokens: set[str] = set()
        for item in value:
            tokens |= _value_text_tokens(item)
        return tokens
    if isinstance(value, dict):
        tokens: set[str] = set()
        for item in value.values():
            tokens |= _value_text_tokens(item)
        return tokens
    return set()


def _semantic_birth_errors(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    required_non_empty = [
        "pressure_statement",
        "lens",
        "lens.makes_visible",
        "lens.hides",
        "lens_debt.counter_lens",
        "rivals",
        "first_wound",
    ]
    for path in required_non_empty:
        if not _is_non_empty(_nested(receipt, path)):
            errors.append(f"{path}: required and non-empty")

    if receipt.get("initial_authority") != "speculative":
        errors.append("initial_authority: must be speculative")

    permissions = receipt.get("permissions", {})
    required_permission_values = {
        "can_govern_execution": False,
        "can_modify_policy": False,
        "can_allocate_execution_budget": False,
        "can_change_default_route": False,
        "can_raise_confidence_without_receipts": False,
        "requires_receipts_for_promotion": True,
    }
    for key, expected in required_permission_values.items():
        if permissions.get(key) is not expected:
            errors.append(f"permissions.{key}: must be {expected}")

    if permissions.get("can_prioritize_search") is True and permissions.get(
        "can_allocate_execution_budget"
    ) is not False:
        errors.append("permissions: search priority must not imply budget allocation")

    negative_duties = receipt.get("negative_duties", {})
    for key in [
        "must_not_raise_confidence",
        "must_not_suppress_rivals",
        "must_not_mutate_memory",
        "must_not_modify_policy",
        "must_not_claim_exhaustive_search",
        "must_not_present_beauty_as_evidence",
    ]:
        if negative_duties.get(key) is not True:
            errors.append(f"negative_duties.{key}: must be true")

    if receipt.get("confidence") == "high" and receipt.get("fertility") == "high":
        errors.append("confidence/fertility: high fertility cannot raise confidence")

    tokens = _text_tokens(
        {
            "source_pressure": receipt.get("source_pressure"),
            "imagination_type": receipt.get("imagination_type"),
            "lens": receipt.get("lens"),
            "candidate": receipt.get("candidate_claim_or_frame"),
            "attention_request": receipt.get("attention_request"),
        }
    )
    if tokens & BEAUTY_TERMS and receipt.get("confidence") != "low":
        errors.append("beauty/analogy: may point, but may not raise confidence")

    imagination_type = set(receipt.get("imagination_type", []))
    if "analogical" in imagination_type:
        wound_tokens = _value_text_tokens(receipt.get("first_wound", {}))
        if not (wound_tokens & CONCRETE_WOUND_TERMS):
            errors.append("first_wound: analogical candidates require a concrete non-analogical probe")

    for ghost in receipt.get("related_ghosts", []):
        if not ghost.get("new_receipts"):
            errors.append("related_ghosts: ghost seeds require new receipts")
        if permissions.get("can_govern_execution") is not False:
            errors.append("related_ghosts: ghosts may seed, but never govern")

    if receipt.get("truth_track") not in {"truth", "usefulness", "representation", "obstruction", "taxonomy"}:
        errors.append("truth_track: unknown track")

    return errors


def _semantic_census_errors(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    candidates_generated = receipt.get("candidates_generated")
    candidates_with_rivals = receipt.get("candidates_with_rivals")
    candidates_with_first_wounds = receipt.get("candidates_with_first_wounds")

    if isinstance(candidates_generated, int):
        if isinstance(candidates_with_rivals, int) and candidates_with_rivals > candidates_generated:
            errors.append("candidates_with_rivals: cannot exceed candidates_generated")
        if (
            isinstance(candidates_with_first_wounds, int)
            and candidates_with_first_wounds > candidates_generated
        ):
            errors.append("candidates_with_first_wounds: cannot exceed candidates_generated")
        if (
            isinstance(candidates_with_first_wounds, int)
            and candidates_generated > candidates_with_first_wounds
            and receipt.get("unwounded_candidate_warning") is not True
        ):
            errors.append("unwounded_candidate_warning: must be true when candidates lack first wounds")
        if (
            isinstance(candidates_with_rivals, int)
            and candidates_generated > candidates_with_rivals
            and receipt.get("rival_suppression_warning") is not True
        ):
            errors.append("rival_suppression_warning: must be true when candidates lack rivals")

    for key in ["frame_monoculture_warning", "attention_capture_warning"]:
        if not isinstance(receipt.get(key), bool):
            errors.append(f"{key}: must be an explicit boolean")

    if receipt.get("pressures_detected", 0) > 0 and "pressures_without_candidates" not in receipt:
        errors.append("pressures_without_candidates: must not be silently omitted")

    return errors


def _semantic_wound_errors(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in ["glimpse_id", "candidate_id", "wound_id", "expected_result", "observed_result"]:
        if not _is_non_empty(receipt.get(key)):
            errors.append(f"{key}: required and non-empty")

    for forbidden in ["authority", "authority_granted", "guardian_decision"]:
        if forbidden in receipt:
            errors.append(f"{forbidden}: wound receipts record probes only and grant no authority")

    return errors


def validate_glimps_receipt(
    receipt: dict[str, Any],
    root: Path | None = None,
) -> GlimpsValidationResult:
    receipt_type = receipt.get("receipt_type", "<missing>")
    if receipt_type not in SCHEMA_BY_RECEIPT_TYPE:
        return GlimpsValidationResult(
            receipt_type=receipt_type,
            passed=False,
            errors=[f"unknown GLIMPS receipt_type: {receipt_type!r}"],
        )

    schema = load_schema(receipt_type, root)
    errors = validate_required_schema(receipt, schema)

    if receipt_type == "glimps.birth/v0":
        errors.extend(_semantic_birth_errors(receipt))
    elif receipt_type == "glimps.emission_census/v0":
        errors.extend(_semantic_census_errors(receipt))
    elif receipt_type == "glimps.wound/v0":
        errors.extend(_semantic_wound_errors(receipt))

    return GlimpsValidationResult(
        receipt_type=receipt_type,
        passed=not errors,
        errors=errors,
    )


def load_receipts(path: Path) -> list[dict[str, Any]]:
    if path.is_file():
        data = load_json(path)
        return data if isinstance(data, list) else [data]

    receipts = []
    for file in sorted(path.glob("*.json")):
        data = load_json(file)
        if isinstance(data, list):
            receipts.extend(data)
        else:
            receipts.append(data)
    return receipts


def validate_path(path: Path, root: Path | None = None) -> list[GlimpsValidationResult]:
    return [validate_glimps_receipt(receipt, root) for receipt in load_receipts(path)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate GLIMPS profile receipts")
    parser.add_argument("receipts", type=Path, help="GLIMPS receipt file or directory")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    if not args.receipts.exists():
        print(f"Error: {args.receipts} does not exist")
        return 1

    results = validate_path(args.receipts)
    overall_pass = all(result.passed for result in results)

    if args.json:
        print(json.dumps({"passed": overall_pass, "results": [r.to_dict() for r in results]}, indent=2))
    else:
        status = "PASS" if overall_pass else "FAIL"
        print(f"GLIMPS profile validation: [{status}]")
        for result in results:
            item_status = "PASS" if result.passed else "FAIL"
            print(f"  [{item_status}] {result.receipt_type}")
            for error in result.errors:
                print(f"         {error}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
