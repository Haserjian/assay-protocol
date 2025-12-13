"""Receipt Emission - MUST 9: Audit receipts."""

import json
from pathlib import Path
from typing import Callable

from .types import Decision, Principal, Receipt, TokenHandling, hash_args


class ReceiptEmitter:
    """Emits receipts for all gateway operations.

    MUST 9: Every request generates a structured receipt.
    """

    def __init__(self, output_path: Path | None = None):
        self._output_path = output_path
        self._receipts: list[Receipt] = []
        self._listeners: list[Callable[[Receipt], None]] = []

    def add_listener(self, listener: Callable[[Receipt], None]) -> None:
        """Add a receipt listener (for streaming/webhooks)."""
        self._listeners.append(listener)

    def emit(
        self,
        principal: Principal,
        mcp_method: str,
        decision: Decision,
        token_handling: TokenHandling,
        trace_id: str | None = None,
        tool_name: str | None = None,
        server_id: str | None = None,
        arguments: dict | None = None,
        **kwargs,
    ) -> Receipt:
        """Emit a receipt for a gateway operation."""
        receipt = Receipt.create(
            principal=principal,
            mcp_method=mcp_method,
            decision=decision,
            token_handling=token_handling,
            trace_id=trace_id,
            tool_name=tool_name,
            server_id=server_id,
            args_hash=hash_args(arguments) if arguments else None,
            size_bytes_in=len(json.dumps(arguments)) if arguments else None,
            **kwargs,
        )

        self._receipts.append(receipt)

        # Notify listeners
        for listener in self._listeners:
            listener(receipt)

        # Write to file if configured
        if self._output_path:
            with open(self._output_path, "a") as f:
                f.write(json.dumps(receipt.to_dict()) + "\n")

        return receipt

    def get_receipts(self) -> list[Receipt]:
        """Get all emitted receipts."""
        return list(self._receipts)

    def get_last(self) -> Receipt | None:
        """Get the last emitted receipt."""
        return self._receipts[-1] if self._receipts else None

    def clear(self) -> None:
        """Clear stored receipts (for testing)."""
        self._receipts.clear()

    def validate_receipt(self, receipt: Receipt) -> list[str]:
        """Validate receipt has required fields.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        if not receipt.ts:
            errors.append("Missing ts")
        if not receipt.receipt_id:
            errors.append("Missing receipt_id")
        if not receipt.trace_id:
            errors.append("Missing trace_id")
        if not receipt.principal:
            errors.append("Missing principal")
        if not receipt.decision:
            errors.append("Missing decision")
        if receipt.decision and receipt.decision.result is None:
            errors.append("Missing decision.result")

        # MUST 5: passthrough_detected must be false
        if receipt.token_handling and receipt.token_handling.passthrough_detected:
            errors.append("passthrough_detected must be false")

        return errors
