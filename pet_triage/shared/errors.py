# shared/errors.py
"""
Error Codes - Unified error handling across the application.

All error responses MUST use these standardized error codes.
"""

from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """
    Standardized error codes for API responses.
    
    Format: ERR_<CATEGORY>_<SPECIFIC>
    Categories:
    - INPUT: Client input validation errors
    - AUTH: Authentication/authorization errors
    - PROC: Processing/internal errors
    - WARN: Warnings (partial success)
    """
    
    # =========================================================================
    # INPUT ERRORS (400 Bad Request)
    # =========================================================================
    
    ERR_INVALID_SPECIES = "ERR_INVALID_SPECIES"
    """Species is not 'dog' or 'cat'"""
    
    ERR_INVALID_CATEGORY = "ERR_INVALID_CATEGORY"
    """Symptom category not in allowed list"""
    
    ERR_MISSING_REQUIRED_FIELD = "ERR_MISSING_REQUIRED_FIELD"
    """Required field is missing from request"""
    
    ERR_INVALID_IMAGE = "ERR_INVALID_IMAGE"
    """Image format invalid or too large"""
    
    ERR_TEXT_TOO_LONG = "ERR_TEXT_TOO_LONG"
    """User description exceeds max length"""
    
    ERR_INVALID_LOCATION = "ERR_INVALID_LOCATION"
    """Invalid latitude/longitude coordinates"""
    
    ERR_INVALID_JSON = "ERR_INVALID_JSON"
    """Request body is not valid JSON"""
    
    # =========================================================================
    # AUTH ERRORS (401/403/429)
    # =========================================================================
    
    ERR_UNAUTHORIZED = "ERR_UNAUTHORIZED"
    """Missing or invalid authentication"""
    
    ERR_FORBIDDEN = "ERR_FORBIDDEN"
    """Authenticated but not authorized"""
    
    ERR_RATE_LIMITED = "ERR_RATE_LIMITED"
    """Too many requests, rate limit exceeded"""
    
    # =========================================================================
    # PROCESSING ERRORS (500/503)
    # =========================================================================
    
    ERR_LLM_TIMEOUT = "ERR_LLM_TIMEOUT"
    """LLM API call timed out"""
    
    ERR_LLM_UNAVAILABLE = "ERR_LLM_UNAVAILABLE"
    """LLM service is unavailable"""
    
    ERR_LLM_INVALID_RESPONSE = "ERR_LLM_INVALID_RESPONSE"
    """LLM returned invalid/unparseable response"""
    
    ERR_RAG_TIMEOUT = "ERR_RAG_TIMEOUT"
    """RAG/Pinecone query timed out"""
    
    ERR_RAG_UNAVAILABLE = "ERR_RAG_UNAVAILABLE"
    """RAG/Pinecone service is unavailable"""
    
    ERR_IMAGE_ANALYSIS_FAILED = "ERR_IMAGE_ANALYSIS_FAILED"
    """Image analysis service failed"""
    
    ERR_VET_SEARCH_FAILED = "ERR_VET_SEARCH_FAILED"
    """Vet location search failed"""
    
    ERR_INTERNAL = "ERR_INTERNAL"
    """Unexpected internal error"""
    
    # =========================================================================
    # WARNING CODES (200 with warnings)
    # =========================================================================
    
    WARN_RAG_NO_RESULTS = "WARN_RAG_NO_RESULTS"
    """No relevant results from knowledge base"""
    
    WARN_RAG_LOW_CONFIDENCE = "WARN_RAG_LOW_CONFIDENCE"
    """RAG results below confidence threshold"""
    
    WARN_IMAGE_SKIPPED = "WARN_IMAGE_SKIPPED"
    """Image analysis was skipped"""
    
    WARN_FALLBACK_USED = "WARN_FALLBACK_USED"
    """Fallback response was used"""
    
    WARN_RISK_ESCALATED = "WARN_RISK_ESCALATED"
    """Risk level was auto-escalated for safety"""
    
    WARN_TEXT_TRUNCATED = "WARN_TEXT_TRUNCATED"
    """Input text was truncated to fit limit"""
    
    WARN_INJECTION_DETECTED = "WARN_INJECTION_DETECTED"
    """Potential prompt injection detected and sanitized"""


# Error code to HTTP status code mapping
ERROR_HTTP_STATUS = {
    # 400 Bad Request
    ErrorCode.ERR_INVALID_SPECIES: 400,
    ErrorCode.ERR_INVALID_CATEGORY: 400,
    ErrorCode.ERR_MISSING_REQUIRED_FIELD: 400,
    ErrorCode.ERR_INVALID_IMAGE: 400,
    ErrorCode.ERR_TEXT_TOO_LONG: 400,
    ErrorCode.ERR_INVALID_LOCATION: 400,
    ErrorCode.ERR_INVALID_JSON: 400,
    
    # 401 Unauthorized
    ErrorCode.ERR_UNAUTHORIZED: 401,
    
    # 403 Forbidden
    ErrorCode.ERR_FORBIDDEN: 403,
    
    # 429 Too Many Requests
    ErrorCode.ERR_RATE_LIMITED: 429,
    
    # 503 Service Unavailable
    ErrorCode.ERR_LLM_TIMEOUT: 503,
    ErrorCode.ERR_LLM_UNAVAILABLE: 503,
    ErrorCode.ERR_RAG_TIMEOUT: 503,
    ErrorCode.ERR_RAG_UNAVAILABLE: 503,
    ErrorCode.ERR_IMAGE_ANALYSIS_FAILED: 503,
    ErrorCode.ERR_VET_SEARCH_FAILED: 503,
    
    # 500 Internal Server Error
    ErrorCode.ERR_LLM_INVALID_RESPONSE: 500,
    ErrorCode.ERR_INTERNAL: 500,
}


# User-friendly error messages
ERROR_MESSAGES = {
    ErrorCode.ERR_INVALID_SPECIES: "We currently only support dogs and cats.",
    ErrorCode.ERR_INVALID_CATEGORY: "Please select a valid symptom category.",
    ErrorCode.ERR_MISSING_REQUIRED_FIELD: "Please fill in all required fields.",
    ErrorCode.ERR_INVALID_IMAGE: "Image must be JPG or PNG, under 5MB.",
    ErrorCode.ERR_TEXT_TOO_LONG: "Description is too long. Please shorten it.",
    ErrorCode.ERR_INVALID_LOCATION: "Invalid location coordinates.",
    ErrorCode.ERR_INVALID_JSON: "Invalid request format.",
    ErrorCode.ERR_UNAUTHORIZED: "Please sign in to continue.",
    ErrorCode.ERR_FORBIDDEN: "You don't have permission for this action.",
    ErrorCode.ERR_RATE_LIMITED: "Too many requests. Please wait a moment.",
    ErrorCode.ERR_LLM_TIMEOUT: "Service is slow. Please try again.",
    ErrorCode.ERR_LLM_UNAVAILABLE: "Service temporarily unavailable.",
    ErrorCode.ERR_LLM_INVALID_RESPONSE: "We encountered an issue. Please try again.",
    ErrorCode.ERR_RAG_TIMEOUT: "Knowledge search took too long.",
    ErrorCode.ERR_RAG_UNAVAILABLE: "Knowledge base temporarily unavailable.",
    ErrorCode.ERR_IMAGE_ANALYSIS_FAILED: "Could not analyze image. Continuing without it.",
    ErrorCode.ERR_VET_SEARCH_FAILED: "Could not find nearby vets.",
    ErrorCode.ERR_INTERNAL: "Something went wrong. Please try again.",
}


class TriageError(Exception):
    """
    Custom exception for triage-specific errors.
    
    Usage:
        raise TriageError(ErrorCode.ERR_INVALID_SPECIES)
        raise TriageError(ErrorCode.ERR_LLM_TIMEOUT, "Additional details")
    """
    
    def __init__(self, code: ErrorCode, detail: Optional[str] = None):
        self.code = code
        self.detail = detail
        self.message = ERROR_MESSAGES.get(code, "An error occurred.")
        self.http_status = ERROR_HTTP_STATUS.get(code, 500)
        
        super().__init__(f"{code.value}: {self.message}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "error_code": self.code.value,
            "error_message": self.message,
            "detail": self.detail,
        }


def is_warning(code: ErrorCode) -> bool:
    """Check if an error code is a warning (non-fatal)."""
    return code.value.startswith("WARN_")


def is_fatal(code: ErrorCode) -> bool:
    """Check if an error code is fatal (request failed)."""
    return code.value.startswith("ERR_")
