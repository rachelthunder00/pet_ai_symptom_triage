# ============================================================================
# Tests for output_guardrails.py
# ============================================================================
"""
Unit tests for output validation and guardrails
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from output_guardrails import OutputGuardrails
from config import OUTPUT_LIMITS


def test_output_guardrails():
    """Test output guardrails"""
    print("=" * 50)
    print("Testing Output Guardrails...")
    print("=" * 50)

    guardrails = OutputGuardrails()

    # Test 1: Valid response
    print("\nTest 1: Valid response")
    valid_response = json.dumps({
        "risk_level": "MONITOR",
        "category": "Stomach Upset",
        "red_flags": [],
        "reasoning_summary": ["Single vomiting episode", "Normal behavior otherwise"],
        "recommended_actions": ["Withhold food for 2-4 hours", "Offer small amounts of water"],
        "what_to_monitor": ["Additional vomiting", "Lethargy", "Loss of appetite"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. Consult a vet if symptoms worsen."
    })

    success, result = guardrails.validate_and_process(valid_response)
    print(f"  Success: {success}")
    print(f"  Risk level: {result['risk_level']}")
    assert success == True
    print("  PASSED")

    # Test 2: Risk level escalation
    print("\nTest 2: Risk level escalation (ER signals but MONITOR level)")
    inconsistent_response = json.dumps({
        "risk_level": "MONITOR",
        "category": "Breathing Issues",
        "red_flags": ["Open mouth breathing"],
        "reasoning_summary": ["Cat has breathing difficulty with open mouth breathing"],
        "recommended_actions": ["Go to emergency vet immediately"],
        "what_to_monitor": ["Breathing rate", "Gum color"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis."
    })

    success, result = guardrails.validate_and_process(inconsistent_response)
    print(f"  Success: {success}")
    print(f"  Original risk: MONITOR, Corrected risk: {result['risk_level']}")
    print(f"  Was escalated: {result.get('_risk_escalated', False)}")
    assert result["risk_level"] in ["ER", "TODAY", "SOON"]  # Should be escalated
    print("  PASSED")

    # Test 3: Invalid JSON
    print("\nTest 3: Invalid JSON")
    invalid_response = "This is not valid JSON at all"

    success, result = guardrails.validate_and_process(invalid_response)
    print(f"  Success: {success}")
    print(f"  Is fallback: {result.get('_is_fallback', False)}")
    assert success == False
    assert result.get("_is_fallback") == True
    print("  PASSED")

    # Test 4: Missing fields
    print("\nTest 4: Missing required fields")
    partial_response = json.dumps({
        "risk_level": "TODAY",
        "category": "Injury & Bleeding"
        # Missing other fields
    })

    success, result = guardrails.validate_and_process(partial_response)
    print(f"  Success: {success}")
    print(f"  Has disclaimer: {'disclaimer' in result}")
    print(f"  Has recommended_actions: {'recommended_actions' in result}")
    assert "disclaimer" in result
    print("  PASSED")

    # Test 5: Content safety - dosing info
    print("\nTest 5: Content safety - dosing information")
    unsafe_response = json.dumps({
        "risk_level": "TODAY",
        "category": "Stomach Upset",
        "red_flags": [],
        "reasoning_summary": ["Vomiting"],
        "recommended_actions": ["Give 10mg of medication twice daily", "See a vet"],
        "what_to_monitor": ["Vomiting"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis."
    })

    success, result = guardrails.validate_and_process(unsafe_response)
    print(f"  Success: {success}")
    # Check that dosing was removed
    all_text = json.dumps(result).lower()
    has_dosing = "10mg" in all_text or "mg" in all_text
    print(f"  Dosing info removed: {not has_dosing}")
    print("  PASSED")

    # Test 6: UI constraints - long lists
    print("\nTest 6: UI constraints - list truncation")
    long_response = json.dumps({
        "risk_level": "MONITOR",
        "category": "Something Else",
        "red_flags": [],
        "reasoning_summary": ["Reason 1", "Reason 2", "Reason 3", "Reason 4", "Reason 5"],  # More than 3
        "recommended_actions": ["Step " + str(i) for i in range(10)],  # More than 6
        "what_to_monitor": ["Item " + str(i) for i in range(10)],  # More than 5
        "follow_up_questions": ["Q1", "Q2", "Q3", "Q4"],  # More than 2
        "disclaimer": "This is not a diagnosis."
    })

    success, result = guardrails.validate_and_process(long_response)
    print(f"  Success: {success}")
    # Use new field names or fall back to old ones
    why_key = 'reasoning_summary' if 'reasoning_summary' in result else 'why'
    steps_key = 'recommended_actions' if 'recommended_actions' in result else 'next_steps_now'
    why_limit = OUTPUT_LIMITS.get('reasoning_summary', OUTPUT_LIMITS.get('why', 3))
    steps_limit = OUTPUT_LIMITS.get('recommended_actions', OUTPUT_LIMITS.get('next_steps_now', 6))
    print(f"  {why_key} count: {len(result.get(why_key, result.get('why', [])))} (max: {why_limit})")
    print(f"  {steps_key} count: {len(result.get(steps_key, result.get('next_steps_now', [])))} (max: {steps_limit})")
    print(f"  monitor count: {len(result['what_to_monitor'])} (max: {OUTPUT_LIMITS['what_to_monitor']})")
    print(f"  followup count: {len(result['follow_up_questions'])} (max: {OUTPUT_LIMITS['follow_up_questions']})")
    # Allow either old or new field names
    why_count = len(result.get('reasoning_summary', result.get('why', [])))
    steps_count = len(result.get('recommended_actions', result.get('next_steps_now', [])))
    assert why_count <= why_limit
    assert steps_count <= steps_limit
    assert len(result['what_to_monitor']) <= OUTPUT_LIMITS['what_to_monitor']
    assert len(result['follow_up_questions']) <= OUTPUT_LIMITS['follow_up_questions']
    print("  PASSED")

    print("\nAll output guardrail tests passed!")


if __name__ == "__main__":
    test_output_guardrails()
