# ============================================================================
# Tests for llm_setup.py
# ============================================================================
"""
Unit tests for LLM setup and ER rules engine

Covers all emergency rules based on clinical signs by body system:
- Cross-category: Gum color, CRT, body postures
- Respiratory emergencies
- Urinary emergencies (male cat blockage)
- Neurological emergencies (seizures)
- GI emergencies (GDV/bloat, bloody vomit/diarrhea)
- Cat anorexia (hepatic lipidosis)
- Injury emergencies (wound types/locations)
- Eye emergencies
- Toxin emergencies
- Allergic reaction emergencies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_setup import (
    get_openai_client,
    check_immediate_er_rules,
    get_er_template,
    select_model,
    call_llm
)


def test_api_connection():
    """Test API connection"""
    print("=" * 50)
    print("Testing OpenAI API Connection...")
    print("=" * 50)

    try:
        client = get_openai_client()

        response = call_llm(
            client=client,
            model="gpt-4o-mini",
            system_prompt="You are a friendly assistant.",
            user_message="Say 'API connection successful!'",
            json_mode=False,
            max_tokens=50
        )

        print(f"API Response: {response}")
        print("API connection test passed!")
        return True

    except Exception as e:
        print(f"API connection test failed: {e}")
        return False


# ============================================================================
# Cross-Category ER Rules Tests
# ============================================================================

def test_gum_color_emergencies():
    """Test gum color emergency detection (cross-category)"""
    print("\n" + "=" * 50)
    print("Testing Gum Color Emergencies...")
    print("=" * 50)

    # Test pale/white gums - shock/blood loss
    test_pale = {
        "species": "dog",
        "category": "Injury & Bleeding",
        "gum_color": "pale"
    }
    is_er, category = check_immediate_er_rules(test_pale)
    print(f"\nTest - Pale gums (shock):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Pale gums should trigger ER"
    assert category == "Injury & Bleeding"
    print("  PASSED")

    # Test grey/muddy gums - poor perfusion
    test_grey = {
        "species": "dog",
        "category": "Something Else",
        "gum_color": "grey"
    }
    is_er, category = check_immediate_er_rules(test_grey)
    print(f"\nTest - Grey gums (poor perfusion):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Grey gums should trigger ER"
    assert category == "Concerning Behaviour Changes"
    print("  PASSED")

    # Test brick red gums - sepsis/heat stroke
    test_brick_red = {
        "species": "dog",
        "category": "Something Else",
        "gum_color": "brick red"
    }
    is_er, category = check_immediate_er_rules(test_brick_red)
    print(f"\nTest - Brick red gums (sepsis/heat stroke):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Brick red gums should trigger ER"
    print("  PASSED")

    # Test normal pink gums - no ER
    test_pink = {
        "species": "dog",
        "category": "Something Else",
        "gum_color": "pink"
    }
    is_er, category = check_immediate_er_rules(test_pink)
    print(f"\nTest - Pink gums (normal):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Pink gums should not trigger ER"
    print("  PASSED")

    print("\nAll gum color tests passed!")


def test_capillary_refill_time():
    """Test CRT emergency detection"""
    print("\n" + "=" * 50)
    print("Testing Capillary Refill Time...")
    print("=" * 50)

    test_prolonged_crt = {
        "species": "dog",
        "category": "Something Else",
        "capillary_refill_time": ">2.5 sec"
    }
    is_er, category = check_immediate_er_rules(test_prolonged_crt)
    print(f"\nTest - Prolonged CRT (>2.5 sec):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Prolonged CRT should trigger ER"
    print("  PASSED")

    test_absent_crt = {
        "species": "cat",
        "category": "Something Else",
        "capillary_refill_time": "absent"
    }
    is_er, category = check_immediate_er_rules(test_absent_crt)
    print(f"\nTest - Absent CRT:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Absent CRT should trigger ER"
    print("  PASSED")

    print("\nAll CRT tests passed!")


def test_body_posture_emergencies():
    """Test distress body posture detection"""
    print("\n" + "=" * 50)
    print("Testing Body Posture Emergencies...")
    print("=" * 50)

    # Orthopnea posture - respiratory distress
    test_orthopnea = {
        "species": "dog",
        "category": "Breathing Issues",
        "orthopnea_posture": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_orthopnea)
    print(f"\nTest - Orthopnea posture:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Orthopnea should trigger ER"
    assert category == "Breathing Issues"
    print("  PASSED")

    # Praying position - severe abdominal pain
    test_praying = {
        "species": "dog",
        "category": "Stomach Upset",
        "praying_position": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_praying)
    print(f"\nTest - Praying position (abdominal pain):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Praying position should trigger ER"
    assert category == "Stomach Upset"
    print("  PASSED")

    print("\nAll body posture tests passed!")


# ============================================================================
# Respiratory Emergency Tests
# ============================================================================

def test_respiratory_emergencies():
    """Test respiratory emergency rules"""
    print("\n" + "=" * 50)
    print("Testing Respiratory Emergencies...")
    print("=" * 50)

    # Cat open-mouth breathing - ALWAYS emergency
    test_cat_panting = {
        "species": "cat",
        "category": "Breathing Issues",
        "open_mouth_breathing": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_cat_panting)
    print(f"\nTest - Cat open-mouth breathing:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Cat open-mouth breathing should trigger ER"
    print("  PASSED")

    # Dog panting (context matters - not always ER)
    test_dog_panting = {
        "species": "dog",
        "category": "Breathing Issues",
        "open_mouth_breathing": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_dog_panting)
    print(f"\nTest - Dog panting (alone):")
    print(f"  Result: is_er={is_er}, category={category}")
    # Dogs can pant normally, so this alone shouldn't trigger ER
    print("  PASSED (dogs can pant normally)")

    # Paradoxical breathing
    test_paradoxical = {
        "species": "dog",
        "category": "Breathing Issues",
        "paradoxical_breathing": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_paradoxical)
    print(f"\nTest - Paradoxical breathing:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Paradoxical breathing should trigger ER"
    print("  PASSED")

    # Stridor
    test_stridor = {
        "species": "dog",
        "category": "Breathing Issues",
        "stridor": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_stridor)
    print(f"\nTest - Inspiratory stridor:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Stridor should trigger ER"
    print("  PASSED")

    # Blue/purple gums (cyanosis)
    test_cyanosis = {
        "species": "dog",
        "category": "Breathing Issues",
        "gum_color": "blue-purple"
    }
    is_er, category = check_immediate_er_rules(test_cyanosis)
    print(f"\nTest - Blue/purple gums (cyanosis):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Cyanosis should trigger ER"
    print("  PASSED")

    print("\nAll respiratory emergency tests passed!")


# ============================================================================
# Urinary Emergency Tests
# ============================================================================

def test_urinary_emergencies():
    """Test urinary emergency rules"""
    print("\n" + "=" * 50)
    print("Testing Urinary Emergencies...")
    print("=" * 50)

    # Male cat urinary blockage - straining
    test_male_cat_straining = {
        "species": "cat",
        "category": "Urinary & Genital",
        "sex": "male",
        "straining_no_urine": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_male_cat_straining)
    print(f"\nTest - Male cat straining (no urine):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Male cat straining should trigger ER"
    print("  PASSED")

    # Male cat - 12+ hours no urination
    test_male_cat_12hrs = {
        "species": "cat",
        "category": "Urinary & Genital",
        "sex": "male",
        "hours_since_urination": "12+"
    }
    is_er, category = check_immediate_er_rules(test_male_cat_12hrs)
    print(f"\nTest - Male cat 12+ hours no urination:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Male cat 12+ hours should trigger ER"
    print("  PASSED")

    # Male cat - crying while urinating
    test_crying = {
        "species": "cat",
        "category": "Urinary & Genital",
        "sex": "male",
        "crying_while_urinating": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_crying)
    print(f"\nTest - Male cat crying while urinating:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Crying while urinating should trigger ER"
    print("  PASSED")

    # Female cat straining - NOT emergency (blockage rare in females)
    test_female_cat = {
        "species": "cat",
        "category": "Urinary & Genital",
        "sex": "female",
        "straining_no_urine": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_female_cat)
    print(f"\nTest - Female cat straining:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Female cat straining alone should not trigger ER"
    print("  PASSED")

    # Late signs - vomiting with urinary issues (any species)
    test_vomiting_urinary = {
        "species": "dog",
        "category": "Urinary & Genital",
        "vomiting_with_urinary_issues": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_vomiting_urinary)
    print(f"\nTest - Vomiting with urinary issues:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Vomiting with urinary issues should trigger ER"
    print("  PASSED")

    print("\nAll urinary emergency tests passed!")


# ============================================================================
# Seizure/Neurological Emergency Tests
# ============================================================================

def test_seizure_emergencies():
    """Test seizure/neurological emergency rules"""
    print("\n" + "=" * 50)
    print("Testing Seizure Emergencies...")
    print("=" * 50)

    # Seizure > 5 minutes (status epilepticus)
    test_long_seizure = {
        "species": "dog",
        "category": "Concerning Behaviour Changes",
        "seizure_duration": ">5 min"
    }
    is_er, category = check_immediate_er_rules(test_long_seizure)
    print(f"\nTest - Seizure >5 minutes:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Seizure >5 min should trigger ER"
    print("  PASSED")

    # 2+ seizures within 5 minutes without recovery
    test_cluster_5min = {
        "species": "dog",
        "category": "Concerning Behaviour Changes",
        "seizures_within_5min": "2+"
    }
    is_er, category = check_immediate_er_rules(test_cluster_5min)
    print(f"\nTest - 2+ seizures within 5 min:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "2+ seizures in 5 min should trigger ER"
    print("  PASSED")

    # 3+ seizures in 24 hours (cluster seizures)
    test_cluster_24h = {
        "species": "dog",
        "category": "Concerning Behaviour Changes",
        "seizure_count": "3+ in 24 hours"
    }
    is_er, category = check_immediate_er_rules(test_cluster_24h)
    print(f"\nTest - 3+ seizures in 24 hours:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "3+ seizures in 24h should trigger ER"
    print("  PASSED")

    # Collapse/unresponsive
    test_collapse = {
        "species": "cat",
        "category": "Concerning Behaviour Changes",
        "collapse": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_collapse)
    print(f"\nTest - Collapse:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Collapse should trigger ER"
    print("  PASSED")

    # First seizure (not ER, but same-day urgent) - should NOT trigger
    test_first_seizure = {
        "species": "dog",
        "category": "Concerning Behaviour Changes",
        "seizure_duration": "<3 min",
        "first_seizure": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_first_seizure)
    print(f"\nTest - First seizure <3 min:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Short first seizure should not trigger ER"
    print("  PASSED")

    print("\nAll seizure emergency tests passed!")


# ============================================================================
# GI Emergency Tests
# ============================================================================

def test_gi_emergencies():
    """Test GI emergency rules (GDV/bloat, bloody vomit/diarrhea)"""
    print("\n" + "=" * 50)
    print("Testing GI Emergencies...")
    print("=" * 50)

    # GDV classic presentation: distended + unproductive retching
    test_gdv = {
        "species": "dog",
        "category": "Stomach Upset",
        "abdomen_distended": "Yes",
        "unproductive_retching": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_gdv)
    print(f"\nTest - GDV (distended + retching):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "GDV symptoms should trigger ER"
    print("  PASSED")

    # Drum-like abdomen
    test_drum = {
        "species": "dog",
        "category": "Stomach Upset",
        "drum_like_abdomen": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_drum)
    print(f"\nTest - Drum-like abdomen:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Drum-like abdomen should trigger ER"
    print("  PASSED")

    # Deep-chested breed with single symptom
    test_deep_chest = {
        "species": "dog",
        "category": "Stomach Upset",
        "deep_chested_breed": "Yes",
        "abdomen_distended": "Yes",
        "unproductive_retching": "No"
    }
    is_er, category = check_immediate_er_rules(test_deep_chest)
    print(f"\nTest - Deep-chested breed with distension:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Deep-chested breed + distension should trigger ER"
    print("  PASSED")

    # Bloody vomit
    test_bloody_vomit = {
        "species": "dog",
        "category": "Stomach Upset",
        "bloody_vomit": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_bloody_vomit)
    print(f"\nTest - Bloody vomit:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Bloody vomit should trigger ER"
    print("  PASSED")

    # Bloody diarrhea
    test_bloody_diarrhea = {
        "species": "dog",
        "category": "Stomach Upset",
        "bloody_diarrhea": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_bloody_diarrhea)
    print(f"\nTest - Bloody diarrhea:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Bloody diarrhea should trigger ER"
    print("  PASSED")

    # Cannot keep water down
    test_dehydration = {
        "species": "cat",
        "category": "Stomach Upset",
        "cannot_keep_water_down": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_dehydration)
    print(f"\nTest - Cannot keep water down:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Cannot keep water down should trigger ER"
    print("  PASSED")

    # Vomiting + lethargy + abdominal pain (obstruction signs)
    test_obstruction = {
        "species": "dog",
        "category": "Stomach Upset",
        "vomiting": "Yes",
        "lethargy": "Yes",
        "abdominal_pain": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_obstruction)
    print(f"\nTest - Vomiting + lethargy + pain:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Obstruction signs should trigger ER"
    print("  PASSED")

    # Normal vomiting (no ER)
    test_normal_vomit = {
        "species": "dog",
        "category": "Stomach Upset",
        "vomiting": "Yes",
        "abdomen_distended": "No"
    }
    is_er, category = check_immediate_er_rules(test_normal_vomit)
    print(f"\nTest - Simple vomiting:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Simple vomiting should not trigger ER"
    print("  PASSED")

    print("\nAll GI emergency tests passed!")


# ============================================================================
# Cat Anorexia Tests (Hepatic Lipidosis)
# ============================================================================

def test_cat_anorexia_emergencies():
    """Test cat anorexia emergency rules (hepatic lipidosis risk)"""
    print("\n" + "=" * 50)
    print("Testing Cat Anorexia Emergencies...")
    print("=" * 50)

    # Cat not eating 3+ days
    test_3days = {
        "species": "cat",
        "category": "Stomach Upset",
        "days_not_eating": "3+"
    }
    is_er, category = check_immediate_er_rules(test_3days)
    print(f"\nTest - Cat not eating 3+ days:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Cat 3+ days not eating should trigger ER"
    print("  PASSED")

    # Cat not eating + jaundice
    test_jaundice = {
        "species": "cat",
        "category": "Something Else",
        "not_eating": "Yes",
        "jaundice": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_jaundice)
    print(f"\nTest - Cat not eating + jaundice:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Cat not eating + jaundice should trigger ER"
    print("  PASSED")

    # Cat not eating + yellow gums
    test_yellow_gums = {
        "species": "cat",
        "category": "Something Else",
        "not_eating": "Yes",
        "yellow_gums": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_yellow_gums)
    print(f"\nTest - Cat not eating + yellow gums:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Cat not eating + yellow gums should trigger ER"
    print("  PASSED")

    # Obese cat not eating 2+ days
    test_obese = {
        "species": "cat",
        "category": "Stomach Upset",
        "obese": "Yes",
        "days_not_eating": "2+"
    }
    is_er, category = check_immediate_er_rules(test_obese)
    print(f"\nTest - Obese cat not eating 2+ days:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Obese cat 2+ days should trigger ER"
    print("  PASSED")

    # Dog not eating 3+ days (dogs tolerate longer)
    test_dog_anorexia = {
        "species": "dog",
        "category": "Stomach Upset",
        "days_not_eating": "3+"
    }
    is_er, category = check_immediate_er_rules(test_dog_anorexia)
    print(f"\nTest - Dog not eating 3+ days:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Dog not eating should not trigger cat-specific ER"
    print("  PASSED")

    print("\nAll cat anorexia tests passed!")


# ============================================================================
# Wound Emergency Tests
# ============================================================================

def test_wound_emergencies():
    """Test wound type and location emergency rules"""
    print("\n" + "=" * 50)
    print("Testing Wound Emergencies...")
    print("=" * 50)

    # Heavy bleeding
    test_heavy_bleeding = {
        "species": "dog",
        "category": "Injury & Bleeding",
        "heavy_bleeding": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_heavy_bleeding)
    print(f"\nTest - Heavy bleeding:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Heavy bleeding should trigger ER"
    print("  PASSED")

    # Deep wound (muscle visible)
    test_deep = {
        "species": "dog",
        "category": "Injury & Bleeding",
        "wound_depth": "deep (muscle visible)"
    }
    is_er, category = check_immediate_er_rules(test_deep)
    print(f"\nTest - Deep wound (muscle visible):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Deep wound should trigger ER"
    print("  PASSED")

    # Chest wound
    test_chest = {
        "species": "dog",
        "category": "Injury & Bleeding",
        "wound_location": "chest"
    }
    is_er, category = check_immediate_er_rules(test_chest)
    print(f"\nTest - Chest wound:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Chest wound should trigger ER"
    print("  PASSED")

    # Abdominal wound
    test_abdomen = {
        "species": "cat",
        "category": "Injury & Bleeding",
        "abdominal_wound": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_abdomen)
    print(f"\nTest - Abdominal wound:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Abdominal wound should trigger ER"
    print("  PASSED")

    # Bite wound
    test_bite = {
        "species": "dog",
        "category": "Injury & Bleeding",
        "bite_wound": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_bite)
    print(f"\nTest - Bite wound:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Bite wound should trigger ER"
    print("  PASSED")

    # Puncture wound
    test_puncture = {
        "species": "cat",
        "category": "Injury & Bleeding",
        "puncture_wound": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_puncture)
    print(f"\nTest - Puncture wound:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Puncture wound should trigger ER"
    print("  PASSED")

    # Degloving injury
    test_degloving = {
        "species": "dog",
        "category": "Injury & Bleeding",
        "degloving_injury": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_degloving)
    print(f"\nTest - Degloving injury:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Degloving should trigger ER"
    print("  PASSED")

    # Minor scratch (no ER)
    test_minor = {
        "species": "dog",
        "category": "Injury & Bleeding",
        "wound_depth": "superficial",
        "heavy_bleeding": "No"
    }
    is_er, category = check_immediate_er_rules(test_minor)
    print(f"\nTest - Minor scratch:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Minor scratch should not trigger ER"
    print("  PASSED")

    print("\nAll wound emergency tests passed!")


# ============================================================================
# Eye Emergency Tests
# ============================================================================

def test_eye_emergencies():
    """Test eye emergency rules"""
    print("\n" + "=" * 50)
    print("Testing Eye Emergencies...")
    print("=" * 50)

    # Eye proptosis (popped out)
    test_proptosis = {
        "species": "dog",
        "category": "Ears, Eyes, and Mouth",
        "eye_popped_out": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_proptosis)
    print(f"\nTest - Eye proptosis:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Eye proptosis should trigger ER"
    print("  PASSED")

    # Sudden eye bulging (glaucoma)
    test_glaucoma = {
        "species": "dog",
        "category": "Ears, Eyes, and Mouth",
        "sudden_eye_bulging": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_glaucoma)
    print(f"\nTest - Sudden eye bulging (glaucoma):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Acute glaucoma should trigger ER"
    print("  PASSED")

    # Lens luxation
    test_lens = {
        "species": "dog",
        "category": "Ears, Eyes, and Mouth",
        "lens_luxation": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_lens)
    print(f"\nTest - Lens luxation:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Lens luxation should trigger ER"
    print("  PASSED")

    # Corneal perforation
    test_corneal = {
        "species": "cat",
        "category": "Ears, Eyes, and Mouth",
        "corneal_perforation": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_corneal)
    print(f"\nTest - Corneal perforation:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Corneal perforation should trigger ER"
    print("  PASSED")

    # Minor eye discharge (no ER)
    test_minor_eye = {
        "species": "dog",
        "category": "Ears, Eyes, and Mouth",
        "eye_discharge": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_minor_eye)
    print(f"\nTest - Minor eye discharge:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Minor discharge should not trigger ER"
    print("  PASSED")

    print("\nAll eye emergency tests passed!")


# ============================================================================
# Toxin Emergency Tests
# ============================================================================

def test_toxin_emergencies():
    """Test toxin/poisoning emergency rules"""
    print("\n" + "=" * 50)
    print("Testing Toxin Emergencies...")
    print("=" * 50)

    # Antifreeze ingestion
    test_antifreeze = {
        "species": "dog",
        "category": "Toxic Ingestion & Poisoning",
        "what_was_eaten": "antifreeze"
    }
    is_er, category = check_immediate_er_rules(test_antifreeze)
    print(f"\nTest - Antifreeze ingestion:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Antifreeze should trigger ER"
    print("  PASSED")

    # Xylitol ingestion
    test_xylitol = {
        "species": "dog",
        "category": "Toxic Ingestion & Poisoning",
        "what_was_eaten": "gum with xylitol"
    }
    is_er, category = check_immediate_er_rules(test_xylitol)
    print(f"\nTest - Xylitol ingestion:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Xylitol should trigger ER"
    print("  PASSED")

    # Lily ingestion (cat)
    test_lily = {
        "species": "cat",
        "category": "Toxic Ingestion & Poisoning",
        "what_was_eaten": "lily flower"
    }
    is_er, category = check_immediate_er_rules(test_lily)
    print(f"\nTest - Lily ingestion (cat):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Lily should trigger ER for cats"
    print("  PASSED")

    # Permethrin exposure (cat)
    test_permethrin = {
        "species": "cat",
        "category": "Toxic Ingestion & Poisoning",
        "permethrin_exposure": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_permethrin)
    print(f"\nTest - Permethrin exposure (cat):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Permethrin should trigger ER for cats"
    print("  PASSED")

    # Caustic substance
    test_caustic = {
        "species": "dog",
        "category": "Toxic Ingestion & Poisoning",
        "caustic_substance": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_caustic)
    print(f"\nTest - Caustic substance:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Caustic substance should trigger ER"
    print("  PASSED")

    # Seizing after ingestion
    test_seizing = {
        "species": "dog",
        "category": "Toxic Ingestion & Poisoning",
        "consciousness": "seizing"
    }
    is_er, category = check_immediate_er_rules(test_seizing)
    print(f"\nTest - Seizing after ingestion:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Seizing should trigger ER"
    print("  PASSED")

    # Ate grass (not toxic)
    test_grass = {
        "species": "dog",
        "category": "Toxic Ingestion & Poisoning",
        "what_was_eaten": "grass"
    }
    is_er, category = check_immediate_er_rules(test_grass)
    print(f"\nTest - Ate grass (not toxic):")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Grass should not trigger ER"
    print("  PASSED")

    print("\nAll toxin emergency tests passed!")


# ============================================================================
# Allergic Reaction Tests
# ============================================================================

def test_allergic_emergencies():
    """Test allergic reaction emergency rules"""
    print("\n" + "=" * 50)
    print("Testing Allergic Reaction Emergencies...")
    print("=" * 50)

    # Facial swelling + breathing changes (anaphylaxis)
    test_anaphylaxis = {
        "species": "dog",
        "category": "Itching & Skin Issues",
        "facial_swelling": "Yes",
        "breathing_changes_with_swelling": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_anaphylaxis)
    print(f"\nTest - Facial swelling + breathing changes:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Anaphylaxis signs should trigger ER"
    print("  PASSED")

    # Throat swelling
    test_throat = {
        "species": "dog",
        "category": "Itching & Skin Issues",
        "throat_swelling": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_throat)
    print(f"\nTest - Throat swelling:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Throat swelling should trigger ER"
    print("  PASSED")

    # Rapid swelling progression
    test_rapid = {
        "species": "cat",
        "category": "Itching & Skin Issues",
        "rapid_swelling": "Yes"
    }
    is_er, category = check_immediate_er_rules(test_rapid)
    print(f"\nTest - Rapid swelling progression:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == True, "Rapid swelling should trigger ER"
    print("  PASSED")

    # Mild itching (no ER)
    test_mild = {
        "species": "dog",
        "category": "Itching & Skin Issues",
        "itching": "Yes",
        "facial_swelling": "No"
    }
    is_er, category = check_immediate_er_rules(test_mild)
    print(f"\nTest - Mild itching:")
    print(f"  Result: is_er={is_er}, category={category}")
    assert is_er == False, "Mild itching should not trigger ER"
    print("  PASSED")

    print("\nAll allergic reaction tests passed!")


# ============================================================================
# Model Selection Tests
# ============================================================================

def test_model_selection():
    """Test model selection logic"""
    print("\n" + "=" * 50)
    print("Testing Model Selection...")
    print("=" * 50)

    # Test intake model
    model = select_model(is_simple_case=True)
    print(f"Simple case model: {model}")
    assert model == "gpt-4o-mini", "Simple case should use gpt-4o-mini"

    # Test triage model
    model = select_model(is_simple_case=False)
    print(f"Normal triage model: {model}")
    assert model == "gpt-4.1-mini", "Normal triage should use gpt-4.1-mini"

    # Test fallback model
    model = select_model(needs_fallback=True)
    print(f"Fallback model: {model}")
    assert model == "gpt-4.1", "Fallback should use gpt-4.1"

    print("All model selection tests passed!")


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all ER rule tests"""
    print("\n" + "=" * 60)
    print("   PET TRIAGE ER RULES - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Cross-Category: Gum Colors", test_gum_color_emergencies),
        ("Cross-Category: CRT", test_capillary_refill_time),
        ("Cross-Category: Body Postures", test_body_posture_emergencies),
        ("Respiratory Emergencies", test_respiratory_emergencies),
        ("Urinary Emergencies", test_urinary_emergencies),
        ("Seizure Emergencies", test_seizure_emergencies),
        ("GI Emergencies", test_gi_emergencies),
        ("Cat Anorexia", test_cat_anorexia_emergencies),
        ("Wound Emergencies", test_wound_emergencies),
        ("Eye Emergencies", test_eye_emergencies),
        ("Toxin Emergencies", test_toxin_emergencies),
        ("Allergic Reactions", test_allergic_emergencies),
        ("Model Selection", test_model_selection),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n FAILED: {name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n ERROR: {name}")
            print(f"   Error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"   TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    # Uncomment to test API connection (requires valid API key)
    # test_api_connection()
    exit(0 if success else 1)
