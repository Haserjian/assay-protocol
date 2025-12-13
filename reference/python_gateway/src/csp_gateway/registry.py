"""Tool Registry - MUST 1: Capability inventory + trust classification."""

from .types import RiskCategory, ToolEntry, TrustLevel


class ToolRegistry:
    """Registry of tools with trust and risk classification."""

    def __init__(self):
        self._tools: dict[tuple[str, str], ToolEntry] = {}
        self._trust_config: dict[str, TrustLevel] = {}
        self._risk_patterns: dict[str, RiskCategory] = {}

    def configure_trust(self, server_id: str, trust_level: TrustLevel) -> None:
        """Configure trust level for a server."""
        self._trust_config[server_id] = trust_level

    def configure_risk(self, tool_pattern: str, risk_category: RiskCategory) -> None:
        """Configure risk category for tool patterns."""
        self._risk_patterns[tool_pattern] = risk_category

    def register(self, server_id: str, tool_name: str, schema: dict | None = None) -> ToolEntry:
        """Register a tool from a server."""
        trust_level = self._trust_config.get(server_id, TrustLevel.UNKNOWN)
        risk_category = self._classify_risk(tool_name)

        entry = ToolEntry(
            server_id=server_id,
            tool_name=tool_name,
            trust_level=trust_level,
            risk_category=risk_category,
            schema=schema,
        )
        self._tools[(server_id, tool_name)] = entry
        return entry

    def get(self, server_id: str, tool_name: str) -> ToolEntry | None:
        """Get a tool entry."""
        return self._tools.get((server_id, tool_name))

    def list_all(self) -> list[ToolEntry]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_for_server(self, server_id: str) -> list[ToolEntry]:
        """List tools for a specific server."""
        return [t for t in self._tools.values() if t.server_id == server_id]

    def _classify_risk(self, tool_name: str) -> RiskCategory:
        """Classify risk based on tool name patterns."""
        for pattern, category in self._risk_patterns.items():
            if pattern in tool_name.lower():
                return category

        # Default risk levels by common patterns
        critical_patterns = ["delete", "rm", "drop", "truncate", "exec", "shell"]
        high_patterns = ["write", "update", "modify", "create"]
        medium_patterns = ["read", "get", "list", "query"]

        tool_lower = tool_name.lower()
        for p in critical_patterns:
            if p in tool_lower:
                return RiskCategory.CRITICAL
        for p in high_patterns:
            if p in tool_lower:
                return RiskCategory.HIGH
        for p in medium_patterns:
            if p in tool_lower:
                return RiskCategory.MEDIUM

        return RiskCategory.LOW
