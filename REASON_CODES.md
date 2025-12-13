# CSP Reason Codes

Canonical reason codes for policy decisions. All conformance tests assert against these codes.

## Decision Reason Codes

| Code | Severity | Description | Operator Action |
|------|----------|-------------|-----------------|
| `ALLOW_POLICY_MATCH` | info | Request matched an allow policy | None |
| `DENY_NO_AUTHN` | high | Missing or invalid authentication | Check client auth config |
| `DENY_NO_PERMISSION` | medium | Principal lacks permission for tool | Review principal permissions |
| `DENY_TOOL_NOT_FOUND` | low | Requested tool does not exist | Check tool name |
| `DENY_NO_MATCHING_RULE` | medium | No policy rule matched (deny-by-default) | Add explicit policy if intended |
| `DENY_UNKNOWN_FIELDS` | medium | Request contains unknown fields | Fix client request schema |
| `DENY_PAYLOAD_TOO_LARGE` | medium | Request exceeds size limit | Reduce payload size |
| `DENY_PATH_TRAVERSAL` | critical | Path escapes workspace boundary | Security review required |
| `DENY_RATE_LIMIT` | low | Rate limit exceeded | Wait or increase quota |
| `DENY_KILL_SWITCH` | critical | Tool disabled by incident response | Contact security team |
| `DENY_PASSTHROUGH_BLOCKED` | critical | Token passthrough attempt blocked | Fix credential broker config |
| `DENY_OAUTH_REDIRECT_INVALID` | critical | OAuth redirect URI validation failed | Check OAuth config |
| `DENY_OAUTH_CLIENT_UNAPPROVED` | high | Dynamic client not in consent registry | Approve client first |
| `REQUIRE_APPROVAL` | medium | Action requires human approval | Route to approver |

## Token Handling Codes

| Code | Description |
|------|-------------|
| `TOKEN_EXCHANGED` | Token exchanged via RFC 8693 |
| `TOKEN_FROM_VAULT` | Credential retrieved from vault |
| `TOKEN_NONE` | No upstream auth required |
| `TOKEN_PASSTHROUGH_BLOCKED` | Passthrough attempt was blocked |

## Incident Codes

| Code | Description |
|------|-------------|
| `INCIDENT_KILL_SWITCH_ACTIVE` | Tools disabled by kill switch |
| `INCIDENT_SESSION_QUARANTINED` | Session in quarantine mode |
| `INCIDENT_TOKENS_REVOKED` | Tokens revoked for principal |

## Usage

```python
from csp_gateway.types import ReasonCode

# In policy decisions
decision = Decision(
    result="deny",
    reason_codes=[ReasonCode.DENY_PATH_TRAVERSAL]
)

# In tests
assert ReasonCode.DENY_PATH_TRAVERSAL in result.reason_codes
```

All tests in `conformance/` and `reference/python_gateway/tests/` MUST use these codes.
