"""Preflight Validation - MUST 7: Validation + guardrails."""

import json
from dataclasses import dataclass
from pathlib import Path

from .types import Decision, DecisionResult, ReasonCode


@dataclass
class ValidationResult:
    """Result of preflight validation."""

    valid: bool
    reason_codes: list[ReasonCode]


class PreflightValidator:
    """Validates tool requests before dispatch.

    MUST 7: Schema validation, size limits, path checks.
    """

    def __init__(
        self,
        max_payload_bytes: int = 1_000_000,
        workspace: str | None = None,
    ):
        self._max_payload_bytes = max_payload_bytes
        self._workspace = Path(workspace).resolve() if workspace else None
        self._schemas: dict[str, dict] = {}
        self._file_tools: set[str] = {"fs_read", "fs_write", "fs_delete", "file_read", "file_write"}

    def register_schema(self, tool_name: str, schema: dict) -> None:
        """Register expected schema for a tool."""
        self._schemas[tool_name] = schema

    def add_file_tool(self, tool_name: str) -> None:
        """Mark a tool as a file tool (requires path validation)."""
        self._file_tools.add(tool_name)

    def set_workspace(self, workspace: str) -> None:
        """Set workspace boundary for file tools."""
        self._workspace = Path(workspace).resolve()

    def validate(self, tool_name: str, arguments: dict) -> ValidationResult:
        """Validate a tool request.

        Checks:
        1. Unknown fields (if schema registered)
        2. Payload size
        3. Path traversal (for file tools)
        """
        reason_codes = []

        # Check payload size
        try:
            payload_size = len(json.dumps(arguments))
            if payload_size > self._max_payload_bytes:
                reason_codes.append(ReasonCode.DENY_PAYLOAD_TOO_LARGE)
        except (TypeError, ValueError):
            reason_codes.append(ReasonCode.DENY_UNKNOWN_FIELDS)

        # Check unknown fields
        if tool_name in self._schemas:
            schema = self._schemas[tool_name]
            known_fields = set(schema.get("properties", {}).keys())
            for key in arguments:
                if key not in known_fields:
                    reason_codes.append(ReasonCode.DENY_UNKNOWN_FIELDS)
                    break

        # Check path traversal for file tools
        if tool_name in self._file_tools and self._workspace:
            path_arg = arguments.get("path") or arguments.get("file_path")
            if path_arg and not self._is_within_workspace(path_arg):
                reason_codes.append(ReasonCode.DENY_PATH_TRAVERSAL)

        return ValidationResult(
            valid=len(reason_codes) == 0,
            reason_codes=reason_codes,
        )

    def _is_within_workspace(self, path: str) -> bool:
        """Check if path is within workspace boundary."""
        if not self._workspace:
            return True

        try:
            # Handle relative paths
            if not Path(path).is_absolute():
                target = (self._workspace / path).resolve()
            else:
                target = Path(path).resolve()

            # Check if target is within workspace
            return target.is_relative_to(self._workspace)
        except (ValueError, OSError):
            return False

    def to_decision(self, result: ValidationResult) -> Decision:
        """Convert validation result to decision."""
        if result.valid:
            return Decision(result=DecisionResult.ALLOW)

        return Decision(
            result=DecisionResult.DENY,
            reason_codes=result.reason_codes,
        )
