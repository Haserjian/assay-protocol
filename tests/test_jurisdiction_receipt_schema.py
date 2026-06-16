from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, ValidationError


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "jurisdiction_receipt.schema.json"
EXAMPLES_DIR = REPO_ROOT / "schemas" / "examples"


@pytest.fixture(scope="module")
def validator() -> Draft7Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def _load_example(name: str) -> dict:
    path = EXAMPLES_DIR / f"jurisdiction_receipt.{name}.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(validator: Draft7Validator, receipt: dict) -> None:
    validator.validate(receipt)


def test_valid_factorize_receipt_passes(validator: Draft7Validator) -> None:
    _validate(validator, _load_example("factorize"))


def test_valid_archive_hard_receipt_passes(validator: Draft7Validator) -> None:
    _validate(validator, _load_example("archive_hard"))


def test_valid_quarantine_receipt_passes(validator: Draft7Validator) -> None:
    _validate(validator, _load_example("quarantine"))


def test_invalid_routing_decision_fails(validator: Draft7Validator) -> None:
    receipt = _load_example("factorize")
    receipt["routing_decision"] = "explain_away"

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_missing_candidate_elasticities_fails(validator: Draft7Validator) -> None:
    receipt = _load_example("factorize")
    del receipt["candidate_elasticities"]

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_extra_top_level_property_fails(validator: Draft7Validator) -> None:
    receipt = _load_example("factorize")
    receipt["decorative_confidence"] = "high"

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_selected_intervention_must_match_refine_decision(validator: Draft7Validator) -> None:
    receipt = _load_example("factorize")
    receipt.update(
        {
            "routing_decision": "refine",
            "selected_intervention": "factorize",
            "selected_elasticity": 0.22,
        }
    )

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_selected_intervention_must_match_factorize_decision(validator: Draft7Validator) -> None:
    receipt = _load_example("factorize")
    receipt["selected_intervention"] = "refine"

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_factorize_permissions_disallow_parent_governance(
    validator: Draft7Validator,
) -> None:
    receipt = _load_example("factorize")
    receipt["new_permissions"]["can_govern"] = True

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_factorize_permissions_require_child_receipts(
    validator: Draft7Validator,
) -> None:
    receipt = _load_example("factorize")
    receipt["new_permissions"]["requires_child_receipts"] = False

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_archive_hard_selected_elasticity_may_be_null(validator: Draft7Validator) -> None:
    receipt = _load_example("archive_hard")
    receipt["selected_elasticity"] = None

    _validate(validator, receipt)


def test_quarantine_selected_elasticity_may_be_null(validator: Draft7Validator) -> None:
    receipt = _load_example("quarantine")
    receipt["selected_elasticity"] = None

    _validate(validator, receipt)


def test_archive_hard_selected_intervention_must_match(validator: Draft7Validator) -> None:
    receipt = _load_example("archive_hard")
    receipt["selected_intervention"] = "replace_frame"

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_quarantine_selected_intervention_must_match(validator: Draft7Validator) -> None:
    receipt = _load_example("quarantine")
    receipt["selected_intervention"] = "factorize"

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_archive_hard_permissions_disallow_governance(
    validator: Draft7Validator,
) -> None:
    receipt = _load_example("archive_hard")
    receipt["new_permissions"]["can_govern"] = True

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_archive_hard_permissions_require_ghost_signal(
    validator: Draft7Validator,
) -> None:
    receipt = _load_example("archive_hard")
    receipt["new_permissions"]["can_suggest"] = False

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_quarantine_permissions_disallow_governance(
    validator: Draft7Validator,
) -> None:
    receipt = _load_example("quarantine")
    receipt["new_permissions"]["can_govern"] = True

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_quarantine_permissions_require_evidence_gathering(
    validator: Draft7Validator,
) -> None:
    receipt = _load_example("quarantine")
    receipt["new_permissions"]["can_gather_evidence"] = False

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_restorative_decision_selected_elasticity_cannot_be_null(
    validator: Draft7Validator,
) -> None:
    receipt = _load_example("factorize")
    receipt["selected_elasticity"] = None

    with pytest.raises(ValidationError):
        _validate(validator, receipt)


def test_examples_are_independent_test_fixtures() -> None:
    factorize = _load_example("factorize")
    archive = _load_example("archive_hard")
    quarantine = _load_example("quarantine")

    assert copy.deepcopy(factorize) != archive
    assert copy.deepcopy(factorize) != quarantine
