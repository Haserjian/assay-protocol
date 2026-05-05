import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GLIMPS = ROOT / "profiles" / "glimps"
EXAMPLES = GLIMPS / "examples"
SCHEMAS = GLIMPS / "schema"


def load_json(path):
    return json.loads(path.read_text())


def birth_example(name="agent_failure_birth_receipt.json"):
    return load_json(EXAMPLES / name)


def birth_schema():
    return load_json(SCHEMAS / "glimpse_birth_receipt.v0.json")


def assert_required_path(document, path):
    value = document
    for part in path.split("."):
        assert part in value, f"missing {path}"
        value = value[part]
    assert value not in ("", [], None), f"empty {path}"


def test_birth_receipt_requires_pressure_statement():
    schema = birth_schema()
    example = birth_example()
    assert "pressure_statement" in schema["required"]
    assert_required_path(example, "pressure_statement")


def test_birth_receipt_requires_lens():
    schema = birth_schema()
    example = birth_example()
    assert "lens" in schema["required"]
    assert_required_path(example, "lens.name")


def test_lens_records_makes_visible_and_hides():
    example = birth_example()
    assert_required_path(example, "lens.makes_visible")
    assert_required_path(example, "lens.hides")


def test_lens_debt_requires_counter_lens():
    schema = birth_schema()
    example = birth_example()
    assert "counter_lens" in schema["properties"]["lens_debt"]["required"]
    assert_required_path(example, "lens_debt.counter_lens")


def test_birth_receipt_requires_at_least_one_rival():
    schema = birth_schema()
    example = birth_example()
    assert "rivals" in schema["required"]
    assert len(example["rivals"]) >= 1


def test_birth_receipt_requires_first_wound():
    schema = birth_schema()
    example = birth_example()
    assert "first_wound" in schema["required"]
    assert_required_path(example, "first_wound.smallest_test")
    assert_required_path(example, "first_wound.what_would_hurt")
    assert_required_path(example, "first_wound.what_it_forbids")


def test_initial_authority_must_be_speculative():
    schema = birth_schema()
    example = birth_example()
    assert schema["properties"]["initial_authority"]["enum"] == ["speculative"]
    assert example["initial_authority"] == "speculative"


def test_truth_track_and_usefulness_track_are_distinct():
    schema = birth_schema()
    tracks = schema["properties"]["truth_track"]["enum"]
    assert "truth" in tracks
    assert "usefulness" in tracks
    assert birth_example("math_birth_receipt.json")["truth_track"] != birth_example(
        "ghost_reactivation_birth_receipt.json"
    )["truth_track"]


def test_glimpse_packet_can_promote_to_claim_packet_only_if_woundable():
    example = birth_example()
    woundable_fields = [
        "pressure_statement",
        "lens.hides",
        "rivals",
        "first_wound.smallest_test",
        "permissions",
        "promotion_requirements",
    ]
    for path in woundable_fields:
        assert_required_path(example, path)
    assert example["initial_authority"] == "speculative"


def test_analogy_candidate_requires_non_analogical_wound():
    candidate = copy.deepcopy(birth_example("math_birth_receipt.json"))
    candidate["imagination_type"].append("analogical")
    wound_text = " ".join(candidate["first_wound"].values()).lower()
    assert "analogy" not in wound_text
    assert "compute" in wound_text or "boundary" in wound_text
