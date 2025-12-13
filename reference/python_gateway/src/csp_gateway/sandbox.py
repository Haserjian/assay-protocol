"""Sandbox Boundaries - MUST 8: Filesystem + network isolation."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SandboxConfig:
    """Configuration for execution sandbox.

    MUST 8: Untrusted tool execution must occur in a sandbox.
    """

    workspace: Path
    network_allowlist: list[str] = field(default_factory=list)
    read_only: bool = False
    drop_capabilities: bool = True

    def to_container_config(self) -> dict:
        """Generate container runtime config.

        This is for documentation/integration purposes.
        Actual enforcement happens at container/VM level.
        """
        return {
            "mounts": [
                {
                    "src": str(self.workspace),
                    "dst": "/workspace",
                    "mode": "ro" if self.read_only else "rw",
                }
            ],
            "network": {
                "mode": "allowlist" if self.network_allowlist else "none",
                "allowed_hosts": self.network_allowlist,
            },
            "security": {
                "drop_all_capabilities": self.drop_capabilities,
                "no_new_privileges": True,
            },
        }


class SandboxExecutor:
    """Executor with sandbox boundaries.

    This reference implementation enforces:
    - Filesystem boundary (workspace only)
    - Network allowlist (documented, not enforced in-process)
    """

    def __init__(self, config: SandboxConfig):
        self._config = config
        self._workspace = config.workspace.resolve()

    @property
    def workspace(self) -> Path:
        return self._workspace

    @property
    def fs_policy(self) -> str:
        return "read_only" if self._config.read_only else "workspace_only"

    @property
    def net_policy(self) -> str:
        return "allowlist" if self._config.network_allowlist else "block_all"

    def validate_path(self, path: str) -> bool:
        """Validate path is within workspace."""
        try:
            if not Path(path).is_absolute():
                target = (self._workspace / path).resolve()
            else:
                target = Path(path).resolve()

            return target.is_relative_to(self._workspace)
        except (ValueError, OSError):
            return False

    def resolve_path(self, path: str) -> Path:
        """Resolve path within workspace.

        Raises SandboxViolation if path escapes workspace.
        """
        if not Path(path).is_absolute():
            target = (self._workspace / path).resolve()
        else:
            target = Path(path).resolve()

        if not target.is_relative_to(self._workspace):
            raise SandboxViolation(f"Path escapes workspace: {path}")

        return target

    def can_reach_host(self, host: str) -> bool:
        """Check if host is in network allowlist.

        Note: Actual enforcement happens at network/container level.
        This is for policy checking.
        """
        if not self._config.network_allowlist:
            return False
        return host in self._config.network_allowlist


class SandboxViolation(Exception):
    """Raised when sandbox boundary is violated."""

    pass
