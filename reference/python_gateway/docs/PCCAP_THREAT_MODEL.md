# PCCap Threat Model (Reference)

This note describes security assumptions for Proof-Carrying Capabilities in
`csp_gateway.pccap`.

## Assets

- Capability token integrity (scope, expiry, principal binding).
- Authorization decision correctness for CRITICAL tool actions.
- Replay resistance for one-time approvals.

## Attack Scenarios and Controls

1. Token tampering
- Attack: modify token fields (expiry/scope/principal) after issuance.
- Control: signature covers canonical token payload (`canonical_bytes`), verified with constant-time compare.
- Expected result: `DENY_PCCAP_SIGNATURE_INVALID`.

2. Scope escalation
- Attack: present token for a different tool/path/args.
- Control: exact tool match + constrained args + path-prefix boundary check using `commonpath`.
- Expected result: `DENY_PCCAP_SCOPE_MISMATCH`.

3. Path traversal / sibling-prefix bypass
- Attack: use `..` segments or `/tmp/scratchy` when prefix is `/tmp/scratch`.
- Control: traversal rejection plus normalized absolute path boundary check.
- Expected result: `DENY_PCCAP_SCOPE_MISMATCH`.

4. Expired-token use
- Attack: replay old approval after TTL.
- Control: timestamp expiry check.
- Expected result: `DENY_PCCAP_EXPIRED`.

5. Cross-principal token reuse
- Attack: steal another principal's token.
- Control: principal subject must match token subject.
- Expected result: `DENY_PCCAP_PRINCIPAL_MISMATCH`.

6. Replay of approved one-time action
- Attack: resubmit same token to repeat critical action.
- Control: `single_use=True` default + consumed-token tracking in `PCCapStore`.
- Expected result: `DENY_PCCAP_REPLAY`.

## Residual Risks

- Key compromise: HMAC secret exposure permits token forgery.
- Process-local replay state: in-memory consumed-token tracking does not survive restart.
- No distributed revocation/audit log in this reference implementation.

## Production Hardening Requirements

- Move signing keys to managed KMS/HSM.
- Persist issued/consumed token state with TTL + durable revocation.
- Emit immutable audit receipts for mint/use/revoke events.
- Add clock-skew policy and explicit max TTL policy per risk tier.
