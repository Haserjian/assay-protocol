import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from assay_validate import dispatch_profile_validation, registered_glimps_receipt_types  # noqa: E402


REGISTRY_PATH = ROOT / "profiles" / "registry.json"
EXPECTED_GLIMPS_RECEIPT_TYPES = {
    "glimps.birth/v0",
    "glimps.emission_census/v0",
    "glimps.wound/v0",
}


def load_json(path):
    return json.loads(path.read_text())


def registry():
    return load_json(REGISTRY_PATH)


def glimps_profile():
    return registry()["profiles"]["glimps"]


def run_json_command(*args):
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result, json.loads(result.stdout)


def test_registry_file_parses_as_json():
    data = registry()
    assert "profiles" in data
    assert "glimps" in data["profiles"]


def test_every_registered_schema_path_exists():
    for entry in glimps_profile()["receipt_types"].values():
        assert (ROOT / entry["schema_path"]).exists()


def test_every_registered_example_path_exists():
    for entry in glimps_profile()["receipt_types"].values():
        assert (ROOT / entry["example_path"]).exists()


def test_every_registered_validator_path_exists():
    for entry in glimps_profile()["receipt_types"].values():
        assert (ROOT / entry["validator"]).exists()


def test_glimps_has_exact_registered_receipt_types():
    assert set(glimps_profile()["receipt_types"]) == EXPECTED_GLIMPS_RECEIPT_TYPES
    assert registered_glimps_receipt_types(ROOT) == EXPECTED_GLIMPS_RECEIPT_TYPES


def test_every_registered_glimps_example_validates_through_assay_dispatcher():
    for receipt_type, entry in glimps_profile()["receipt_types"].items():
        result, report = run_json_command("scripts/assay_validate.py", entry["example_path"], "--json")
        assert result.returncode == 0
        assert report["ok"] is True
        assert report["receipt_type"] == receipt_type
        assert report["profile"] == "glimps"
        assert report["errors"] == []


def test_every_registered_glimps_example_validates_through_profile_validator():
    for receipt_type, entry in glimps_profile()["receipt_types"].items():
        result, report = run_json_command("scripts/glimps_validate.py", entry["example_path"], "--json")
        assert result.returncode == 0
        assert report["passed"] is True
        assert report["results"][0]["receipt_type"] == receipt_type
        assert report["results"][0]["errors"] == []


def test_no_glimps_entry_is_normative_crs_profile():
    profile = glimps_profile()
    assert profile["normative_crs_profile"] is False
    for entry in profile["receipt_types"].values():
        assert entry["normative_crs_profile"] is False


def test_normative_profiles_require_promotion_artifact():
    for profile_name, profile in registry()["profiles"].items():
        if profile.get("normative_crs_profile") is True:
            promotion_document = profile.get("promotion_document")
            assert promotion_document, f"{profile_name} lacks promotion_document"
            assert (ROOT / promotion_document).exists()


def test_no_incubating_profile_can_claim_runtime_authority():
    for profile_name, profile in registry()["profiles"].items():
        if profile.get("status") != "incubating":
            continue
        for receipt_type, entry in profile["receipt_types"].items():
            boundary = entry["authority_boundary"]
            assert boundary["can_govern_execution"] is False, (profile_name, receipt_type)
            assert boundary["can_modify_policy"] is False, (profile_name, receipt_type)
            assert boundary["can_allocate_execution_budget"] is False, (profile_name, receipt_type)
            assert boundary["can_raise_confidence_without_receipts"] is False, (
                profile_name,
                receipt_type,
            )


def test_assay_validate_still_rejects_unknown_glimps_receipt_type():
    report = dispatch_profile_validation([{"receipt_type": "glimps.unknown/v0"}])
    assert report["ok"] is False
    assert report["receipt_type"] == "glimps.unknown/v0"
    assert report["profile"] == "glimps"
    assert report["errors"] == ["unregistered GLIMPS receipt_type: 'glimps.unknown/v0'"]


def test_assay_validate_output_shape_for_registered_glimps_receipts():
    for entry in glimps_profile()["receipt_types"].values():
        _, report = run_json_command("scripts/assay_validate.py", entry["example_path"], "--json")
        assert set(report) == {"ok", "receipt_type", "profile", "errors"}
