# ============================================================================
# Tests for shared/schemas.py
# ============================================================================
"""
Unit tests for shared schemas module - Pydantic data models
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import (
    TriageResponse,
    APIResponse,
    TriageRequest,
    LegacyTriageResponse,
    get_fallback_response,
)
from shared.constants import RiskLevel, SymptomCategory


def test_triage_response_creation():
    """Test TriageResponse model creation"""
    print("=" * 50)
    print("Testing TriageResponse Model...")
    print("=" * 50)
    
    # Valid response with correct field names
    response = TriageResponse(
        risk_level="ER",
        category="Urinary & Genital",
        red_flags=["Male cat straining to urinate"],
        reasoning_summary=["Urinary blockage can be fatal within 24-48 hours"],
        recommended_actions=["Go to emergency vet immediately"],
        what_to_monitor=["Any urine production"],
        follow_up_questions=[],
        disclaimer="This is not a diagnosis. Please consult a vet."
    )
    
    assert response.risk_level == "ER"
    assert response.category == "Urinary & Genital"
    assert len(response.red_flags) == 1
    print(f"  ✓ Created TriageResponse: risk_level={response.risk_level}")
    
    # Test dict conversion
    response_dict = response.model_dump()
    assert "risk_level" in response_dict
    assert "category" in response_dict
    assert "reasoning_summary" in response_dict
    assert "recommended_actions" in response_dict
    print(f"  ✓ Converted to dict with correct fields")
    
    print("PASSED")


def test_triage_response_validation():
    """Test TriageResponse validation"""
    print("\n" + "=" * 50)
    print("Testing TriageResponse Validation...")
    print("=" * 50)
    
    # Test with all risk levels
    for level in ["ER", "TODAY", "SOON", "MONITOR"]:
        response = TriageResponse(
            risk_level=level,
            category="Stomach Upset",
            red_flags=[],
            reasoning_summary=["Test reason"],
            recommended_actions=["Test action"],
            what_to_monitor=["Test monitor"],
            follow_up_questions=[],
            disclaimer="Test disclaimer for validation."
        )
        assert response.risk_level == level
        print(f"  ✓ Risk level '{level}' accepted")
    
    print("PASSED")


def test_api_response_success():
    """Test APIResponse success case"""
    print("\n" + "=" * 50)
    print("Testing APIResponse Success...")
    print("=" * 50)
    
    triage = TriageResponse(
        risk_level="MONITOR",
        category="Stomach Upset",
        red_flags=[],
        reasoning_summary=["Single vomiting episode"],
        recommended_actions=["Withhold food for 2 hours"],
        what_to_monitor=["Additional vomiting"],
        follow_up_questions=[],
        disclaimer="This is not a diagnosis. Always consult a vet."
    )
    
    api_response = APIResponse(
        success=True,
        trace_id="test-123",
        processing_time_ms=100,
        data=triage,
        error_code=None
    )
    
    assert api_response.success == True
    assert api_response.data is not None
    assert api_response.error_code is None
    print(f"  ✓ APIResponse success: {api_response.success}")
    
    print("PASSED")


def test_api_response_error():
    """Test APIResponse error case"""
    print("\n" + "=" * 50)
    print("Testing APIResponse Error...")
    print("=" * 50)
    
    api_response = APIResponse(
        success=False,
        trace_id="test-456",
        processing_time_ms=50,
        data=None,
        error_code="INVALID_SPECIES",
        error_message="Invalid species: hamster is not supported"
    )
    
    assert api_response.success == False
    assert api_response.data is None
    assert api_response.error_code is not None
    print(f"  ✓ APIResponse error: {api_response.error_message}")
    
    print("PASSED")


def test_triage_request():
    """Test TriageRequest model"""
    print("\n" + "=" * 50)
    print("Testing TriageRequest Model...")
    print("=" * 50)
    
    request = TriageRequest(
        species="cat",
        category="Breathing Issues",
        structured_fields={"open_mouth_breathing": "Yes"},
        user_description="My cat is breathing with mouth open"
    )
    
    assert request.species == "cat"
    assert request.category == "Breathing Issues"
    assert request.structured_fields["open_mouth_breathing"] == "Yes"
    print(f"  ✓ TriageRequest: species={request.species}, category={request.category}")
    
    print("PASSED")


def test_legacy_triage_response():
    """Test LegacyTriageResponse model (backward compatibility)"""
    print("\n" + "=" * 50)
    print("Testing LegacyTriageResponse (backward compat)...")
    print("=" * 50)
    
    # Legacy format with old field names (why, next_steps_now)
    legacy = LegacyTriageResponse(
        risk_level="ER",
        category="Urinary & Genital",
        red_flags=["Male cat straining"],
        why=["Urinary blockage"],
        next_steps_now=["Go to ER"],
        what_to_monitor=["Urine output"],
        follow_up_questions=[],
        disclaimer="This is not a diagnosis. Always consult a veterinarian."
    )
    
    assert legacy.risk_level == "ER"
    assert legacy.category == "Urinary & Genital"
    print(f"  ✓ LegacyTriageResponse: risk_level={legacy.risk_level}")
    
    # Test conversion to unified format
    unified = legacy.to_unified()
    assert unified.risk_level == "ER"
    assert unified.reasoning_summary == ["Urinary blockage"]
    assert unified.recommended_actions == ["Go to ER"]
    print(f"  ✓ Converted to unified format successfully")
    
    print("PASSED")


def test_get_fallback_response():
    """Test fallback response generation"""
    print("\n" + "=" * 50)
    print("Testing get_fallback_response...")
    print("=" * 50)
    
    fallback = get_fallback_response("Test error")
    
    # Should return a valid TriageResponse
    assert fallback.risk_level is not None
    assert fallback.category is not None
    assert len(fallback.reasoning_summary) > 0
    assert len(fallback.recommended_actions) > 0
    print(f"  ✓ Fallback risk_level: {fallback.risk_level}")
    print(f"  ✓ Fallback has is_fallback metadata: {fallback.is_fallback}")
    
    print("PASSED")


def test_text_truncation():
    """Test automatic text truncation for long items"""
    print("\n" + "=" * 50)
    print("Testing Text Truncation...")
    print("=" * 50)
    
    # Create response with very long text
    long_text = "A" * 150  # 150 chars, should be truncated to 120
    
    response = TriageResponse(
        risk_level="MONITOR",
        category="Stomach Upset",
        red_flags=[],
        reasoning_summary=[long_text],
        recommended_actions=["Short action"],
        what_to_monitor=[],
        follow_up_questions=[],
        disclaimer="This is not a diagnosis. Always consult a vet."
    )
    
    # Check if truncated
    truncated_text = response.reasoning_summary[0]
    assert len(truncated_text) <= 120 or truncated_text.endswith("...")
    print(f"  ✓ Long text truncated: {len(truncated_text)} chars")
    
    print("PASSED")


def run_all_tests():
    """Run all schema tests"""
    test_triage_response_creation()
    test_triage_response_validation()
    test_api_response_success()
    test_api_response_error()
    test_triage_request()
    test_legacy_triage_response()
    test_get_fallback_response()
    test_text_truncation()
    
    print("\n" + "=" * 50)
    print("ALL SCHEMA TESTS PASSED!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
