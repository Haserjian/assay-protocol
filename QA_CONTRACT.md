# QA Contract (v1)

This repository uses a machine-readable QA contract at [`.github/qa_contract.yaml`](.github/qa_contract.yaml).

Purpose:
- Keep CI invariants stable.
- Catch accidental workflow drift before merge.

The validator is [`scripts/ci/validate_qa_contract.py`](scripts/ci/validate_qa_contract.py).

CI enforcement:
- Workflow: [`.github/workflows/qa-contract-drift.yml`](.github/workflows/qa-contract-drift.yml)
- Fails if required workflow/job/step/action invariants drift.

Current tier:
- `public` baseline
