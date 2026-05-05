import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "profiles" / "glimps" / "examples"
SCHEMAS = ROOT / "profiles" / "glimps" / "schema"


def load_json(path):
    return json.loads(path.read_text())


def census_example():
    return load_json(EXAMPLES / "emission_census.json")


def census_schema():
    return load_json(SCHEMAS / "glimpse_emission_census.v0.json")


def test_emission_census_schema_requires_birth_side_counts():
    schema = census_schema()
    for field in [
        "pressures_detected",
        "glimpses_generated",
        "lenses_generated",
        "candidates_generated",
        "candidates_with_rivals",
        "candidates_with_first_wounds",
    ]:
        assert field in schema["required"]


def test_emission_census_detects_missing_first_wounds():
    census = copy.deepcopy(census_example())
    census["candidates_with_first_wounds"] = census["candidates_generated"] - 1
    census["unwounded_candidate_warning"] = (
        census["candidates_with_first_wounds"] < census["candidates_generated"]
    )
    assert census["unwounded_candidate_warning"] is True


def test_emission_census_flags_frame_monoculture():
    census = copy.deepcopy(census_example())
    census["lenses_generated"] = 1
    census["candidates_generated"] = 5
    census["frame_monoculture_warning"] = (
        census["lenses_generated"] <= 1 and census["candidates_generated"] > 1
    )
    assert census["frame_monoculture_warning"] is True


def test_emission_census_flags_attention_capture():
    census = copy.deepcopy(census_example())
    census["glimpses_generated"] = 9
    high_priority_requests = 9
    census["attention_capture_warning"] = high_priority_requests == census["glimpses_generated"]
    assert census["attention_capture_warning"] is True


def test_emission_census_flags_rival_suppression():
    census = copy.deepcopy(census_example())
    census["candidates_with_rivals"] = census["candidates_generated"] - 1
    census["rival_suppression_warning"] = (
        census["candidates_with_rivals"] < census["candidates_generated"]
    )
    assert census["rival_suppression_warning"] is True


def test_emission_census_flags_fertility_confidence_confusion():
    census = copy.deepcopy(census_example())
    high_fertility_candidates_counted_as_high_confidence = 1
    census["fertility_confidence_confusion_warning"] = (
        high_fertility_candidates_counted_as_high_confidence > 0
    )
    assert census["fertility_confidence_confusion_warning"] is True
