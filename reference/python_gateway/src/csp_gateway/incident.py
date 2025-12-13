"""Incident Response - MUST 9: Kill switch + revocation."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .types import Principal


@dataclass
class IncidentEvent:
    """Record of an incident response action."""

    ts: str
    action: str
    target: str
    actor: str


class IncidentController:
    """Incident response controls.

    MUST 9: Operational incident mode with kill switch,
    revocation, and quarantine.
    """

    def __init__(self):
        self._kill_switch_tools: set[str] = set()
        self._quarantined_sessions: set[str] = set()
        self._revoked_principals: set[str] = set()
        self._events: list[IncidentEvent] = []
        self._listeners: list[Callable[[IncidentEvent], None]] = []

    def add_listener(self, listener: Callable[[IncidentEvent], None]) -> None:
        """Add event listener."""
        self._listeners.append(listener)

    def activate_kill_switch(self, tool_names: list[str], actor: str = "system") -> None:
        """Immediately deny specified tools."""
        self._kill_switch_tools.update(tool_names)
        self._emit_event("kill_switch_activated", ",".join(tool_names), actor)

    def deactivate_kill_switch(self, tool_names: list[str], actor: str = "system") -> None:
        """Re-enable tools."""
        self._kill_switch_tools.difference_update(tool_names)
        self._emit_event("kill_switch_deactivated", ",".join(tool_names), actor)

    def is_killed(self, tool_name: str) -> bool:
        """Check if tool is killed."""
        return tool_name in self._kill_switch_tools

    def quarantine_session(self, session_id: str, actor: str = "system") -> None:
        """Quarantine a suspicious session."""
        self._quarantined_sessions.add(session_id)
        self._emit_event("session_quarantined", session_id, actor)

    def release_session(self, session_id: str, actor: str = "system") -> None:
        """Release a session from quarantine."""
        self._quarantined_sessions.discard(session_id)
        self._emit_event("session_released", session_id, actor)

    def is_quarantined(self, session_id: str) -> bool:
        """Check if session is quarantined."""
        return session_id in self._quarantined_sessions

    def revoke_principal(self, principal_sub: str, actor: str = "system") -> None:
        """Revoke all tokens for a principal."""
        self._revoked_principals.add(principal_sub)
        self._emit_event("principal_revoked", principal_sub, actor)

    def reinstate_principal(self, principal_sub: str, actor: str = "system") -> None:
        """Reinstate a principal."""
        self._revoked_principals.discard(principal_sub)
        self._emit_event("principal_reinstated", principal_sub, actor)

    def is_revoked(self, principal: Principal) -> bool:
        """Check if principal is revoked."""
        return principal.sub in self._revoked_principals

    def get_events(self) -> list[IncidentEvent]:
        """Get all incident events."""
        return list(self._events)

    def _emit_event(self, action: str, target: str, actor: str) -> None:
        """Emit an incident event."""
        event = IncidentEvent(
            ts=datetime.now(timezone.utc).isoformat(),
            action=action,
            target=target,
            actor=actor,
        )
        self._events.append(event)
        for listener in self._listeners:
            listener(event)
