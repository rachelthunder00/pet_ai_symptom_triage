# ============================================================================
# Tests for shared/constants.py
# ============================================================================
"""
Unit tests for shared constants module - single source of truth
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.constants import (
    SymptomCategory,
    RiskLevel,
    RISK_LEVEL_DESCRIPTIONS,
    SEVERITY_TO_RISK_LEVEL,
    normalize_risk_level,
    SUPPORTED_SPECIES,
    SUPPORTED_CATEGORIES,
    DEFAULT_DISCLAIMER,
    OUTPUT_LIMITS,
    INPUT_LIMITS,
    MODEL_CONFIG,
    TIMEOUT_CONFIG,
)


def test_symptom_categories():
    """Test symptom category enum"""
    print("=" * 50)
    print("Testing Symptom Categories...")
    print("=" * 50)
    
    # Test all 9 categories exist
    expected_categories = [
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
    
    for cat in expected_categories:
        assert cat in [c.value for c in SymptomCategory], f"Missing category: {cat}"
        print(f"  ✓ {cat}")
    
    assert len(SymptomCategory) == 9, "Should have exactly 9 categories"
    print(f"\nTotal categories: {len(SymptomCategory)}")
    print("PASSED")


def test_risk_levels():
    """Test risk level enum"""
    print("\n" + "=" * 50)
    print("Testing Risk Levels...")
    print("=" * 50)
    
    # Test all 4 risk levels exist
    expected_levels = ["ER", "TODAY", "SOON", "MONITOR"]
    
    for level in expected_levels:
        assert level in [r.value for r in RiskLevel], f"Missing risk level: {level}"
        print(f"  ✓ {level}: {RISK_LEVEL_DESCRIPTIONS[level]}")
    
    assert len(RiskLevel) == 4, "Should have exactly 4 risk levels"
    print("PASSED")


def test_severity_mapping():
    """Test severity to risk level mapping"""
    print("\n" + "=" * 50)
    print("Testing Severity → Risk Level Mapping...")
    print("=" * 50)
    
    # Test mapping - normalize_risk_level returns RiskLevel enum
    test_cases = [
        ("CRITICAL", RiskLevel.ER),
        ("URGENT", RiskLevel.TODAY),
        ("MODERATE", RiskLevel.SOON),
        ("NORMAL", RiskLevel.MONITOR),
        ("LOW", RiskLevel.MONITOR),
    ]
    
    for severity, expected_risk in test_cases:
        result = normalize_risk_level(severity)
        assert result == expected_risk, f"Expected {severity} → {expected_risk}, got {result}"
        print(f"  ✓ {severity} → {result.value}")
    
    # Test with already valid risk levels (should pass through)
    for level in ["ER", "TODAY", "SOON", "MONITOR"]:
        result = normalize_risk_level(level)
        assert result.value == level, f"Pass-through failed for {level}"
        print(f"  ✓ {level} → {result.value} (pass-through)")
    
    print("PASSED")


def test_supported_species():
    """Test supported species"""
    print("\n" + "=" * 50)
    print("Testing Supported Species...")
    print("=" * 50)
    
    assert "dog" in SUPPORTED_SPECIES
    assert "cat" in SUPPORTED_SPECIES
    assert len(SUPPORTED_SPECIES) == 2, "MVP should only support dogs and cats"
    
    print(f"  Supported: {SUPPORTED_SPECIES}")
    print("PASSED")


def test_supported_categories_list():
    """Test SUPPORTED_CATEGORIES list matches enum"""
    print("\n" + "=" * 50)
    print("Testing SUPPORTED_CATEGORIES List...")
    print("=" * 50)
    
    enum_values = [c.value for c in SymptomCategory]
    
    for cat in SUPPORTED_CATEGORIES:
        assert cat in enum_values, f"Category '{cat}' not in enum"
        print(f"  ✓ {cat}")
    
    assert len(SUPPORTED_CATEGORIES) == len(SymptomCategory)
    print("PASSED")


def test_config_dicts():
    """Test configuration dictionaries"""
    print("\n" + "=" * 50)
    print("Testing Configuration Dictionaries...")
    print("=" * 50)
    
    # OUTPUT_LIMITS - use unified field names
    assert "reasoning_summary" in OUTPUT_LIMITS, "OUTPUT_LIMITS should have reasoning_summary"
    assert "recommended_actions" in OUTPUT_LIMITS, "OUTPUT_LIMITS should have recommended_actions"
    assert "what_to_monitor" in OUTPUT_LIMITS
    assert "follow_up_questions" in OUTPUT_LIMITS
    print(f"  ✓ OUTPUT_LIMITS: {OUTPUT_LIMITS}")
    
    # INPUT_LIMITS
    assert "max_text_length" in INPUT_LIMITS
    assert "max_image_size_mb" in INPUT_LIMITS
    assert INPUT_LIMITS["max_text_length"] == 1200
    print(f"  ✓ INPUT_LIMITS: {INPUT_LIMITS}")
    
    # MODEL_CONFIG
    assert "intake" in MODEL_CONFIG
    assert "triage" in MODEL_CONFIG
    assert "fallback" in MODEL_CONFIG
    print(f"  ✓ MODEL_CONFIG: {MODEL_CONFIG}")
    
    # TIMEOUT_CONFIG - check for either old or new field names
    assert ("llm_timeout" in TIMEOUT_CONFIG or "llm_call" in TIMEOUT_CONFIG), "Should have LLM timeout"
    assert ("rag_timeout" in TIMEOUT_CONFIG or "rag_retrieval" in TIMEOUT_CONFIG), "Should have RAG timeout"
    print(f"  ✓ TIMEOUT_CONFIG: {TIMEOUT_CONFIG}")
    
    print("PASSED")


def test_default_disclaimer():
    """Test default disclaimer"""
    print("\n" + "=" * 50)
    print("Testing Default Disclaimer...")
    print("=" * 50)
    
    assert DEFAULT_DISCLAIMER is not None
    assert len(DEFAULT_DISCLAIMER) > 20
    assert "diagnosis" in DEFAULT_DISCLAIMER.lower() or "vet" in DEFAULT_DISCLAIMER.lower()
    
    print(f"  Disclaimer: {DEFAULT_DISCLAIMER}")
    print("PASSED")


def run_all_tests():
    """Run all constants tests"""
    test_symptom_categories()
    test_risk_levels()
    test_severity_mapping()
    test_supported_species()
    test_supported_categories_list()
    test_config_dicts()
    test_default_disclaimer()
    
    print("\n" + "=" * 50)
    print("[PASS] ALL SHARED CONSTANTS TESTS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
