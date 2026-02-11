"""Tests for PCCap (Proof-Carrying Capabilities) module."""

import time

import pytest

from csp_gateway.pccap import (
    Keyring,
    PCCapPolicyEngine,
    PCCapScope,
    PCCapStore,
    PCCapToken,
    ReasonCodePCCap,
    enforce_pccap_for_fs_delete,
    generate_token_id,
    mint_pccap,
    mint_pccap_fs_delete,
)
from csp_gateway.types import Principal


@pytest.fixture
def keyring():
    """Fixed keyring for reproducible tests."""
    return Keyring(secret_key=b"test-secret-key-32-bytes-long!!")


@pytest.fixture
def principal():
    """Test principal."""
    return Principal(sub="agent@test.com", actor_type="agent")


@pytest.fixture
def admin():
    """Admin issuer."""
    return "admin@test.com"


class TestPCCapScope:
    """Tests for PCCapScope matching."""

    def test_exact_tool_match(self):
        scope = PCCapScope(tool_name="fs.delete")
        matches, reason = scope.matches_request("fs.delete", {})
        assert matches is True
        assert reason is None

    def test_tool_mismatch(self):
        scope = PCCapScope(tool_name="fs.delete")
        matches, reason = scope.matches_request("fs.write", {})
        assert matches is False
        assert "tool mismatch" in reason

    def test_path_prefix_match(self):
        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp/scratch")
        matches, reason = scope.matches_request(
            "fs.delete", {"path": "/tmp/scratch/file.txt"}
        )
        assert matches is True

    def test_path_prefix_mismatch(self):
        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp/scratch")
        matches, reason = scope.matches_request(
            "fs.delete", {"path": "/etc/passwd"}
        )
        assert matches is False
        assert "not under allowed prefix" in reason

    def test_path_prefix_sibling_rejected(self):
        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp/scratch")
        matches, reason = scope.matches_request(
            "fs.delete", {"path": "/tmp/scratchy/file.txt"}
        )
        assert matches is False
        assert "not under allowed prefix" in reason

    def test_path_traversal_blocked(self):
        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp/scratch")
        matches, reason = scope.matches_request(
            "fs.delete", {"path": "/tmp/scratch/../../../etc/passwd"}
        )
        assert matches is False
        # Path traversal is blocked - either detected as traversal or as prefix escape
        assert "not under allowed prefix" in reason or "path traversal" in reason

    def test_max_bytes_enforced(self):
        scope = PCCapScope(tool_name="fs.write", max_bytes=100)

        # Under limit
        matches, _ = scope.matches_request("fs.write", {"content": "x" * 50})
        assert matches is True

        # Over limit
        matches, reason = scope.matches_request("fs.write", {"content": "x" * 200})
        assert matches is False
        assert "exceeds max_bytes" in reason

    def test_allowed_args_exact_match(self):
        scope = PCCapScope(
            tool_name="db.query",
            allowed_args={"database": "test_db", "readonly": True},
        )

        # Exact match
        matches, _ = scope.matches_request(
            "db.query", {"database": "test_db", "readonly": True, "query": "SELECT 1"}
        )
        assert matches is True

        # Wrong value
        matches, reason = scope.matches_request(
            "db.query", {"database": "prod_db", "readonly": True}
        )
        assert matches is False
        assert "arg mismatch" in reason


class TestPCCapToken:
    """Tests for PCCapToken lifecycle."""

    def test_token_creation(self, keyring, principal, admin):
        scope = PCCapScope(tool_name="fs.delete")
        token = mint_pccap(
            principal=principal,
            scope=scope,
            issued_by=admin,
            keyring=keyring,
            ttl_seconds=60,
        )

        assert token.token_id.startswith("pccap_")
        assert token.principal_sub == principal.sub
        assert token.signature is not None
        assert not token.is_expired()

    def test_token_expiry(self, keyring, principal, admin):
        scope = PCCapScope(tool_name="fs.delete")
        token = mint_pccap(
            principal=principal,
            scope=scope,
            issued_by=admin,
            keyring=keyring,
            ttl_seconds=1,  # 1 second TTL
        )

        assert not token.is_expired()
        time.sleep(1.1)
        assert token.is_expired()

    def test_token_serialization(self, keyring, principal, admin):
        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp")
        token = mint_pccap(
            principal=principal,
            scope=scope,
            issued_by=admin,
            keyring=keyring,
        )

        d = token.to_dict()
        restored = PCCapToken.from_dict(d)

        assert restored.token_id == token.token_id
        assert restored.scope.tool_name == "fs.delete"
        assert restored.scope.path_prefix == "/tmp"
        assert restored.signature == token.signature
        assert restored.single_use is True
        assert restored.nonce is not None

    def test_signature_verification(self, keyring, principal, admin):
        scope = PCCapScope(tool_name="fs.delete")
        token = mint_pccap(
            principal=principal,
            scope=scope,
            issued_by=admin,
            keyring=keyring,
        )

        # Valid signature
        assert keyring.verify(token) is True

        # Tampered signature
        token.signature = "invalid"
        assert keyring.verify(token) is False

    def test_signature_tampering_detected(self, keyring, principal, admin):
        """Modifying token after signing should fail verification."""
        scope = PCCapScope(tool_name="fs.delete")
        token = mint_pccap(
            principal=principal,
            scope=scope,
            issued_by=admin,
            keyring=keyring,
        )

        # Tamper with the token
        token.expires_at = token.expires_at + 3600  # Try to extend expiry

        # Signature should now fail
        assert keyring.verify(token) is False

        # Restore original expiry, signature should work again
        token.expires_at = token.expires_at - 3600
        assert keyring.verify(token) is True


class TestEnforcePCCap:
    """Tests for PCCap enforcement."""

    def test_valid_token_allowed(self, keyring, principal, admin):
        token = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp/scratch",
            issued_by=admin,
            keyring=keyring,
        )

        allowed, reason, code = enforce_pccap_for_fs_delete(
            principal=principal,
            path="/tmp/scratch/file.txt",
            token=token,
            keyring=keyring,
        )

        assert allowed is True
        assert code == ReasonCodePCCap.ALLOW_PCCAP_VALID

    def test_expired_token_denied(self, keyring, principal, admin):
        token = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp/scratch",
            issued_by=admin,
            keyring=keyring,
            ttl_seconds=0,  # Immediate expiry
        )

        time.sleep(0.1)

        allowed, reason, code = enforce_pccap_for_fs_delete(
            principal=principal,
            path="/tmp/scratch/file.txt",
            token=token,
            keyring=keyring,
        )

        assert allowed is False
        assert code == ReasonCodePCCap.DENY_PCCAP_EXPIRED

    def test_wrong_principal_denied(self, keyring, principal, admin):
        token = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp/scratch",
            issued_by=admin,
            keyring=keyring,
        )

        other_principal = Principal(sub="other@test.com", actor_type="agent")

        allowed, reason, code = enforce_pccap_for_fs_delete(
            principal=other_principal,
            path="/tmp/scratch/file.txt",
            token=token,
            keyring=keyring,
        )

        assert allowed is False
        assert code == ReasonCodePCCap.DENY_PCCAP_PRINCIPAL_MISMATCH

    def test_scope_violation_denied(self, keyring, principal, admin):
        token = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp/scratch",
            issued_by=admin,
            keyring=keyring,
        )

        # Try to delete outside allowed prefix
        allowed, reason, code = enforce_pccap_for_fs_delete(
            principal=principal,
            path="/etc/passwd",
            token=token,
            keyring=keyring,
        )

        assert allowed is False
        assert code == ReasonCodePCCap.DENY_PCCAP_SCOPE_MISMATCH

    def test_invalid_signature_denied(self, keyring, principal, admin):
        token = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp/scratch",
            issued_by=admin,
            keyring=keyring,
        )

        # Corrupt signature
        token.signature = "corrupted"

        allowed, reason, code = enforce_pccap_for_fs_delete(
            principal=principal,
            path="/tmp/scratch/file.txt",
            token=token,
            keyring=keyring,
        )

        assert allowed is False
        assert code == ReasonCodePCCap.DENY_PCCAP_SIGNATURE_INVALID


class TestPCCapStore:
    """Tests for PCCap token storage."""

    def test_store_and_retrieve(self, keyring, principal, admin):
        store = PCCapStore()
        token = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp",
            issued_by=admin,
            keyring=keyring,
        )

        store.store(token)
        retrieved = store.get(token.token_id)

        assert retrieved is not None
        assert retrieved.token_id == token.token_id

    def test_revoke(self, keyring, principal, admin):
        store = PCCapStore()
        token = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp",
            issued_by=admin,
            keyring=keyring,
        )

        store.store(token)
        assert store.get(token.token_id) is not None

        revoked = store.revoke(token.token_id)
        assert revoked is True
        assert store.get(token.token_id) is None

    def test_cleanup_expired(self, keyring, principal, admin):
        store = PCCapStore()

        # Create expired token
        expired = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp",
            issued_by=admin,
            keyring=keyring,
            ttl_seconds=0,
        )
        store.store(expired)

        # Create valid token
        valid = mint_pccap_fs_delete(
            principal=principal,
            path_prefix="/tmp",
            issued_by=admin,
            keyring=keyring,
            ttl_seconds=300,
        )
        store.store(valid)

        time.sleep(0.1)

        # Cleanup
        removed = store.cleanup_expired()
        assert removed == 1

        # Expired should be gone, valid should remain
        assert store.get(expired.token_id) is None
        assert store.get(valid.token_id) is not None

    def test_list_for_principal(self, keyring, admin):
        store = PCCapStore()

        agent1 = Principal(sub="agent1@test.com", actor_type="agent")
        agent2 = Principal(sub="agent2@test.com", actor_type="agent")

        # Tokens for agent1
        t1 = mint_pccap_fs_delete(agent1, "/tmp/a", admin, keyring)
        t2 = mint_pccap_fs_delete(agent1, "/tmp/b", admin, keyring)
        store.store(t1)
        store.store(t2)

        # Token for agent2
        t3 = mint_pccap_fs_delete(agent2, "/tmp/c", admin, keyring)
        store.store(t3)

        # List for agent1
        tokens = store.list_for_principal("agent1@test.com")
        assert len(tokens) == 2

        # List for agent2
        tokens = store.list_for_principal("agent2@test.com")
        assert len(tokens) == 1

    def test_list_excludes_consumed_single_use_tokens(self, keyring, principal, admin):
        store = PCCapStore()
        token = mint_pccap_fs_delete(principal, "/tmp", admin, keyring, single_use=True)
        store.store(token)
        assert len(store.list_for_principal(principal.sub)) == 1
        assert store.mark_used(token.token_id) is True
        assert len(store.list_for_principal(principal.sub)) == 0


class TestPCCapPolicyEngine:
    """Tests for the integrated policy engine."""

    def test_mint_and_evaluate(self, keyring, principal, admin):
        engine = PCCapPolicyEngine(keyring=keyring)

        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp")
        token = engine.mint(
            principal=principal,
            scope=scope,
            issued_by=admin,
        )

        # Evaluate with token ID
        allowed, reason, code = engine.evaluate_with_pccap(
            principal=principal,
            tool_name="fs.delete",
            arguments={"path": "/tmp/file.txt"},
            token_id=token.token_id,
        )

        assert allowed is True
        assert code == "ALLOW_PCCAP_VALID"

    def test_auto_find_matching_token(self, keyring, principal, admin):
        """Engine should find matching token when none specified."""
        engine = PCCapPolicyEngine(keyring=keyring)

        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp")
        engine.mint(principal=principal, scope=scope, issued_by=admin)

        # Evaluate without specifying token_id
        allowed, reason, code = engine.evaluate_with_pccap(
            principal=principal,
            tool_name="fs.delete",
            arguments={"path": "/tmp/file.txt"},
            token_id=None,  # Let engine find it
        )

        assert allowed is True

    def test_single_use_token_replay_denied(self, keyring, principal, admin):
        engine = PCCapPolicyEngine(keyring=keyring)
        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp")
        token = engine.mint(principal=principal, scope=scope, issued_by=admin, single_use=True)

        first_allowed, _, first_code = engine.evaluate_with_pccap(
            principal=principal,
            tool_name="fs.delete",
            arguments={"path": "/tmp/file.txt"},
            token_id=token.token_id,
        )
        assert first_allowed is True
        assert first_code == "ALLOW_PCCAP_VALID"

        second_allowed, _, second_code = engine.evaluate_with_pccap(
            principal=principal,
            tool_name="fs.delete",
            arguments={"path": "/tmp/file.txt"},
            token_id=token.token_id,
        )
        assert second_allowed is False
        assert second_code == "DENY_PCCAP_REPLAY"

    def test_multi_use_token_allows_repeat(self, keyring, principal, admin):
        engine = PCCapPolicyEngine(keyring=keyring)
        scope = PCCapScope(tool_name="fs.delete", path_prefix="/tmp")
        token = engine.mint(principal=principal, scope=scope, issued_by=admin, single_use=False)

        first_allowed, _, first_code = engine.evaluate_with_pccap(
            principal=principal,
            tool_name="fs.delete",
            arguments={"path": "/tmp/file.txt"},
            token_id=token.token_id,
        )
        second_allowed, _, second_code = engine.evaluate_with_pccap(
            principal=principal,
            tool_name="fs.delete",
            arguments={"path": "/tmp/file.txt"},
            token_id=token.token_id,
        )

        assert first_allowed is True
        assert first_code == "ALLOW_PCCAP_VALID"
        assert second_allowed is True
        assert second_code == "ALLOW_PCCAP_VALID"

    def test_no_matching_token(self, keyring, principal, admin):
        engine = PCCapPolicyEngine(keyring=keyring)

        # No tokens minted
        allowed, reason, code = engine.evaluate_with_pccap(
            principal=principal,
            tool_name="fs.delete",
            arguments={"path": "/tmp/file.txt"},
        )

        assert allowed is False
        assert code == "DENY_NO_PCCAP"


class TestTokenIdGeneration:
    """Tests for token ID generation."""

    def test_unique_ids(self):
        ids = [generate_token_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    def test_prefix(self):
        tid = generate_token_id()
        assert tid.startswith("pccap_")
