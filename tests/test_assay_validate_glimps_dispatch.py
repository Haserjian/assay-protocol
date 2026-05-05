import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from assay_validate import dispatch_profile_validation  # noqa: E402


EXAMPLES = ROOT / "profiles" / "glimps" / "examples"


def load_json(path):
    return json.loads(path.read_text())


def birth_example():
    return load_json(EXAMPLES / "agent_failure_birth_receipt.json")


def census_example():
    return load_json(EXAMPLES / "emission_census.json")


def wound_example():
    return load_json(EXAMPLES / "wound_receipt.json")


def run_json_command(*args):
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result, json.loads(result.stdout)


def write_json(path, value):
    path.write_text(json.dumps(value))


def test_general_dispatcher_validates_valid_glimps_birth_receipt():
    report = dispatch_profile_validation([birth_example()])
    assert report == {
        "ok": True,
        "receipt_type": "glimps.birth/v0",
        "profile": "glimps",
        "errors": [],
    }


def test_general_dispatcher_validates_valid_glimps_emission_census():
    report = dispatch_profile_validation([census_example()])
    assert report["ok"] is True
    assert report["receipt_type"] == "glimps.emission_census/v0"
    assert report["profile"] == "glimps"
    assert report["errors"] == []


def test_general_dispatcher_validates_valid_glimps_wound_receipt():
    report = dispatch_profile_validation([wound_example()])
    assert report["ok"] is True
    assert report["receipt_type"] == "glimps.wound/v0"
    assert report["profile"] == "glimps"
    assert report["errors"] == []


def test_general_dispatcher_rejects_unknown_glimps_receipt_type():
    receipt = copy.deepcopy(birth_example())
    receipt["receipt_type"] = "glimps.unknown/v0"
    report = dispatch_profile_validation([receipt])
    assert report["ok"] is False
    assert report["receipt_type"] == "glimps.unknown/v0"
    assert any("unregistered GLIMPS receipt_type" in error for error in report["errors"])


def test_general_dispatcher_rejects_non_string_receipt_type():
    report = dispatch_profile_validation([{"receipt_type": None}])
    assert report["ok"] is False
    assert report["receipt_type"] is None
    assert report["profile"] == "unknown"
    assert report["errors"] == ["receipt_type: must be a string"]


def test_general_dispatcher_preserves_glimps_semantic_errors():
    receipt = copy.deepcopy(birth_example())
    receipt["permissions"]["can_govern_execution"] = True
    report = dispatch_profile_validation([receipt])
    assert report["ok"] is False
    assert any("permissions.can_govern_execution" in error for error in report["errors"])


def test_general_dispatcher_enforces_glimps_schema_minimums():
    receipt = copy.deepcopy(census_example())
    for key in [
        "pressures_detected",
        "glimpses_generated",
        "lenses_generated",
        "candidates_generated",
        "candidates_with_rivals",
        "candidates_with_first_wounds",
    ]:
        receipt[key] = -1
    report = dispatch_profile_validation([receipt])
    assert report["ok"] is False
    assert any("below minimum 0" in error for error in report["errors"])


def test_assay_validate_cli_dispatches_glimps_birth_json():
    result, report = run_json_command(
        "scripts/assay_validate.py",
        "profiles/glimps/examples/agent_failure_birth_receipt.json",
        "--json",
    )
    assert result.returncode == 0
    assert report == {
        "ok": True,
        "receipt_type": "glimps.birth/v0",
        "profile": "glimps",
        "errors": [],
    }


def test_assay_validate_cli_dispatches_glimps_directory_json():
    result, report = run_json_command(
        "scripts/assay_validate.py",
        "profiles/glimps/examples",
        "--json",
    )
    assert result.returncode == 0
    assert report["ok"] is True
    assert report["profile"] == "glimps"
    assert report["receipt_count"] == 5
    assert {item["receipt_type"] for item in report["results"]} == {
        "glimps.birth/v0",
        "glimps.emission_census/v0",
        "glimps.wound/v0",
    }


def test_assay_validate_cli_rejects_non_string_receipt_type_json(tmp_path):
    malformed = tmp_path / "malformed.json"
    write_json(malformed, {"receipt_type": None})
    result, report = run_json_command("scripts/assay_validate.py", str(malformed), "--json")
    assert result.returncode == 1
    assert report["ok"] is False
    assert report["receipt_type"] is None
    assert report["errors"] == ["receipt_type: must be a string"]


def test_assay_validate_cli_writes_profile_output_report(tmp_path):
    output = tmp_path / "glimps-report.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/assay_validate.py",
            "profiles/glimps/examples/agent_failure_birth_receipt.json",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    report = load_json(output)
    assert report == {
        "ok": True,
        "receipt_type": "glimps.birth/v0",
        "profile": "glimps",
        "errors": [],
    }


def test_standalone_glimps_validator_still_works():
    result, report = run_json_command(
        "scripts/glimps_validate.py",
        "profiles/glimps/examples/agent_failure_birth_receipt.json",
        "--json",
    )
    assert result.returncode == 0
    assert report["passed"] is True
    assert report["results"][0]["receipt_type"] == "glimps.birth/v0"
