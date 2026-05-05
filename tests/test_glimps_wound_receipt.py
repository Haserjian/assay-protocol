import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "profiles" / "glimps" / "examples"
SCHEMAS = ROOT / "profiles" / "glimps" / "schema"


def load_json(path):
    return json.loads(path.read_text())


def birth_example():
    return load_json(EXAMPLES / "agent_failure_birth_receipt.json")


def wound_example():
    return load_json(EXAMPLES / "wound_receipt.json")


def wound_schema():
    return load_json(SCHEMAS / "glimpse_wound_receipt.v0.json")


def test_wound_receipt_schema_has_expected_routes():
    routes = wound_schema()["properties"]["next_route"]["enum"]
    assert routes == [
        "promote_to_claim_packet",
        "revise",
        "archive_as_ghost",
        "run_more_wounds",
    ]


def test_wound_receipt_links_to_birth_receipt():
    birth = birth_example()
    wound = wound_example()
    assert wound["glimpse_id"] == birth["glimpse_id"]


def test_wound_receipt_records_probe_and_result():
    wound = wound_example()
    assert wound["receipt_type"] == "glimps.wound/v0"
    assert wound["probe_type"] in wound_schema()["properties"]["probe_type"]["enum"]
    assert wound["expected_result"]
    assert wound["observed_result"]
    assert wound["wound_result"] in ["survived", "weakened", "killed", "inconclusive"]


def test_wound_receipt_keeps_promotion_explicit():
    wound = wound_example()
    assert wound["next_route"] != "promote_to_claim_packet"
    assert wound["next_route"] in wound_schema()["properties"]["next_route"]["enum"]
