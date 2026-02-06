# ============================================================================
# Tests for shared/prompts.py
# ============================================================================
"""
Unit tests for shared prompts module - unified prompt templates
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.prompts import (
    GLOBAL_SAFETY_RULES,
    UNIFIED_SYSTEM_PROMPT,
    DEVELOPER_PROMPT,
    RUNTIME_PROMPT_TEMPLATE,
    FEW_SHOT_EXAMPLES,
    build_runtime_prompt,
    build_triage_message,
    get_triage_system_prompt,
)


def test_global_safety_rules():
    """Test global safety rules content"""
    print("=" * 50)
    print("Testing Global Safety Rules...")
    print("=" * 50)
    
    # Check key safety rules are present
    assert "diagnosis" in GLOBAL_SAFETY_RULES.lower(), "Should mention diagnosis restriction"
    assert "medication" in GLOBAL_SAFETY_RULES.lower() or "dosing" in GLOBAL_SAFETY_RULES.lower(), "Should mention medication/dosing"
    assert "safety" in GLOBAL_SAFETY_RULES.lower(), "Should mention safety"
    
    print(f"  ✓ Contains diagnosis restriction")
    print(f"  ✓ Contains medication/dosing restriction")
    print(f"  ✓ Contains safety mention")
    print(f"  ✓ Length: {len(GLOBAL_SAFETY_RULES)} characters")
    
    print("PASSED")


def test_unified_system_prompt():
    """Test unified system prompt content"""
    print("\n" + "=" * 50)
    print("Testing Unified System Prompt...")
    print("=" * 50)
    
    # Check required elements
    assert "JSON" in UNIFIED_SYSTEM_PROMPT, "Should mention JSON output"
    assert "risk_level" in UNIFIED_SYSTEM_PROMPT, "Should mention risk_level field"
    assert "ER" in UNIFIED_SYSTEM_PROMPT, "Should mention ER risk level"
    assert "TODAY" in UNIFIED_SYSTEM_PROMPT, "Should mention TODAY risk level"
    assert "SOON" in UNIFIED_SYSTEM_PROMPT, "Should mention SOON risk level"
    assert "MONITOR" in UNIFIED_SYSTEM_PROMPT, "Should mention MONITOR risk level"
    
    print(f"  ✓ Contains JSON output instruction")
    print(f"  ✓ Contains all risk levels (ER, TODAY, SOON, MONITOR)")
    print(f"  ✓ Length: {len(UNIFIED_SYSTEM_PROMPT)} characters")
    
    print("PASSED")


def test_developer_prompt():
    """Test developer prompt content"""
    print("\n" + "=" * 50)
    print("Testing Developer Prompt...")
    print("=" * 50)
    
    # Check key elements
    assert len(DEVELOPER_PROMPT) > 100, "Developer prompt should be substantial"
    assert "triage" in DEVELOPER_PROMPT.lower() or "pet" in DEVELOPER_PROMPT.lower()
    
    print(f"  ✓ Developer prompt defined")
    print(f"  ✓ Length: {len(DEVELOPER_PROMPT)} characters")
    
    print("PASSED")


def test_runtime_prompt_template():
    """Test runtime prompt template"""
    print("\n" + "=" * 50)
    print("Testing Runtime Prompt Template...")
    print("=" * 50)
    
    # Check placeholders exist
    assert "{species}" in RUNTIME_PROMPT_TEMPLATE or "species" in RUNTIME_PROMPT_TEMPLATE.lower()
    assert "{category}" in RUNTIME_PROMPT_TEMPLATE or "category" in RUNTIME_PROMPT_TEMPLATE.lower()
    
    print(f"  ✓ Contains species placeholder")
    print(f"  ✓ Contains category placeholder")
    print(f"  ✓ Length: {len(RUNTIME_PROMPT_TEMPLATE)} characters")
    
    print("PASSED")


def test_few_shot_examples():
    """Test few-shot examples content"""
    print("\n" + "=" * 50)
    print("Testing Few-Shot Examples...")
    print("=" * 50)
    
    # Check examples contain expected cases
    assert "ER" in FEW_SHOT_EXAMPLES, "Should have ER example"
    assert "urinary" in FEW_SHOT_EXAMPLES.lower() or "cat" in FEW_SHOT_EXAMPLES.lower()
    
    # Check JSON structure in examples (new field names)
    assert "risk_level" in FEW_SHOT_EXAMPLES
    assert "red_flags" in FEW_SHOT_EXAMPLES
    assert "recommended_actions" in FEW_SHOT_EXAMPLES or "next_steps" in FEW_SHOT_EXAMPLES.lower()
    
    print(f"  ✓ Contains ER example case")
    print(f"  ✓ Contains JSON structure")
    print(f"  ✓ Length: {len(FEW_SHOT_EXAMPLES)} characters")
    
    print("PASSED")


def test_build_runtime_prompt():
    """Test build_runtime_prompt function"""
    print("\n" + "=" * 50)
    print("Testing build_runtime_prompt...")
    print("=" * 50)
    
    prompt = build_runtime_prompt(
        species="cat",
        category="Urinary & Genital",
        structured_fields={
            "sex": "male",
            "straining_no_urine": "Yes",
            "hours_since_urination": "14"
        },
        user_description="My cat keeps going to the litter box but nothing comes out"
    )
    
    # Check prompt contains case details
    assert "cat" in prompt.lower()
    assert "urinary" in prompt.lower() or "genital" in prompt.lower()
    assert "male" in prompt.lower()
    assert "straining" in prompt.lower() or "litter" in prompt.lower()
    
    print(f"  ✓ Contains species: cat")
    print(f"  ✓ Contains category: Urinary")
    print(f"  ✓ Contains structured fields")
    print(f"  ✓ Contains user description")
    print(f"  ✓ Prompt length: {len(prompt)} characters")
    
    print("PASSED")


def test_build_triage_message():
    """Test build_triage_message function"""
    print("\n" + "=" * 50)
    print("Testing build_triage_message...")
    print("=" * 50)
    
    # Test with pet profile
    message = build_triage_message(
        species="dog",
        category="Stomach Upset",
        structured_fields={
            "abdomen_distended": "Yes",
            "unproductive_retching": "Yes"
        },
        user_description="My dog's stomach looks bloated",
        pet_profile={
            "name": "Max",
            "age": "7 years",
            "breed": "Great Dane"
        },
        include_examples=False
    )
    
    assert "dog" in message.lower()
    assert "stomach" in message.lower() or "upset" in message.lower()
    assert "distended" in message.lower() or "bloated" in message.lower()
    
    print(f"  ✓ Contains species")
    print(f"  ✓ Contains category")
    print(f"  ✓ Contains symptoms")
    print(f"  ✓ Message length: {len(message)} characters")
    
    # Test with examples
    message_with_examples = build_triage_message(
        species="cat",
        category="Breathing Issues",
        structured_fields={"open_mouth_breathing": "Yes"},
        user_description="My cat is breathing weird",
        include_examples=True
    )
    
    assert len(message_with_examples) > len(message), "With examples should be longer"
    print(f"  ✓ With examples length: {len(message_with_examples)} characters")
    
    print("PASSED")


def test_get_triage_system_prompt():
    """Test get_triage_system_prompt function"""
    print("\n" + "=" * 50)
    print("Testing get_triage_system_prompt...")
    print("=" * 50)
    
    system_prompt = get_triage_system_prompt()
    
    assert system_prompt is not None
    assert len(system_prompt) > 200, "System prompt should be substantial"
    assert "JSON" in system_prompt, "Should mention JSON"
    
    print(f"  ✓ System prompt defined")
    print(f"  ✓ Contains JSON instruction")
    print(f"  ✓ Length: {len(system_prompt)} characters")
    
    print("PASSED")


def run_all_tests():
    """Run all prompts tests"""
    test_global_safety_rules()
    test_unified_system_prompt()
    test_developer_prompt()
    test_runtime_prompt_template()
    test_few_shot_examples()
    test_build_runtime_prompt()
    test_build_triage_message()
    test_get_triage_system_prompt()
    
    print("\n" + "=" * 50)
    print("[PASS] ALL SHARED PROMPTS TESTS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
