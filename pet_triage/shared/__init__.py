# shared/__init__.py
"""
Shared module - Single Source of Truth for Pet Triage AI Backend

This module contains all shared definitions, constants, schemas, and rules
that must be consistent across the entire application.

Usage:
    from shared.constants import SymptomCategory, RiskLevel
    from shared.schemas import TriageResponse, APIResponse
    from shared.red_flags import check_immediate_er
"""

# Note: Imports are done at module level for lazy loading
# Import specific items as needed to avoid circular imports

__all__ = [
    # Constants (from shared.constants)
    "SymptomCategory",
    "RiskLevel",
    "RISK_LEVEL_DESCRIPTIONS",
    "SEVERITY_TO_RISK_LEVEL",
    "normalize_risk_level",
    "SUPPORTED_SPECIES",
    "SUPPORTED_CATEGORIES",
    "DEFAULT_DISCLAIMER",
    "OUTPUT_LIMITS",
    "INPUT_LIMITS",
    "MODEL_CONFIG",
    "TIMEOUT_CONFIG",
    # Schemas (from shared.schemas)
    "TriageResponse",
    "APIResponse",
    "TriageRequest",
    "get_fallback_response",
    # Errors (from shared.errors)
    "ErrorCode",
    "TriageError",
    # Red Flags (from shared.red_flags)
    "check_immediate_er",
    "check_red_flags",
    "check_text_for_red_flags",
    # Prompts (from shared.prompts)
    "UNIFIED_SYSTEM_PROMPT",
    "build_runtime_prompt",
    "build_triage_message",
    "get_triage_system_prompt",
    "FEW_SHOT_EXAMPLES",
]


def __getattr__(name):
    """Lazy loading of module attributes."""
    
    # Constants
    if name in ("SymptomCategory", "RiskLevel", "RISK_LEVEL_DESCRIPTIONS", 
                "SEVERITY_TO_RISK_LEVEL", "normalize_risk_level", "SUPPORTED_SPECIES",
                "SUPPORTED_CATEGORIES", "DEFAULT_DISCLAIMER", "OUTPUT_LIMITS", 
                "INPUT_LIMITS", "MODEL_CONFIG", "TIMEOUT_CONFIG"):
        from shared import constants
        return getattr(constants, name)
    
    # Schemas
    if name in ("TriageResponse", "APIResponse", "TriageRequest", "get_fallback_response"):
        from shared import schemas
        return getattr(schemas, name)
    
    # Errors
    if name in ("ErrorCode", "TriageError"):
        from shared import errors
        return getattr(errors, name)
    
    # Red Flags
    if name in ("check_immediate_er", "check_red_flags", "check_text_for_red_flags"):
        from shared import red_flags
        return getattr(red_flags, name)
    
    # Prompts
    if name in ("UNIFIED_SYSTEM_PROMPT", "build_runtime_prompt", "build_triage_message",
                "get_triage_system_prompt", "FEW_SHOT_EXAMPLES"):
        from shared import prompts
        return getattr(prompts, name)
    
    raise AttributeError(f"module 'shared' has no attribute '{name}'")
