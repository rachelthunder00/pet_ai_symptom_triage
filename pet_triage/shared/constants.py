# shared/constants.py
"""
Constants and Enumerations - SINGLE SOURCE OF TRUTH

All modules in the Pet Triage AI system MUST import constants from this file.
Do NOT define duplicate constants elsewhere.

Covers:
- Symptom categories (9 types)
- Risk levels (ER/TODAY/SOON/MONITOR)
- Severity mapping (RAG → unified)
- Supported species
- Disclaimers
"""

from enum import Enum
from typing import List


# =============================================================================
# SYMPTOM CATEGORIES (9 types - EXACT values, no variants)
# =============================================================================

class SymptomCategory(str, Enum):
    """
    10 supported symptom categories - SINGLE SOURCE OF TRUTH
    All modules MUST use this enum. No synonyms, no variants.
    """
    TOXIC_INGESTION = "Toxic Ingestion & Poisoning"
    STOMACH_UPSET = "Stomach Upset"
    ITCHING_SKIN = "Itching & Skin Issues"
    INJURY_BLEEDING = "Injury & Bleeding"
    BEHAVIOUR_CHANGES = "Concerning Behaviour Changes"
    EARS_EYES_MOUTH = "Ears, Eyes, and Mouth"
    BREATHING_ISSUES = "Breathing Issues"
    URINARY_GENITAL = "Urinary & Genital"
    SOMETHING_ELSE = "Something Else"
    GENERAL_QUESTION = "General Question"
    
    @classmethod
    def values(cls) -> List[str]:
        """Return list of all category values."""
        return [e.value for e in cls]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is a valid category."""
        return value in cls.values()
    
    @classmethod
    def from_string(cls, value: str) -> "SymptomCategory":
        """Get enum from string, with fuzzy matching for common variants."""
        # Direct match
        if value in cls.values():
            for e in cls:
                if e.value == value:
                    return e
        
        # Fuzzy matching for common variants
        value_lower = value.lower().strip()
        mapping = {
            "toxic": cls.TOXIC_INGESTION,
            "poison": cls.TOXIC_INGESTION,
            "stomach": cls.STOMACH_UPSET,
            "vomit": cls.STOMACH_UPSET,
            "diarrhea": cls.STOMACH_UPSET,
            "itch": cls.ITCHING_SKIN,
            "skin": cls.ITCHING_SKIN,
            "rash": cls.ITCHING_SKIN,
            "injury": cls.INJURY_BLEEDING,
            "bleed": cls.INJURY_BLEEDING,
            "wound": cls.INJURY_BLEEDING,
            "musculoskeletal": cls.INJURY_BLEEDING,  # Map RAG variant
            "behaviour": cls.BEHAVIOUR_CHANGES,
            "behavior": cls.BEHAVIOUR_CHANGES,
            "seizure": cls.BEHAVIOUR_CHANGES,
            "ear": cls.EARS_EYES_MOUTH,
            "eye": cls.EARS_EYES_MOUTH,
            "mouth": cls.EARS_EYES_MOUTH,
            "breath": cls.BREATHING_ISSUES,
            "respiratory": cls.BREATHING_ISSUES,
            "urinary": cls.URINARY_GENITAL,
            "genital": cls.URINARY_GENITAL,
        }
        
        for key, category in mapping.items():
            if key in value_lower:
                return category
        
        return cls.SOMETHING_ELSE


# Legacy support - list format for backward compatibility
SUPPORTED_CATEGORIES = SymptomCategory.values()


# =============================================================================
# RISK LEVELS (4 levels - EXACT values)
# =============================================================================

class RiskLevel(str, Enum):
    """
    4 risk levels - SINGLE SOURCE OF TRUTH
    All modules MUST use these exact values.
    """
    ER = "ER"           # Emergency - Go to emergency vet NOW
    TODAY = "TODAY"     # Urgent - Vet visit today
    SOON = "SOON"       # Non-urgent - Vet visit within 24-48 hours
    MONITOR = "MONITOR" # Low-risk - Safe to monitor at home
    
    @classmethod
    def values(cls) -> List[str]:
        """Return list of all risk level values."""
        return [e.value for e in cls]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is a valid risk level."""
        return value.upper() in cls.values()
    
    @classmethod
    def priority(cls, level: "RiskLevel") -> int:
        """Get priority order (higher = more urgent)."""
        priorities = {
            cls.ER: 4,
            cls.TODAY: 3,
            cls.SOON: 2,
            cls.MONITOR: 1,
        }
        return priorities.get(level, 0)


# Risk level descriptions for UI/documentation
RISK_LEVEL_DESCRIPTIONS = {
    RiskLevel.ER: "Go to emergency vet NOW",
    RiskLevel.TODAY: "Vet visit today",
    RiskLevel.SOON: "Vet visit within 24-48 hours",
    RiskLevel.MONITOR: "Safe to monitor at home"
}

# Legacy support
RISK_LEVELS = {level.value: RISK_LEVEL_DESCRIPTIONS[level] for level in RiskLevel}


# =============================================================================
# SEVERITY MAPPING (RAG/tools.py → unified RiskLevel)
# =============================================================================

SEVERITY_TO_RISK_LEVEL = {
    # RAG tools.py uses these
    "CRITICAL": RiskLevel.ER,
    "URGENT": RiskLevel.TODAY,
    "MODERATE": RiskLevel.SOON,
    "NORMAL": RiskLevel.MONITOR,
    "LOW": RiskLevel.MONITOR,
    
    # Image analyzer uses these (lowercase)
    # Note: "urgent" from image analyzer means "needs attention today", not ER-level emergency
    "urgent": RiskLevel.TODAY,
    "consult_vet": RiskLevel.TODAY,
    "monitor": RiskLevel.MONITOR,  # Semantic consistency: "monitor" → MONITOR
    "normal": RiskLevel.MONITOR,
    
    # Direct values (for passthrough)
    "ER": RiskLevel.ER,
    "TODAY": RiskLevel.TODAY,
    "SOON": RiskLevel.SOON,
    "MONITOR": RiskLevel.MONITOR,
    
    # Fallback
    "UNKNOWN": RiskLevel.TODAY,  # Conservative default
}


def normalize_risk_level(raw_severity: str) -> RiskLevel:
    """
    Convert any severity string to unified RiskLevel.
    
    Args:
        raw_severity: Raw severity string from any source
        
    Returns:
        Normalized RiskLevel enum value
    """
    if not raw_severity:
        return RiskLevel.TODAY  # Conservative default
    
    # Try direct mapping first
    if raw_severity in SEVERITY_TO_RISK_LEVEL:
        return SEVERITY_TO_RISK_LEVEL[raw_severity]
    
    # Try uppercase
    upper = raw_severity.upper()
    if upper in SEVERITY_TO_RISK_LEVEL:
        return SEVERITY_TO_RISK_LEVEL[upper]
    
    # Keyword matching as fallback
    lower = raw_severity.lower()
    if "critical" in lower or "emergency" in lower:
        return RiskLevel.ER
    elif "urgent" in lower or "high" in lower:
        return RiskLevel.TODAY
    elif "moderate" in lower or "medium" in lower:
        return RiskLevel.SOON
    elif "low" in lower or "normal" in lower or "monitor" in lower:
        return RiskLevel.MONITOR
    
    # Conservative default
    return RiskLevel.TODAY


# =============================================================================
# SUPPORTED SPECIES
# =============================================================================

SUPPORTED_SPECIES = ["dog", "cat"]


# =============================================================================
# DISCLAIMERS
# =============================================================================

DEFAULT_DISCLAIMER = (
    "This is not a veterinary diagnosis. If symptoms worsen or you're concerned, "
    "seek veterinary care immediately."
)

ER_DISCLAIMER = (
    "EMERGENCY: Seek immediate veterinary care. This is not a diagnosis."
)


# =============================================================================
# OUTPUT LIMITS (for UI constraints)
# =============================================================================

OUTPUT_LIMITS = {
    "reasoning_summary": 3,      # Max items
    "recommended_actions": 6,    # Max items
    "what_to_monitor": 5,        # Max items
    "follow_up_questions": 2,    # Max items
    "red_flags": 5,              # Max items
    "max_item_length": 120,      # Max chars per item
}


# =============================================================================
# INPUT LIMITS
# =============================================================================

INPUT_LIMITS = {
    "max_text_length": 1200,     # Max chars for user description
    "max_image_size_mb": 15,     # Max image size (increased for smartphone photos)
    "allowed_image_types": ["image/jpeg", "image/jpg", "image/png", "image/webp"],
}


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

MODEL_CONFIG = {
    "intake": "gpt-4o-mini",      # Cheapest, for initial classification
    "triage": "gpt-4.1-mini",     # Main triage engine
    "fallback": "gpt-4.1",        # Fallback model for complex cases
    "vision": "gpt-4o",           # Image analysis
    "embedding": "text-embedding-3-small",  # RAG embeddings
}

# Timeouts in seconds
TIMEOUT_CONFIG = {
    "llm_call": 30,
    "llm_retry_backoff": 2,
    "rag_retrieval": 5,
    "image_analysis": 15,
    "vet_search": 10,
    "web_search": 15,
}

# Rate limiting configuration
# Conservative limits to prevent cost overruns and abuse
RATE_LIMIT_CONFIG = {
    "llm_calls_per_minute": 30,      # Max LLM calls per minute
    "llm_calls_per_hour": 500,       # Max LLM calls per hour
    "image_calls_per_minute": 10,    # Max image analysis calls per minute
}
