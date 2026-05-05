import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from glimps_validate import validate_glimps_receipt  # noqa: E402


EXAMPLES = ROOT / "profiles" / "glimps" / "examples"


def load_json(path):
    return json.loads(path.read_text())


def birth_example(name="agent_failure_birth_receipt.json"):
    return load_json(EXAMPLES / name)


def census_example():
    return load_json(EXAMPLES / "emission_census.json")


def wound_example():
    return load_json(EXAMPLES / "wound_receipt.json")


def assert_invalid(receipt, expected_fragment):
    result = validate_glimps_receipt(receipt, ROOT)
    assert result.passed is False
    assert any(expected_fragment in error for error in result.errors), result.errors


def test_valid_birth_example_passes_validator():
    result = validate_glimps_receipt(birth_example(), ROOT)
    assert result.passed is True
    assert result.errors == []


def test_valid_emission_census_example_passes_validator():
    result = validate_glimps_receipt(census_example(), ROOT)
    assert result.passed is True
    assert result.errors == []


def test_valid_wound_example_passes_validator():
    result = validate_glimps_receipt(wound_example(), ROOT)
    assert result.passed is True
    assert result.errors == []


def test_invalid_receipt_type_fails():
    receipt = copy.deepcopy(birth_example())
    receipt["receipt_type"] = "glimps.claim/v0"
    assert_invalid(receipt, "unknown GLIMPS receipt_type")


def test_authority_leakage_fails():
    receipt = copy.deepcopy(birth_example())
    receipt["permissions"]["can_govern_execution"] = True
    assert_invalid(receipt, "permissions.can_govern_execution")


def test_missing_pressure_statement_fails():
    receipt = copy.deepcopy(birth_example())
    del receipt["pressure_statement"]
    assert_invalid(receipt, "pressure_statement")


def test_missing_rival_fails():
    receipt = copy.deepcopy(birth_example())
    receipt["rivals"] = []
    assert_invalid(receipt, "rivals")


def test_missing_first_wound_fails():
    receipt = copy.deepcopy(birth_example())
    del receipt["first_wound"]
    assert_invalid(receipt, "first_wound")


def test_confidence_raised_without_receipts_fails():
    receipt = copy.deepcopy(birth_example())
    receipt["confidence"] = "high"
    receipt["fertility"] = "high"
    assert_invalid(receipt, "high fertility cannot raise confidence")


def test_beauty_may_point_but_not_testify():
    receipt = copy.deepcopy(birth_example("math_birth_receipt.json"))
    receipt["confidence"] = "medium"
    assert_invalid(receipt, "beauty/analogy")


def test_analogical_candidate_requires_non_analogical_wound():
    receipt = copy.deepcopy(birth_example("math_birth_receipt.json"))
    receipt["imagination_type"] = ["analogical"]
    receipt["first_wound"] = {
        "smallest_test": "Compare the analogy to another analogy.",
        "what_would_hurt": "The metaphor feels weaker.",
        "what_it_forbids": "A less elegant metaphor."
    }
    assert_invalid(receipt, "analogical candidates require")


def test_wound_receipt_without_glimpse_id_fails():
    receipt = copy.deepcopy(wound_example())
    del receipt["glimpse_id"]
    assert_invalid(receipt, "glimpse_id")


def test_emission_census_inconsistent_counts_fail():
    receipt = copy.deepcopy(census_example())
    receipt["candidates_with_rivals"] = receipt["candidates_generated"] + 1
    assert_invalid(receipt, "candidates_with_rivals")


def test_emission_census_missing_first_wounds_warning_is_enforced():
    receipt = copy.deepcopy(census_example())
    receipt["candidates_with_first_wounds"] = receipt["candidates_generated"] - 1
    receipt["unwounded_candidate_warning"] = False
    assert_invalid(receipt, "unwounded_candidate_warning")


def test_rival_suppression_warning_is_enforced():
    receipt = copy.deepcopy(census_example())
    receipt["candidates_with_rivals"] = receipt["candidates_generated"] - 1
    receipt["rival_suppression_warning"] = False
    assert_invalid(receipt, "rival_suppression_warning")


def test_wound_receipt_grants_no_authority():
    receipt = copy.deepcopy(wound_example())
    receipt["authority_granted"] = True
    assert_invalid(receipt, "authority_granted")
