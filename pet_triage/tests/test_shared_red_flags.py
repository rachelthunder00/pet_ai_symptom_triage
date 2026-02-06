# ============================================================================
# Tests for shared/red_flags.py
# ============================================================================
"""
Unit tests for shared red flags module - unified emergency detection rules
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.red_flags import (
    check_immediate_er,
    check_text_for_red_flags,
    check_red_flags,
    EMERGENCY_GUM_COLORS,
    DANGEROUS_SUBSTANCES,
    BLOAT_RISK_BREEDS,
    BRACHYCEPHALIC_BREEDS,
    CRITICAL_KEYWORDS,
    URGENT_KEYWORDS,
    MODERATE_KEYWORDS,
)


def test_gum_color_constants():
    """Test emergency gum color constants"""
    print("=" * 50)
    print("Testing Emergency Gum Colors...")
    print("=" * 50)
    
    # Check key emergency gum colors exist
    assert "blue" in EMERGENCY_GUM_COLORS
    assert "pale" in EMERGENCY_GUM_COLORS
    assert "white" in EMERGENCY_GUM_COLORS
    assert "grey" in EMERGENCY_GUM_COLORS or "gray" in EMERGENCY_GUM_COLORS
    
    print(f"  Emergency gum colors: {list(EMERGENCY_GUM_COLORS.keys())}")
    print("PASSED")


def test_dangerous_substances():
    """Test dangerous substances list"""
    print("\n" + "=" * 50)
    print("Testing Dangerous Substances...")
    print("=" * 50)
    
    expected_substances = [
        "antifreeze", "xylitol", "chocolate", "grapes", "raisins",
        "rat poison", "lily"
    ]
    
    # DANGEROUS_SUBSTANCES is a list of tuples
    all_substances = []
    for substance_group in DANGEROUS_SUBSTANCES:
        all_substances.extend(substance_group)
    
    for substance in expected_substances:
        found = any(substance in s.lower() for s in all_substances)
        assert found, f"Missing dangerous substance: {substance}"
        print(f"  ✓ {substance}")
    
    print("PASSED")


def test_breed_lists():
    """Test breed-specific alert lists"""
    print("\n" + "=" * 50)
    print("Testing Breed Alert Lists...")
    print("=" * 50)
    
    # Bloat risk breeds (deep-chested)
    bloat_breeds = ["great dane", "german shepherd", "doberman", "boxer"]
    for breed in bloat_breeds:
        found = any(breed in b.lower() for b in BLOAT_RISK_BREEDS)
        assert found, f"Missing bloat risk breed: {breed}"
    print(f"  ✓ Bloat risk breeds: {len(BLOAT_RISK_BREEDS)} breeds")
    
    # Brachycephalic breeds
    brachy_breeds = ["bulldog", "pug", "french bulldog", "persian"]
    for breed in brachy_breeds:
        found = any(breed in b.lower() for b in BRACHYCEPHALIC_BREEDS)
        assert found, f"Missing brachycephalic breed: {breed}"
    print(f"  ✓ Brachycephalic breeds: {len(BRACHYCEPHALIC_BREEDS)} breeds")
    
    print("PASSED")


def test_keyword_lists():
    """Test keyword severity lists"""
    print("\n" + "=" * 50)
    print("Testing Keyword Severity Lists...")
    print("=" * 50)
    
    # Critical keywords
    critical_expected = ["not breathing", "unconscious", "seizure", "choking"]
    for kw in critical_expected:
        assert kw in CRITICAL_KEYWORDS, f"Missing critical keyword: {kw}"
    print(f"  ✓ Critical keywords: {len(CRITICAL_KEYWORDS)} keywords")
    
    # Urgent keywords
    urgent_expected = ["vomiting blood", "difficulty breathing", "broken bone"]
    for kw in urgent_expected:
        assert kw in URGENT_KEYWORDS, f"Missing urgent keyword: {kw}"
    print(f"  ✓ Urgent keywords: {len(URGENT_KEYWORDS)} keywords")
    
    # Moderate keywords
    moderate_expected = ["vomiting", "diarrhea", "limping"]
    for kw in moderate_expected:
        assert kw in MODERATE_KEYWORDS, f"Missing moderate keyword: {kw}"
    print(f"  ✓ Moderate keywords: {len(MODERATE_KEYWORDS)} keywords")
    
    print("PASSED")


def test_check_immediate_er_gum_color():
    """Test check_immediate_er with gum color emergencies"""
    print("\n" + "=" * 50)
    print("Testing check_immediate_er - Gum Colors...")
    print("=" * 50)
    
    # Test pale gums
    result = check_immediate_er({
        "species": "dog",
        "category": "Injury & Bleeding",
        "gum_color": "pale"
    })
    assert result["is_er"] == True, "Pale gums should trigger ER"
    print(f"  ✓ Pale gums → ER ({result['category']})")
    
    # Test blue gums
    result = check_immediate_er({
        "species": "cat",
        "category": "Breathing Issues",
        "gum_color": "blue"
    })
    assert result["is_er"] == True, "Blue gums should trigger ER"
    print(f"  ✓ Blue gums → ER ({result['category']})")
    
    # Test normal gums - should NOT trigger ER
    result = check_immediate_er({
        "species": "dog",
        "category": "Stomach Upset",
        "gum_color": "pink"
    })
    assert result["is_er"] == False, "Pink (normal) gums should NOT trigger ER"
    print(f"  ✓ Pink gums → No ER")
    
    print("PASSED")


def test_check_immediate_er_male_cat_urinary():
    """Test check_immediate_er with male cat urinary blockage"""
    print("\n" + "=" * 50)
    print("Testing check_immediate_er - Male Cat Urinary...")
    print("=" * 50)
    
    # Male cat straining - should trigger ER
    result = check_immediate_er({
        "species": "cat",
        "category": "Urinary & Genital",
        "sex": "male",
        "straining_no_urine": "Yes"
    })
    assert result["is_er"] == True, "Male cat straining should trigger ER"
    assert result["category"] == "Urinary & Genital"
    print(f"  ✓ Male cat straining → ER")
    
    # Male cat no urination 12+ hours - should trigger ER
    result = check_immediate_er({
        "species": "cat",
        "category": "Urinary & Genital",
        "sex": "male",
        "hours_since_urination": "12+"
    })
    assert result["is_er"] == True, "Male cat 12+ hours no urination should trigger ER"
    print(f"  ✓ Male cat 12+ hours → ER")
    
    # Female cat straining - should NOT trigger ER automatically
    result = check_immediate_er({
        "species": "cat",
        "category": "Urinary & Genital",
        "sex": "female",
        "straining_no_urine": "Yes"
    })
    # Female cats can still strain without immediate ER (less common blockage)
    print(f"  ✓ Female cat straining → {'ER' if result['is_er'] else 'No auto-ER'}")
    
    print("PASSED")


def test_check_immediate_er_bloat():
    """Test check_immediate_er with GDV/bloat symptoms"""
    print("\n" + "=" * 50)
    print("Testing check_immediate_er - GDV/Bloat...")
    print("=" * 50)
    
    # Classic GDV presentation
    result = check_immediate_er({
        "species": "dog",
        "category": "Stomach Upset",
        "abdomen_distended": "Yes",
        "unproductive_retching": "Yes"
    })
    assert result["is_er"] == True, "Distended abdomen + retching should trigger ER"
    assert result["category"] == "Stomach Upset"
    print(f"  ✓ Distended + retching → ER")
    
    # Just distended without retching - should NOT auto-trigger
    result = check_immediate_er({
        "species": "dog",
        "category": "Stomach Upset",
        "abdomen_distended": "Yes",
        "unproductive_retching": "No"
    })
    print(f"  ✓ Distended only → {'ER' if result['is_er'] else 'No auto-ER'}")
    
    print("PASSED")


def test_check_immediate_er_breathing():
    """Test check_immediate_er with breathing emergencies"""
    print("\n" + "=" * 50)
    print("Testing check_immediate_er - Breathing Issues...")
    print("=" * 50)
    
    # Cat open-mouth breathing - ALWAYS emergency
    result = check_immediate_er({
        "species": "cat",
        "category": "Breathing Issues",
        "open_mouth_breathing": "Yes"
    })
    assert result["is_er"] == True, "Cat open-mouth breathing should trigger ER"
    print(f"  ✓ Cat open-mouth breathing → ER")
    
    # Dog open-mouth breathing - may be normal (panting)
    result = check_immediate_er({
        "species": "dog",
        "category": "Breathing Issues",
        "open_mouth_breathing": "Yes"
    })
    print(f"  ✓ Dog open-mouth breathing → {'ER' if result['is_er'] else 'Not auto-ER (panting normal)'}")
    
    print("PASSED")


def test_check_text_for_red_flags():
    """Test text-based red flag detection"""
    print("\n" + "=" * 50)
    print("Testing check_text_for_red_flags...")
    print("=" * 50)
    
    # ER-level symptoms
    result = check_text_for_red_flags("My dog is not breathing and collapsed")
    assert result["severity"] == "ER"
    assert len(result["matched_symptoms"]) > 0
    print(f"  ✓ 'not breathing, collapsed' → ER")
    
    # TODAY-level symptoms
    result = check_text_for_red_flags("My cat is vomiting blood")
    assert result["severity"] in ["ER", "TODAY"]
    print(f"  ✓ 'vomiting blood' → {result['severity']}")
    
    # SOON-level symptoms
    result = check_text_for_red_flags("My dog has been vomiting and has diarrhea")
    assert result["severity"] in ["ER", "TODAY", "SOON"]
    print(f"  ✓ 'vomiting, diarrhea' → {result['severity']}")
    
    # MONITOR level (low severity)
    result = check_text_for_red_flags("My cat seems a little tired today")
    assert result["severity"] == "MONITOR"
    print(f"  ✓ 'a little tired' → MONITOR")
    
    print("PASSED")


def test_check_text_for_red_flags_breed_specific():
    """Test breed-specific alerts in text detection"""
    print("\n" + "=" * 50)
    print("Testing check_text_for_red_flags - Breed Specific...")
    print("=" * 50)
    
    # Great Dane with bloat symptoms
    result = check_text_for_red_flags(
        text="My dog's stomach looks bloated and he's trying to vomit",
        species="dog",
        breed="Great Dane"
    )
    assert result["severity"] == "ER"
    assert len(result.get("breed_alerts", [])) > 0
    print(f"  ✓ Great Dane + bloat symptoms → ER with breed alert")
    
    # Pug with breathing issues
    result = check_text_for_red_flags(
        text="My dog is panting heavily",
        species="dog",
        breed="Pug"
    )
    assert len(result.get("breed_alerts", [])) > 0
    print(f"  ✓ Pug + breathing → Breed alert added")
    
    print("PASSED")


def test_check_red_flags_combined():
    """Test combined red flags check"""
    print("\n" + "=" * 50)
    print("Testing check_red_flags (combined)...")
    print("=" * 50)
    
    # Test with structured fields
    result = check_red_flags(
        structured_fields={
            "species": "cat",
            "category": "Urinary & Genital",
            "sex": "male",
            "straining_no_urine": "Yes"
        },
        user_text="My cat can't pee"
    )
    assert result["is_er"] == True or result.get("severity") == "ER"
    print(f"  ✓ Structured + text → is_er={result.get('is_er', result.get('severity'))}")
    
    # Test with text only
    result = check_red_flags(
        structured_fields={},
        user_text="My dog ate chocolate and is now having seizures"
    )
    assert result.get("severity") == "ER" or result.get("is_er") == True
    print(f"  ✓ Text only → severity={result.get('severity', 'ER')}")
    
    print("PASSED")


def run_all_tests():
    """Run all red flags tests"""
    test_gum_color_constants()
    test_dangerous_substances()
    test_breed_lists()
    test_keyword_lists()
    test_check_immediate_er_gum_color()
    test_check_immediate_er_male_cat_urinary()
    test_check_immediate_er_bloat()
    test_check_immediate_er_breathing()
    test_check_text_for_red_flags()
    test_check_text_for_red_flags_breed_specific()
    test_check_red_flags_combined()
    
    print("\n" + "=" * 50)
    print("[PASS] ALL SHARED RED FLAGS TESTS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
