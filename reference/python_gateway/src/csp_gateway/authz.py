"""Authorization - MUST 3 & 4: Identity-bound discovery + Runtime AuthZ."""

from dataclasses import dataclass, field

from .registry import ToolRegistry
from .types import (
    Decision,
    DecisionResult,
    Principal,
    ReasonCode,
    RiskCategory,
    ToolEntry,
)


@dataclass
class Permission:
    """Permission grant for a principal."""

    principal_sub: str
    allowed_tools: set[str] = field(default_factory=set)
    denied_tools: set[str] = field(default_factory=set)
    max_risk: RiskCategory = RiskCategory.HIGH


class PolicyEngine:
    """Policy evaluation engine.

    Implements deny-by-default authorization.
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry
        self._permissions: dict[str, Permission] = {}
        self._kill_switch_tools: set[str] = set()

    def grant(
        self,
        principal_sub: str,
        tools: list[str],
        max_risk: RiskCategory = RiskCategory.HIGH,
    ) -> None:
        """Grant permission to tools for a principal."""
        if principal_sub not in self._permissions:
            self._permissions[principal_sub] = Permission(principal_sub=principal_sub)

        perm = self._permissions[principal_sub]
        perm.allowed_tools.update(tools)
        perm.max_risk = max_risk

    def deny(self, principal_sub: str, tools: list[str]) -> None:
        """Explicitly deny tools for a principal."""
        if principal_sub not in self._permissions:
            self._permissions[principal_sub] = Permission(principal_sub=principal_sub)

        self._permissions[principal_sub].denied_tools.update(tools)

    def activate_kill_switch(self, tool_names: list[str]) -> None:
        """MUST 9: Incident kill switch."""
        self._kill_switch_tools.update(tool_names)

    def deactivate_kill_switch(self, tool_names: list[str]) -> None:
        """Deactivate kill switch for tools."""
        self._kill_switch_tools.difference_update(tool_names)

    def can_discover(self, principal: Principal, tool: ToolEntry) -> bool:
        """MUST 3: Identity-bound tool discovery.

        Principals can only see tools they are permitted to invoke.
        Deny-by-default visibility.
        """
        perm = self._permissions.get(principal.sub)
        if not perm:
            return False

        if tool.tool_name in perm.denied_tools:
            return False

        if tool.tool_name not in perm.allowed_tools:
            return False

        return True

    def filter_tools_list(
        self, principal: Principal, tools: list[ToolEntry]
    ) -> list[ToolEntry]:
        """Filter tools/list response by principal permissions."""
        return [t for t in tools if self.can_discover(principal, t)]

    def evaluate(
        self,
        principal: Principal,
        tool_name: str,
        arguments: dict | None = None,
    ) -> Decision:
        """MUST 4: Runtime authorization.

        Deny-by-default: no matching rule = deny.
        """
        # Check kill switch first (MUST 9)
        if tool_name in self._kill_switch_tools:
            return Decision(
                result=DecisionResult.DENY,
                reason_codes=[ReasonCode.DENY_KILL_SWITCH],
            )

        # Check if tool exists
        tool = None
        for t in self._registry.list_all():
            if t.tool_name == tool_name:
                tool = t
                break

        if not tool:
            return Decision(
                result=DecisionResult.DENY,
                reason_codes=[ReasonCode.DENY_TOOL_NOT_FOUND],
            )

        # Check permissions
        perm = self._permissions.get(principal.sub)
        if not perm:
            return Decision(
                result=DecisionResult.DENY,
                reason_codes=[ReasonCode.DENY_NO_MATCHING_RULE],
            )

        if tool_name in perm.denied_tools:
            return Decision(
                result=DecisionResult.DENY,
                reason_codes=[ReasonCode.DENY_NO_PERMISSION],
            )

        if tool_name not in perm.allowed_tools:
            return Decision(
                result=DecisionResult.DENY,
                reason_codes=[ReasonCode.DENY_NO_MATCHING_RULE],
            )

        # Check risk level
        risk_order = [
            RiskCategory.LOW, RiskCategory.MEDIUM, RiskCategory.HIGH, RiskCategory.CRITICAL
        ]
        if risk_order.index(tool.risk_category) > risk_order.index(perm.max_risk):
            return Decision(
                result=DecisionResult.REQUIRE_APPROVAL,
                reason_codes=[ReasonCode.REQUIRE_APPROVAL],
            )

        return Decision(
            result=DecisionResult.ALLOW,
            reason_codes=[ReasonCode.ALLOW_POLICY_MATCH],
        )
