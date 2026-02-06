# ============================================================================
# Tests for shared/errors.py
# ============================================================================
"""
Unit tests for shared errors module - error codes and exception classes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.errors import (
    ErrorCode,
    TriageError,
    ERROR_HTTP_STATUS,
    ERROR_MESSAGES,
    is_warning,
    is_fatal,
)


def test_error_codes():
    """Test error code enum"""
    print("=" * 50)
    print("Testing Error Codes...")
    print("=" * 50)
    
    # Test essential error codes exist (with ERR_ prefix)
    essential_codes = [
        "ERR_INVALID_SPECIES",
        "ERR_INVALID_CATEGORY",
        "ERR_MISSING_REQUIRED_FIELD",
        "ERR_TEXT_TOO_LONG",
        "ERR_LLM_TIMEOUT",
        "ERR_LLM_UNAVAILABLE",
        "ERR_LLM_INVALID_RESPONSE",
        "ERR_RATE_LIMITED",
    ]
    
    for code in essential_codes:
        assert hasattr(ErrorCode, code), f"Missing error code: {code}"
        print(f"  ✓ ErrorCode.{code}")
    
    print(f"\nTotal error codes: {len(ErrorCode)}")
    print("PASSED")


def test_error_http_status():
    """Test error code to HTTP status mapping"""
    print("\n" + "=" * 50)
    print("Testing Error HTTP Status Mapping...")
    print("=" * 50)
    
    # Check mappings (using ERR_ prefix)
    assert ERROR_HTTP_STATUS[ErrorCode.ERR_INVALID_SPECIES] == 400
    assert ERROR_HTTP_STATUS[ErrorCode.ERR_INVALID_CATEGORY] == 400
    assert ERROR_HTTP_STATUS[ErrorCode.ERR_LLM_TIMEOUT] == 503  # Service Unavailable
    assert ERROR_HTTP_STATUS[ErrorCode.ERR_RATE_LIMITED] == 429
    
    print(f"  ✓ ERR_INVALID_SPECIES → 400")
    print(f"  ✓ ERR_INVALID_CATEGORY → 400")
    print(f"  ✓ ERR_LLM_TIMEOUT → 503")
    print(f"  ✓ ERR_RATE_LIMITED → 429")
    
    print("PASSED")


def test_error_messages():
    """Test error messages"""
    print("\n" + "=" * 50)
    print("Testing Error Messages...")
    print("=" * 50)
    
    # Check messages exist for all ERR_ codes (not WARN_)
    err_codes = [c for c in ErrorCode if c.value.startswith("ERR_")]
    for code in err_codes:
        assert code in ERROR_MESSAGES, f"Missing message for: {code}"
    
    print(f"  ✓ All {len(err_codes)} error codes have messages")
    
    # Check specific messages
    assert "species" in ERROR_MESSAGES[ErrorCode.ERR_INVALID_SPECIES].lower() or "dog" in ERROR_MESSAGES[ErrorCode.ERR_INVALID_SPECIES].lower()
    assert "category" in ERROR_MESSAGES[ErrorCode.ERR_INVALID_CATEGORY].lower()
    
    print(f"  ✓ ERR_INVALID_SPECIES: {ERROR_MESSAGES[ErrorCode.ERR_INVALID_SPECIES][:50]}...")
    print(f"  ✓ ERR_INVALID_CATEGORY: {ERROR_MESSAGES[ErrorCode.ERR_INVALID_CATEGORY][:50]}...")
    
    print("PASSED")


def test_triage_error_creation():
    """Test TriageError exception creation"""
    print("\n" + "=" * 50)
    print("Testing TriageError Exception...")
    print("=" * 50)
    
    # Create error (TriageError uses code and detail, not message)
    error = TriageError(
        code=ErrorCode.ERR_INVALID_SPECIES,
        detail="Hamster is not supported"
    )
    
    assert error.code == ErrorCode.ERR_INVALID_SPECIES
    assert "Hamster" in error.detail
    assert error.http_status == 400
    
    print(f"  ✓ Created TriageError")
    print(f"  ✓ Code: {error.code}")
    print(f"  ✓ Detail: {error.detail}")
    print(f"  ✓ HTTP Status: {error.http_status}")
    
    print("PASSED")


def test_triage_error_with_details():
    """Test TriageError with additional details"""
    print("\n" + "=" * 50)
    print("Testing TriageError with Details...")
    print("=" * 50)
    
    error = TriageError(
        code=ErrorCode.ERR_LLM_UNAVAILABLE,
        detail="API call failed: Connection timeout, model=gpt-4.1-mini"
    )
    
    assert error.detail is not None
    assert "timeout" in error.detail.lower()
    
    print(f"  ✓ Error with detail: {error.detail}")
    
    # Test dict conversion
    error_dict = error.to_dict()
    assert "error_code" in error_dict
    assert "error_message" in error_dict
    assert "detail" in error_dict
    
    print(f"  ✓ Converted to dict: {list(error_dict.keys())}")
    
    print("PASSED")


def test_triage_error_raising():
    """Test raising and catching TriageError"""
    print("\n" + "=" * 50)
    print("Testing TriageError Raising/Catching...")
    print("=" * 50)
    
    try:
        raise TriageError(
            code=ErrorCode.ERR_TEXT_TOO_LONG,
            detail="Text exceeds 1200 character limit"
        )
    except TriageError as e:
        assert e.code == ErrorCode.ERR_TEXT_TOO_LONG
        assert e.http_status == 400
        print(f"  ✓ Caught TriageError: {e.code.value}")
    
    print("PASSED")


def test_triage_error_to_dict():
    """Test TriageError.to_dict() method"""
    print("\n" + "=" * 50)
    print("Testing TriageError.to_dict()...")
    print("=" * 50)
    
    error = TriageError(
        code=ErrorCode.ERR_RATE_LIMITED,
        detail="Too many requests, please wait"
    )
    
    response = error.to_dict()
    
    assert "error_code" in response
    assert response["error_code"] == ErrorCode.ERR_RATE_LIMITED.value
    assert "error_message" in response
    assert response["detail"] == "Too many requests, please wait"
    
    print(f"  ✓ Error code: {response['error_code']}")
    print(f"  ✓ Detail: {response['detail']}")
    
    print("PASSED")


def test_is_warning_and_is_fatal():
    """Test is_warning and is_fatal helper functions"""
    print("\n" + "=" * 50)
    print("Testing is_warning and is_fatal...")
    print("=" * 50)
    
    # Test warning codes
    for code in ErrorCode:
        if code.value.startswith("WARN_"):
            assert is_warning(code), f"{code} should be a warning"
            assert not is_fatal(code), f"{code} should not be fatal"
            print(f"  ✓ {code.value} is a warning")
    
    # Test fatal codes
    for code in ErrorCode:
        if code.value.startswith("ERR_"):
            assert is_fatal(code), f"{code} should be fatal"
            assert not is_warning(code), f"{code} should not be a warning"
    
    print(f"  ✓ is_warning and is_fatal work correctly")
    
    print("PASSED")


def run_all_tests():
    """Run all error tests"""
    test_error_codes()
    test_error_http_status()
    test_error_messages()
    test_triage_error_creation()
    test_triage_error_with_details()
    test_triage_error_raising()
    test_triage_error_to_dict()
    test_is_warning_and_is_fatal()
    
    print("\n" + "=" * 50)
    print("[PASS] ALL SHARED ERRORS TESTS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
