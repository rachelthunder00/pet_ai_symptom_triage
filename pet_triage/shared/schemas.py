# shared/schemas.py
"""
Pydantic Schemas - Unified API Data Models

All API responses MUST use these schemas to ensure consistency
across the entire application.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS (inline for schema independence, but values match constants.py)
# =============================================================================

class RiskLevelEnum(str, Enum):
    ER = "ER"
    TODAY = "TODAY"
    SOON = "SOON"
    MONITOR = "MONITOR"


class SymptomCategoryEnum(str, Enum):
    TOXIC_INGESTION = "Toxic Ingestion & Poisoning"
    STOMACH_UPSET = "Stomach Upset"
    ITCHING_SKIN = "Itching & Skin Issues"
    INJURY_BLEEDING = "Injury & Bleeding"
    BEHAVIOUR_CHANGES = "Concerning Behaviour Changes"
    EARS_EYES_MOUTH = "Ears, Eyes, and Mouth"
    BREATHING_ISSUES = "Breathing Issues"
    URINARY_GENITAL = "Urinary & Genital"
    SOMETHING_ELSE = "Something Else"


# =============================================================================
# SOURCE DOCUMENT SCHEMA
# =============================================================================

class SourceDocument(BaseModel):
    """RAG source document reference."""
    text: str = Field(..., max_length=500, description="Excerpt from source")
    doc_type: str = Field(default="unknown", description="Document type")
    animal_type: Optional[List[str]] = Field(default=None)
    source: Optional[str] = Field(default=None, description="Original source")
    score: Optional[float] = Field(default=None, ge=0, le=1, description="Relevance score")


# =============================================================================
# NEARBY VET SCHEMA
# =============================================================================

class NearbyVet(BaseModel):
    """Veterinary clinic information."""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    distance_km: Optional[float] = None
    is_emergency_clinic: bool = False
    location: Optional[dict] = Field(default=None, description="lat/lng coordinates")


# =============================================================================
# TRIAGE RESPONSE SCHEMA
# =============================================================================

class TriageResponse(BaseModel):
    """
    Unified triage response schema.
    
    ALL triage endpoints MUST return this exact structure.
    Field names are standardized across the application.
    """
    
    # Core triage fields
    risk_level: RiskLevelEnum = Field(
        ..., 
        description="Triage urgency level: ER/TODAY/SOON/MONITOR"
    )
    category: SymptomCategoryEnum = Field(
        ..., 
        description="Symptom category (one of 9 types)"
    )
    red_flags: List[str] = Field(
        default_factory=list, 
        max_items=5,
        description="Detected emergency indicators"
    )
    
    # Reasoning (non-diagnostic)
    reasoning_summary: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=3,
        description="Brief reasons for the risk level (NOT diagnosis)"
    )
    
    # Actions
    recommended_actions: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=6,
        description="Immediate actionable steps for pet owner"
    )
    what_to_monitor: List[str] = Field(
        default_factory=list, 
        max_items=5,
        description="Signs to watch for"
    )
    follow_up_questions: List[str] = Field(
        default_factory=list, 
        max_items=2,
        description="Follow-up questions if info incomplete"
    )
    
    # Sources (from RAG)
    sources: Optional[List[SourceDocument]] = Field(
        default=None,
        description="RAG source documents if available"
    )
    
    # Nearby vets (if location provided and urgent)
    nearby_vets: Optional[List[NearbyVet]] = Field(
        default=None,
        description="Nearby vet clinics if ER/TODAY"
    )
    
    # Mandatory disclaimer
    disclaimer: str = Field(
        default="This is not a veterinary diagnosis. If symptoms worsen or you're concerned, seek veterinary care immediately.",
        min_length=20,
        description="Medical disclaimer (always required)"
    )
    
    # Internal metadata (not shown to user, use public names)
    risk_escalated: Optional[bool] = Field(default=None, exclude=True)
    escalation_reason: Optional[str] = Field(default=None, exclude=True)
    image_context: Optional[str] = Field(default=None, exclude=True)
    is_fallback: Optional[bool] = Field(default=None, exclude=True)
    
    model_config = {
        "use_enum_values": True,
        "extra": "allow"
    }
    
    @field_validator('reasoning_summary', 'recommended_actions', 'what_to_monitor', 'red_flags', mode='before')
    @classmethod
    def truncate_long_items(cls, v):
        """Truncate items longer than 120 characters."""
        if isinstance(v, list):
            return [item[:117] + "..." if isinstance(item, str) and len(item) > 120 else item for item in v]
        return v


# =============================================================================
# LEGACY RESPONSE SCHEMA (for backward compatibility)
# =============================================================================

class LegacyTriageResponse(BaseModel):
    """
    Legacy response format for backward compatibility.
    Maps to the old field names used in existing code.
    """
    risk_level: str
    category: str
    red_flags: List[str] = Field(default_factory=list)
    why: List[str] = Field(default_factory=list)  # Old name for reasoning_summary
    next_steps_now: List[str] = Field(default_factory=list)  # Old name for recommended_actions
    what_to_monitor: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    disclaimer: str = ""
    
    def to_unified(self) -> TriageResponse:
        """Convert legacy format to unified format."""
        return TriageResponse(
            risk_level=self.risk_level,
            category=self.category,
            red_flags=self.red_flags,
            reasoning_summary=self.why,
            recommended_actions=self.next_steps_now,
            what_to_monitor=self.what_to_monitor,
            follow_up_questions=self.follow_up_questions,
            disclaimer=self.disclaimer,
        )
    
    @classmethod
    def from_unified(cls, unified: TriageResponse) -> "LegacyTriageResponse":
        """Convert unified format to legacy format."""
        return cls(
            risk_level=unified.risk_level,
            category=unified.category,
            red_flags=unified.red_flags,
            why=unified.reasoning_summary,
            next_steps_now=unified.recommended_actions,
            what_to_monitor=unified.what_to_monitor,
            follow_up_questions=unified.follow_up_questions,
            disclaimer=unified.disclaimer,
        )


# =============================================================================
# API RESPONSE WRAPPER
# =============================================================================

class APIResponse(BaseModel):
    """
    Top-level API response wrapper.
    
    All API endpoints return this structure.
    """
    
    success: bool = Field(..., description="Whether the request succeeded")
    trace_id: str = Field(..., description="Request trace ID for debugging")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = Field(..., ge=0, description="Total processing time")
    model_used: Optional[str] = Field(default=None, description="LLM model used")
    
    # Response data
    data: Optional[TriageResponse] = Field(default=None, description="Triage response")
    
    # Error info
    error_code: Optional[str] = Field(default=None, description="Error code if failed")
    error_message: Optional[str] = Field(default=None, description="Human-readable error")
    
    # Warnings (non-fatal issues)
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    
    # Metadata
    is_er: bool = Field(default=False, description="Whether this is an emergency")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class PetProfile(BaseModel):
    """Pet profile information."""
    name: Optional[str] = None
    species: str = Field(..., pattern="^(dog|cat)$")
    breed: Optional[str] = None
    age: Optional[str] = None
    weight: Optional[str] = None
    sex: Optional[str] = None
    known_conditions: Optional[List[str]] = None


class TriageRequest(BaseModel):
    """
    Triage request payload from mobile app.
    """
    species: str = Field(..., pattern="^(dog|cat)$", description="Pet species")
    category: str = Field(..., description="Selected symptom category")
    structured_fields: dict = Field(default_factory=dict, description="UI form fields")
    user_description: str = Field(default="", max_length=1200, description="Free text")
    pet_profile: Optional[PetProfile] = None
    
    # Optional image
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image")
    image_type: Optional[str] = Field(default=None, pattern="^image/(jpeg|jpg|png)$")
    
    # Optional location for vet finding
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        valid_categories = [
            "Toxic Ingestion & Poisoning",
            "Stomach Upset",
            "Itching & Skin Issues",
            "Injury & Bleeding",
            "Concerning Behaviour Changes",
            "Ears, Eyes, and Mouth",
            "Breathing Issues",
            "Urinary & Genital",
            "Something Else"
        ]
        if v not in valid_categories:
            raise ValueError(f"Invalid category: {v}")
        return v


# =============================================================================
# FALLBACK RESPONSE
# =============================================================================

def get_fallback_response(reason: str = None) -> TriageResponse:
    """
    Get a safe fallback response when processing fails.
    
    This ensures the app never breaks - always returns a valid response.
    """
    return TriageResponse(
        risk_level=RiskLevelEnum.TODAY,
        category=SymptomCategoryEnum.SOMETHING_ELSE,
        red_flags=[],
        reasoning_summary=[
            "Unable to complete full assessment",
            "Professional evaluation recommended"
        ],
        recommended_actions=[
            "Contact your regular veterinarian during business hours",
            "Monitor your pet closely for any changes",
            "If symptoms worsen, seek emergency veterinary care"
        ],
        what_to_monitor=[
            "Breathing difficulty",
            "Collapse or weakness",
            "Severe pain signs",
            "Worsening of current symptoms"
        ],
        follow_up_questions=[],
        disclaimer="This is not a veterinary diagnosis. If symptoms worsen or you're concerned, seek veterinary care.",
        _is_fallback=True,
    )
