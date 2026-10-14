"""
ChildNutri AI - Central Explanation Module
"""

from ai.explanation.explanation_safety import (
    STATUS_AVAILABLE,
    STATUS_PARTIAL,
    STATUS_NOT_ASSESSED,
    STATUS_NOT_AVAILABLE,
    STATUS_ERROR,
    MEDICAL_DECISION_SUPPORT_NOTICE,
    DATA_LIMITATIONS,
    EVIDENCE_SOURCES,
    ExplanationSafetyValidator
)
from ai.explanation.explanation_rules import ExplanationRules
from ai.explanation.explanation_templates import ExplanationTemplates
from ai.explanation.explanation_engine import HumanExplanationEngine

__all__ = [
    "HumanExplanationEngine",
    "ExplanationRules",
    "ExplanationTemplates",
    "ExplanationSafetyValidator",
    "STATUS_AVAILABLE",
    "STATUS_PARTIAL",
    "STATUS_NOT_ASSESSED",
    "STATUS_NOT_AVAILABLE",
    "STATUS_ERROR",
    "MEDICAL_DECISION_SUPPORT_NOTICE",
    "DATA_LIMITATIONS",
    "EVIDENCE_SOURCES"
]
