# Assay Profiles

`profiles/registry.json` is the Assay profile discovery surface.

It maps receipt families to profile metadata:

```text
receipt_type -> profile metadata -> schema path -> validator owner -> lifecycle status
```

An incubating profile is visible to Assay validation and has tests, examples, schemas, and a validator owner. Incubating does not mean the profile is a normative Constitutional Receipt Standard profile.

Normative CRS promotion requires a separate promotion receipt or document. Do not mark a profile as `normative_crs_profile: true` without that explicit promotion artifact.

## Registered Profiles

### GLIMPS

Status: incubating.

GLIMPS births candidate sight but grants no authority. It registers:

- `glimps.birth/v0`
- `glimps.emission_census/v0`
- `glimps.wound/v0`

Validate through the profile validator:

```bash
python3 scripts/glimps_validate.py profiles/glimps/examples/agent_failure_birth_receipt.json --json
```

Validate through the general Assay dispatcher:

```bash
python3 scripts/assay_validate.py profiles/glimps/examples/agent_failure_birth_receipt.json --json
```
