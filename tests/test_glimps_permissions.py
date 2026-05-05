import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "profiles" / "glimps" / "examples"
SCHEMAS = ROOT / "profiles" / "glimps" / "schema"


def load_json(path):
    return json.loads(path.read_text())


def birth_example(name="agent_failure_birth_receipt.json"):
    return load_json(EXAMPLES / name)


def birth_schema():
    return load_json(SCHEMAS / "glimpse_birth_receipt.v0.json")


def test_glimps_candidate_cannot_govern_execution():
    example = birth_example()
    assert example["permissions"]["can_govern_execution"] is False


def test_glimps_candidate_cannot_modify_policy():
    example = birth_example()
    assert example["permissions"]["can_modify_policy"] is False
    assert example["negative_duties"]["must_not_modify_policy"] is True


def test_glimps_can_prioritize_search_but_not_allocate_budget():
    example = birth_example()
    assert example["permissions"]["can_prioritize_search"] is True
    assert example["permissions"]["can_allocate_execution_budget"] is False
    assert example["attention_request"]["requires_gate"] is True


def test_glimps_cannot_change_default_route():
    example = birth_example()
    assert example["permissions"]["can_change_default_route"] is False


def test_fertility_cannot_raise_confidence():
    example = birth_example()
    assert example["fertility"] == "high"
    assert example["confidence"] == "low"
    assert example["permissions"]["can_raise_confidence_without_receipts"] is False
    assert example["negative_duties"]["must_not_raise_confidence"] is True


def test_ai_intuition_cannot_raise_confidence_without_receipts():
    schema = birth_schema()
    proposer_kind = schema["properties"]["proposer"]["properties"]["kind"]["enum"]
    assert "ai" in proposer_kind
    permission = schema["properties"]["permissions"]["properties"][
        "can_raise_confidence_without_receipts"
    ]
    assert permission["enum"] == [False]


def test_beauty_may_point_but_not_testify():
    example = birth_example("math_birth_receipt.json")
    assert "beautiful_near_miss" in example["source_pressure"]
    assert example["attention_request"]["requested"] is True
    assert example["permissions"]["can_raise_confidence_without_receipts"] is False
    assert example["negative_duties"]["must_not_present_beauty_as_evidence"] is True


def test_glimpse_negative_duties_present():
    schema = birth_schema()
    example = birth_example()
    required = set(schema["properties"]["negative_duties"]["required"])
    assert required == set(example["negative_duties"])
    assert all(example["negative_duties"].values())


def test_ghost_seed_cannot_reactivate_without_new_receipts():
    example = birth_example("ghost_reactivation_birth_receipt.json")
    assert example["permissions"]["can_govern_execution"] is False
    assert example["related_ghosts"]
    for ghost in example["related_ghosts"]:
        assert ghost["new_receipts"], "ghost reactivation requires new receipts"
