# ============================================================================
# Tests for prompts.py
# ============================================================================
"""
Unit tests for prompt building functions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts import (
    build_case_summary,
    build_triage_message,
    build_intake_message,
    get_triage_system_prompt,
    get_intake_system_prompt,
    get_fallback_system_prompt
)


def test_prompts():
    """Test prompt building"""
    print("=" * 50)
    print("Testing Prompt Building...")
    print("=" * 50)

    # Test case summary building
    summary = build_case_summary(
        species="cat",
        category="Urinary & Genital",
        structured_fields={
            "sex": "male",
            "straining_no_urine": "Yes",
            "hours_since_urination": "14"
        },
        user_description="My cat keeps going to the litter box but nothing comes out",
        pet_profile={
            "name": "Whiskers",
            "age": "5 years",
            "breed": "Domestic Shorthair"
        }
    )

    print("\nCase Summary Example:")
    print("-" * 40)
    print(summary)
    print("-" * 40)

    # Test triage message
    triage_msg = build_triage_message(
        species="cat",
        category="Urinary & Genital",
        structured_fields={
            "sex": "male",
            "straining_no_urine": "Yes",
            "hours_since_urination": "14"
        },
        user_description="My cat keeps going to the litter box but nothing comes out",
        include_examples=False
    )

    print("\nTriage Message Example:")
    print("-" * 40)
    print(triage_msg)
    print("-" * 40)

    print("\nPrompt building tests completed!")


def test_system_prompts():
    """Test that system prompts are properly defined"""
    print("\n" + "=" * 50)
    print("Testing System Prompts...")
    print("=" * 50)

    # Check triage system prompt
    triage_prompt = get_triage_system_prompt()
    assert triage_prompt is not None, "Triage system prompt should be defined"
    assert len(triage_prompt) > 100, "Triage system prompt should be substantial"
    assert "JSON" in triage_prompt, "Triage system prompt should mention JSON output"
    print("Triage system prompt: OK")

    # Check intake system prompt
    intake_prompt = get_intake_system_prompt()
    assert intake_prompt is not None, "Intake system prompt should be defined"
    assert len(intake_prompt) > 50, "Intake system prompt should be substantial"
    print("Intake system prompt: OK")

    # Check fallback system prompt
    fallback_prompt = get_fallback_system_prompt()
    assert fallback_prompt is not None, "Fallback system prompt should be defined"
    print("Fallback system prompt: OK")

    print("\nAll system prompt tests passed!")


if __name__ == "__main__":
    test_prompts()
    test_system_prompts()
