"""Shared core types for CSP gateway extensions.

This module re-exports canonical types from ``assay_gateway.types`` so
PCCap code uses the same decision/principal enums as the base gateway.
"""

from assay_gateway.types import Decision, DecisionResult, Principal, ReasonCode, RiskCategory

__all__ = [
    "Decision",
    "DecisionResult",
    "Principal",
    "ReasonCode",
    "RiskCategory",
]
