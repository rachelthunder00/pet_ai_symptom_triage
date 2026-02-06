# ============================================================================
# File 4: task3_input_guardrails.py - Task 3.3 Input Guardrails
# ============================================================================
"""
Task 3.3: Input Guardrails

This file implements the 5-layer input guardrails from the document:
Layer A - Scope Guardrails (MVP boundaries)
Layer B - Structured Field Completeness Check
Layer C - Immediate ER Pre-check (Rule engine first)
Layer D - Input Quality Guardrails (Sanitization and limits)
Layer E - Prompt Injection & Unsafe Request Detection

According to the document:
"We enforce guardrails in a fixed order to ensure safety and efficiency"

NOTE: This file now imports from shared module for consistency.
"""

import re
from typing import Dict, Any, Tuple, Optional, List

# Import from shared module (single source of truth)
from shared.constants import (
    SUPPORTED_SPECIES,
    SUPPORTED_CATEGORIES,
    INPUT_LIMITS,
)
from shared.red_flags import check_immediate_er
from llm_setup import get_er_template


# ============================================================================
# Part 1: Layer A - Scope Guardrails (MVP Boundaries)
# ============================================================================

class ScopeGuardrails:
    """
    Layer A: Scope Guardrails
    
    Check if input is within MVP support scope:
    - Only dogs and cats
    - Only 9 symptom categories
    """
    
    @staticmethod
    def check_species(species: str) -> Tuple[bool, Optional[str]]:
        """
        Check if pet species is supported
        
        Returns: (passed, error_message)
        """
        if not species:
            return False, "Please select your pet type (dog or cat)"
        
        species_lower = species.lower().strip()
        
        if species_lower not in ["dog", "cat"]:
            return False, f"Sorry, we currently only support dogs and cats. '{species}' is not supported."
        
        return True, None
    
    @staticmethod
    def check_category(category: str) -> Tuple[bool, Optional[str]]:
        """
        Check if symptom category is supported
        
        Returns: (passed, error_message)
        """
        if not category:
            return False, "Please select a symptom category"
        
        if category not in SUPPORTED_CATEGORIES:
            return False, f"Unsupported category: {category}. Please select from supported categories."
        
        return True, None
    
    @staticmethod
    def check_symptom_input(symptom_text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if symptom input is valid
        
        Returns: (passed, error_message)
        """
        if not symptom_text or not symptom_text.strip():
            return False, "Please describe your pet's symptoms"
        
        # Check if too short/meaningless
        cleaned = symptom_text.strip()
        if len(cleaned) < 5:
            return False, "Please provide more detailed symptom description"
        
        # Check if just a greeting
        greetings = ["hi", "hello", "hey", "help", "help me"]
        if cleaned.lower() in greetings:
            return False, "Please describe your pet's specific symptoms"
        
        return True, None


# ============================================================================
# Part 2: Layer B - Structured Field Completeness Check
# ============================================================================

class StructuredFieldsGuardrails:
    """
    Layer B: Structured Field Completeness Check
    
    Check if minimum required structured fields exist for each category
    """
    
    # Required fields per category
    REQUIRED_FIELDS = {
        "Breathing Issues": {
            "any_of": ["open_mouth_breathing", "gum_color", "respiratory_rate", "breathing_posture"],
            "message": "Please answer at least one breathing-related question"
        },
        "Urinary & Genital": {
            "all_of": ["sex"],
            "any_of": ["straining_no_urine", "hours_since_urination"],
            "message": "Please provide pet's sex and urination status"
        },
        "Concerning Behaviour Changes": {
            "any_of": ["seizure_status", "seizure_duration", "collapse"],
            "message": "Please describe specific behavior changes (seizures, collapse, etc.)"
        },
        "Stomach Upset": {
            "any_of": ["abdomen_distended", "unproductive_retching", "vomiting_frequency", "blood_present"],
            "message": "Please describe the gastrointestinal symptoms"
        },
        "Injury & Bleeding": {
            "any_of": ["heavy_bleeding", "bleeding_stopped_after_pressure", "wound_depth"],
            "message": "Please describe the wound and bleeding status"
        },
        "Ears, Eyes, and Mouth": {
            "any_of": ["eye_popped_out", "sudden_eye_bulging", "eye_discharge", "facial_swelling"],
            "message": "Please describe the eye/ear/mouth symptoms"
        },
        "Toxic Ingestion & Poisoning": {
            "any_of": ["suspected_ingestion", "what_was_eaten", "time_since_ingestion"],
            "message": "Please describe what was eaten and when"
        },
        "Itching & Skin Issues": {
            "any_of": ["facial_swelling", "hives_spreading", "breathing_changes_with_swelling"],
            "message": "Please describe the skin issue details"
        }
    }
    
    @classmethod
    def check_completeness(
        cls, 
        category: str, 
        structured_fields: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check if structured fields are complete
        
        Args:
            category: Symptom category
            structured_fields: User-provided structured fields
            
        Returns:
            (is_complete, error_message, suggested_followup_questions)
        """
        if category not in cls.REQUIRED_FIELDS:
            return True, None, []
        
        requirements = cls.REQUIRED_FIELDS[category]
        
        # Check all_of (must have all)
        if "all_of" in requirements:
            for field in requirements["all_of"]:
                if not structured_fields.get(field):
                    return False, requirements["message"], cls._get_follow_up_questions(category)
        
        # Check any_of (must have at least one)
        if "any_of" in requirements:
            has_any = any(
                structured_fields.get(field) 
                for field in requirements["any_of"]
            )
            if not has_any:
                return False, requirements["message"], cls._get_follow_up_questions(category)
        
        return True, None, []
    
    @classmethod
    def _get_follow_up_questions(cls, category: str) -> List[str]:
        """
        Get follow-up questions for the category (max 2)
        """
        questions = {
            "Breathing Issues": [
                "Is your pet breathing with mouth open right now?",
                "What color are the gums? (pink/pale/blue-purple)"
            ],
            "Urinary & Genital": [
                "When was the last normal urination?",
                "Is there repeated straining with no urine produced?"
            ],
            "Concerning Behaviour Changes": [
                "Is there seizure activity? If so, how long?",
                "Is there collapse or inability to stand?"
            ],
            "Stomach Upset": [
                "Does the abdomen look swollen or distended?",
                "Is there unproductive retching (trying to vomit but nothing comes out)?"
            ],
            "Injury & Bleeding": [
                "Is the bleeding heavy? Does it stop with pressure?",
                "How deep is the wound? Can you see muscle or bone?"
            ],
            "Ears, Eyes, and Mouth": [
                "Is there obvious eye abnormality (bulging, swelling, discharge)?",
                "Is there facial swelling?"
            ],
            "Toxic Ingestion & Poisoning": [
                "What do you know or suspect was eaten?",
                "Approximately how long ago did this happen?"
            ],
            "Itching & Skin Issues": [
                "Is there facial swelling?",
                "Is the rash spreading quickly?"
            ]
        }
        return questions.get(category, [])[:2]


# ============================================================================
# Part 3: Layer C - Immediate ER Pre-check
# ============================================================================

class ERPreCheckGuardrails:
    """
    Layer C: Immediate ER Pre-check
    
    Run deterministic ER red flag check before calling LLM.
    Uses fuzzy matching to catch variations of emergency keywords.
    """
    
    # Exact keyword matching (original list for backward compatibility)
    TEXT_ER_KEYWORDS = {
        "breathing": [
            "open mouth breathing", "can't breathe", "gasping", "blue gums",
            "choking", "struggling to breathe", "labored breathing",
            "breathing with mouth open", "mouth open", "cat panting",
            "panting cat", "cat breathing with mouth"
        ],
        "urinary": [
            "can't urinate", "straining to pee", "no urine", "blocked",
            "keeps going to litter box", "crying in litter box"
        ],
        "seizure": [
            "seizure", "convulsion", "fitting", "shaking uncontrollably"
        ],
        "bloat": [
            "bloat", "stomach twisted", "retching", "belly swollen",
            "trying to vomit nothing comes out"
        ],
        "bleeding": [
            "heavy bleeding", "won't stop bleeding", "gushing blood"
        ],
        "poisoning": [
            "ate chocolate", "ate grapes", "poisoning", "ate rat poison",
            "ate lilies", "ate xylitol", "ate antifreeze"
        ],
        "collapse": [
            "collapsed", "can't stand", "unresponsive", "unconscious"
        ]
    }
    
    # Fuzzy matching patterns: (core_words_required, description)
    # If ALL core words appear anywhere in text, it's a match
    FUZZY_PATTERNS = {
        "breathing": [
            # Cat open-mouth breathing variations (CATS SHOULD NEVER PANT)
            (["cat", "mouth", "open"], "Cat with mouth open"),
            (["cat", "panting"], "Cat panting"),
            (["cat", "breathing", "mouth"], "Cat breathing through mouth"),
            (["cat", "heavy", "breathing"], "Cat heavy breathing"),
            (["cat", "labored", "breathing"], "Cat labored breathing"),
            (["cat", "breathing", "hard"], "Cat breathing hard"),
            (["cat", "breathing", "fast"], "Cat breathing fast"),
            (["cat", "rapid", "breathing"], "Cat rapid breathing"),
            (["cat", "struggling", "breathe"], "Cat struggling to breathe"),
            (["cat", "trouble", "breathing"], "Cat trouble breathing"),
            (["cat", "difficulty", "breathing"], "Cat difficulty breathing"),
            (["cat", "gasping"], "Cat gasping"),
            (["cat", "wheezing"], "Cat wheezing severely"),
            (["kitten", "mouth", "open"], "Kitten with mouth open"),
            (["kitten", "panting"], "Kitten panting"),
            (["kitten", "breathing", "hard"], "Kitten breathing hard"),
            # General breathing emergencies
            (["cannot", "breathe"], "Cannot breathe"),
            (["cant", "breathe"], "Can't breathe"),
            (["can't", "breathe"], "Can't breathe"),
            (["unable", "breathe"], "Unable to breathe"),
            (["not", "breathing"], "Not breathing"),
            (["stopped", "breathing"], "Stopped breathing"),
            (["struggling", "breathe"], "Struggling to breathe"),
            (["difficulty", "breathing"], "Difficulty breathing"),
            (["hard", "time", "breathing"], "Hard time breathing"),
            (["trouble", "breathing"], "Trouble breathing"),
            (["gasping", "air"], "Gasping for air"),
            (["choking"], "Choking"),
            (["something", "stuck", "throat"], "Something stuck in throat"),
            # Gum color emergencies
            (["gums", "blue"], "Blue gums"),
            (["gums", "purple"], "Purple gums"),
            (["gums", "pale"], "Pale gums"),
            (["gums", "white"], "White gums"),
            (["gums", "gray"], "Gray gums"),
            (["gums", "grey"], "Grey gums"),
            (["tongue", "blue"], "Blue tongue"),
            (["tongue", "purple"], "Purple tongue"),
            (["lips", "blue"], "Blue lips"),
        ],
        "urinary": [
            # Male cat urinary blockage (LIFE-THREATENING)
            (["cat", "cannot", "pee"], "Cat cannot pee"),
            (["cat", "cant", "pee"], "Cat can't pee"),
            (["cat", "can't", "pee"], "Cat can't pee"),
            (["cat", "unable", "urinate"], "Cat unable to urinate"),
            (["cat", "straining", "urinate"], "Cat straining to urinate"),
            (["cat", "straining", "pee"], "Cat straining to pee"),
            (["cat", "trying", "pee"], "Cat trying to pee but can't"),
            (["cat", "litter", "box", "crying"], "Cat crying in litter box"),
            (["cat", "litter", "nothing"], "Cat in litter box producing nothing"),
            (["male", "cat", "litter"], "Male cat litter box issues"),
            (["male", "cat", "blocked"], "Male cat blocked"),
            (["male", "cat", "straining"], "Male cat straining"),
            # General urinary emergencies
            (["blocked", "urinary"], "Urinary blockage"),
            (["urinary", "blockage"], "Urinary blockage"),
            (["cannot", "urinate"], "Cannot urinate"),
            (["cant", "urinate"], "Can't urinate"),
            (["can't", "urinate"], "Can't urinate"),
            (["no", "urine"], "No urine production"),
            (["hasnt", "peed"], "Hasn't peed"),
            (["hasn't", "peed"], "Hasn't peed"),
            (["not", "urinating"], "Not urinating"),
            (["straining", "litter"], "Straining in litter box"),
            (["crying", "pee"], "Crying when trying to pee"),
            (["painful", "urination"], "Painful urination"),
        ],
        "seizure": [
            # Active seizure
            (["having", "seizure"], "Having seizure"),
            (["seizure", "now"], "Seizure happening now"),
            (["seizuring"], "Seizuring"),
            (["convulsing"], "Convulsing"),
            (["convulsion"], "Convulsion"),
            (["fitting"], "Fitting"),
            (["shaking", "uncontrollably"], "Shaking uncontrollably"),
            (["violent", "shaking"], "Violent shaking"),
            (["whole", "body", "shaking"], "Whole body shaking"),
            (["twitching", "uncontrollably"], "Twitching uncontrollably"),
            (["falling", "over", "shaking"], "Falling over and shaking"),
            (["jerking", "movements"], "Jerking movements"),
            (["stiff", "shaking"], "Stiff and shaking"),
            (["foaming", "mouth"], "Foaming at mouth"),
            (["paddling", "legs"], "Paddling legs"),
            (["multiple", "seizures"], "Multiple seizures"),
            (["cluster", "seizures"], "Cluster seizures"),
            (["seizure", "wont", "stop"], "Seizure won't stop"),
            (["seizure", "won't", "stop"], "Seizure won't stop"),
        ],
        "bloat": [
            # GDV/Bloat (LIFE-THREATENING especially in large dogs)
            (["stomach", "swollen"], "Swollen stomach"),
            (["stomach", "bloated"], "Bloated stomach"),
            (["stomach", "distended"], "Distended stomach"),
            (["belly", "swollen"], "Swollen belly"),
            (["belly", "hard"], "Hard belly"),
            (["belly", "tight"], "Tight belly"),
            (["abdomen", "distended"], "Distended abdomen"),
            (["abdomen", "swollen"], "Swollen abdomen"),
            (["trying", "vomit", "nothing"], "Trying to vomit nothing"),
            (["trying", "throw", "up", "nothing"], "Trying to throw up nothing"),
            (["dry", "heaving"], "Dry heaving"),
            (["retching", "nothing"], "Retching nothing"),
            (["retching", "producing", "nothing"], "Retching producing nothing"),
            (["unproductive", "vomiting"], "Unproductive vomiting"),
            (["heaving", "nothing", "coming"], "Heaving but nothing coming"),
            (["restless", "stomach"], "Restless with stomach issues"),
            (["pacing", "restless"], "Pacing and restless"),
            (["wont", "lie", "down"], "Won't lie down"),
            (["won't", "lie", "down"], "Won't lie down"),
            (["stomach", "twisted"], "Stomach twisted"),
            (["drooling", "excessively"], "Drooling excessively"),
        ],
        "bleeding": [
            # Severe bleeding
            (["bleeding", "stop"], "Bleeding won't stop"),
            (["bleeding", "wont", "stop"], "Bleeding won't stop"),
            (["bleeding", "won't", "stop"], "Bleeding won't stop"),
            (["blood", "everywhere"], "Blood everywhere"),
            (["severe", "bleeding"], "Severe bleeding"),
            (["heavy", "bleeding"], "Heavy bleeding"),
            (["heavy", "blood"], "Heavy blood loss"),
            (["bleeding", "lot"], "Bleeding a lot"),
            (["bleeding", "heavily"], "Bleeding heavily"),
            (["blood", "gushing"], "Blood gushing"),
            (["blood", "pouring"], "Blood pouring"),
            (["blood", "spurting"], "Blood spurting"),
            (["arterial", "bleeding"], "Arterial bleeding"),
            (["deep", "wound"], "Deep wound"),
            (["deep", "cut"], "Deep cut"),
            (["hit", "by", "car"], "Hit by car"),
            (["trauma"], "Trauma"),
            (["attacked", "by"], "Attacked by animal"),
            (["bite", "wound"], "Bite wound"),
            (["puncture", "wound"], "Puncture wound"),
        ],
        "poisoning": [
            # Toxic ingestion
            (["ate", "chocolate"], "Ate chocolate"),
            (["eaten", "chocolate"], "Eaten chocolate"),
            (["ate", "poison"], "Ate poison"),
            (["ate", "toxic"], "Ate toxic substance"),
            (["swallowed", "poison"], "Swallowed poison"),
            (["ingested", "toxic"], "Ingested toxic substance"),
            (["ate", "lily"], "Ate lily"),
            (["ate", "lilies"], "Ate lilies"),
            (["ate", "grape"], "Ate grapes"),
            (["ate", "grapes"], "Ate grapes"),
            (["ate", "raisin"], "Ate raisins"),
            (["ate", "raisins"], "Ate raisins"),
            (["ate", "onion"], "Ate onion"),
            (["ate", "garlic"], "Ate garlic"),
            (["ate", "xylitol"], "Ate xylitol"),
            (["ate", "medication"], "Ate medication"),
            (["ate", "pills"], "Ate pills"),
            (["ate", "medicine"], "Ate medicine"),
            (["ate", "rat", "poison"], "Ate rat poison"),
            (["ate", "rodenticide"], "Ate rodenticide"),
            (["ate", "antifreeze"], "Ate antifreeze"),
            (["drank", "antifreeze"], "Drank antifreeze"),
            (["ate", "cleaning"], "Ate cleaning product"),
            (["drank", "cleaning"], "Drank cleaning product"),
            (["ate", "bleach"], "Ate bleach"),
            (["drank", "bleach"], "Drank bleach"),
            (["got", "into", "poison"], "Got into poison"),
            (["got", "into", "medication"], "Got into medication"),
            (["got", "into", "pills"], "Got into pills"),
            (["poisoning"], "Poisoning suspected"),
            (["think", "poisoned"], "Think pet is poisoned"),
        ],
        "collapse": [
            # Collapse/unconscious
            (["collapsed"], "Collapsed"),
            (["collapse"], "Collapse"),
            (["fell", "over"], "Fell over"),
            (["fell", "down"], "Fell down"),
            (["cannot", "stand"], "Cannot stand"),
            (["cant", "stand"], "Can't stand"),
            (["can't", "stand"], "Can't stand"),
            (["unable", "stand"], "Unable to stand"),
            (["wont", "stand"], "Won't stand"),
            (["won't", "stand"], "Won't stand"),
            (["cannot", "walk"], "Cannot walk"),
            (["cant", "walk"], "Can't walk"),
            (["can't", "walk"], "Can't walk"),
            (["legs", "not", "working"], "Legs not working"),
            (["legs", "gave", "out"], "Legs gave out"),
            (["not", "responding"], "Not responding"),
            (["unresponsive"], "Unresponsive"),
            (["unconscious"], "Unconscious"),
            (["passed", "out"], "Passed out"),
            (["fainted"], "Fainted"),
            (["not", "moving"], "Not moving"),
            (["limp"], "Limp"),
            (["lifeless"], "Lifeless"),
            (["not", "waking", "up"], "Not waking up"),
            (["wont", "wake", "up"], "Won't wake up"),
            (["won't", "wake", "up"], "Won't wake up"),
            (["extremely", "weak"], "Extremely weak"),
            (["sudden", "weakness"], "Sudden weakness"),
            (["paralyzed"], "Paralyzed"),
            (["paralysed"], "Paralysed"),
            (["cannot", "move"], "Cannot move"),
            (["cant", "move"], "Can't move"),
            (["can't", "move"], "Can't move"),
        ],
        "eye": [
            # Eye emergencies
            (["eye", "popping", "out"], "Eye popping out"),
            (["eye", "bulging"], "Eye bulging"),
            (["eye", "swollen", "shut"], "Eye swollen shut"),
            (["eye", "bleeding"], "Eye bleeding"),
            (["something", "in", "eye"], "Something in eye"),
            (["chemical", "in", "eye"], "Chemical in eye"),
            (["eye", "injury"], "Eye injury"),
            (["eye", "punctured"], "Eye punctured"),
            (["scratched", "eye"], "Scratched eye"),
            (["sudden", "blindness"], "Sudden blindness"),
            (["cannot", "see"], "Cannot see"),
            (["cant", "see"], "Can't see"),
            (["can't", "see"], "Can't see"),
        ],
        "heatstroke": [
            # Heat stroke
            (["heat", "stroke"], "Heat stroke"),
            (["heatstroke"], "Heatstroke"),
            (["overheated"], "Overheated"),
            (["overheating"], "Overheating"),
            (["left", "in", "car"], "Left in car"),
            (["hot", "car"], "Hot car"),
            (["excessive", "panting"], "Excessive panting"),
            (["bright", "red", "tongue"], "Bright red tongue"),
            (["drooling", "hot"], "Drooling when hot"),
            (["collapse", "hot"], "Collapsed from heat"),
        ],
        "allergic": [
            # Severe allergic reaction
            (["face", "swelling"], "Face swelling"),
            (["face", "swollen"], "Face swollen"),
            (["throat", "swelling"], "Throat swelling"),
            (["throat", "swollen"], "Throat swollen"),
            (["tongue", "swelling"], "Tongue swelling"),
            (["tongue", "swollen"], "Tongue swollen"),
            (["allergic", "reaction"], "Allergic reaction"),
            (["anaphylaxis"], "Anaphylaxis"),
            (["anaphylactic"], "Anaphylactic reaction"),
            (["bee", "sting", "swelling"], "Bee sting with swelling"),
            (["wasp", "sting", "swelling"], "Wasp sting with swelling"),
            (["hives", "spreading"], "Hives spreading rapidly"),
            (["swelling", "rapidly"], "Swelling rapidly"),
        ],
        "birth": [
            # Birthing emergencies
            (["labor", "hours"], "In labor for hours"),
            (["giving", "birth", "stuck"], "Giving birth, stuck"),
            (["puppy", "stuck"], "Puppy stuck"),
            (["kitten", "stuck"], "Kitten stuck"),
            (["cannot", "deliver"], "Cannot deliver"),
            (["cant", "deliver"], "Can't deliver"),
            (["can't", "deliver"], "Can't deliver"),
            (["straining", "birth"], "Straining to give birth"),
            (["green", "discharge"], "Green discharge during labor"),
            (["bleeding", "labor"], "Bleeding during labor"),
        ]
    }
    
    @classmethod
    def _fuzzy_match(cls, text_lower: str, core_words: list) -> bool:
        """
        Check if ALL core words appear in the text (order doesn't matter).
        This allows matching variations like:
        - "my cat keeps his mouth open" matches ["cat", "mouth", "open"]
        - "cat is breathing with his mouth open" matches ["cat", "mouth", "open"]
        """
        return all(word in text_lower for word in core_words)
    
    @classmethod
    def check_text_for_er(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect ER keywords from text using both exact and fuzzy matching.
        
        Returns: (is_er_detected, detected_category)
        """
        if not text:
            return False, None
        
        text_lower = text.lower()
        
        keyword_to_category = {
            "breathing": "Breathing Issues",
            "urinary": "Urinary & Genital",
            "seizure": "Concerning Behaviour Changes",
            "bloat": "Stomach Upset",
            "bleeding": "Injury & Bleeding",
            "poisoning": "Toxic Ingestion & Poisoning",
            "collapse": "Concerning Behaviour Changes",
            "eye": "Ears, Eyes, and Mouth",
            "heatstroke": "Concerning Behaviour Changes",
            "allergic": "Itching & Skin Issues",
            "birth": "Urinary & Genital"
        }
        
        # Method 1: Exact keyword matching (fast, original behavior)
        for key, keywords in cls.TEXT_ER_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return True, keyword_to_category.get(key, "Something Else")
        
        # Method 2: Fuzzy pattern matching (catches more variations)
        for key, patterns in cls.FUZZY_PATTERNS.items():
            for core_words, description in patterns:
                if cls._fuzzy_match(text_lower, core_words):
                    return True, keyword_to_category.get(key, "Something Else")
        
        return False, None
    
    @classmethod
    def run_er_precheck(
        cls, 
        structured_fields: Dict[str, Any], 
        user_text: str = ""
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Run complete ER pre-check
        
        Args:
            structured_fields: Structured fields
            user_text: User free text description
            
        Returns:
            (is_er_triggered, er_template_response)
        """
        # First check structured fields (more reliable)
        # Use shared module's check_immediate_er function (returns dict)
        er_result = check_immediate_er(structured_fields)
        
        if er_result["is_er"]:
            return True, get_er_template(er_result["category"])
        
        # If structured fields didn't trigger, check text keywords (fallback)
        is_text_er, text_category = cls.check_text_for_er(user_text)
        
        if is_text_er:
            return True, get_er_template(text_category)
        
        return False, None


# ============================================================================
# Part 4: Layer D - Input Quality Guardrails
# ============================================================================

class InputQualityGuardrails:
    """
    Layer D: Input Quality Guardrails
    
    Clean and validate input data
    """
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text input
        """
        if not text:
            return ""
        
        # Trim whitespace
        text = text.strip()
        
        # Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        return text
    
    @staticmethod
    def check_text_length(text: str, max_length: int = None) -> Tuple[bool, str]:
        """
        Check text length and truncate if needed
        
        Returns: (is_within_limit, processed_text)
        """
        if max_length is None:
            max_length = INPUT_LIMITS["max_text_length"]
        
        if len(text) <= max_length:
            return True, text
        
        # Truncate
        truncated = text[:max_length]
        # Try to cut at sentence boundary
        last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        
        if last_period > max_length * 0.7:
            truncated = truncated[:last_period + 1]
        
        return False, truncated
    
    @staticmethod
    def validate_image(
        file_size_bytes: int, 
        content_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate image file
        
        Returns: (is_valid, error_message)
        """
        # Check file type
        if content_type.lower() not in INPUT_LIMITS["allowed_image_types"]:
            return False, "Only JPG and PNG image formats are supported"
        
        # Check file size
        max_size = INPUT_LIMITS["max_image_size_mb"] * 1024 * 1024
        if file_size_bytes > max_size:
            return False, f"Image too large. Please upload an image smaller than {INPUT_LIMITS['max_image_size_mb']}MB"
        
        return True, None


# ============================================================================
# Part 5: Layer E - Prompt Injection & Unsafe Request Detection
# ============================================================================

class SafetyGuardrails:
    """
    Layer E: Prompt Injection & Unsafe Request Detection
    
    According to the document:
    "We do not block users from getting help, but we ignore instruction-like text 
     and enforce triage-only behavior."
    """
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r'ignore.*(previous|above|all|prior).*(instructions?|rules?|prompts?)',
        r'forget.*(your|all).*(instructions?|rules?)',
        r'pretend you are',
        r'act as if',
        r'reveal.*(system|hidden).*(prompt|instructions?)',
        r'disregard.*instructions',
        r'override.*rules',
    ]
    
    # Unsafe request patterns
    UNSAFE_REQUEST_PATTERNS = [
        r'give.*(dosage|dose)',
        r'how much.*medication',
        r'prescribe',
        r'definitive diagnosis',
        r'guarantee',
        r'100%.*safe',
        r'what disease does.*have',
    ]
    
    @classmethod
    def detect_injection(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect prompt injection attempts
        
        Returns: (is_injection_detected, detected_pattern)
        """
        if not text:
            return False, None
        
        text_lower = text.lower()
        
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, pattern
        
        return False, None
    
    @classmethod
    def detect_unsafe_request(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect unsafe requests (e.g., medication dosing)
        
        Returns: (is_detected, detected_pattern)
        """
        if not text:
            return False, None
        
        text_lower = text.lower()
        
        for pattern in cls.UNSAFE_REQUEST_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, pattern
        
        return False, None
    
    @classmethod
    def sanitize_for_safety(cls, text: str) -> str:
        """
        Sanitize text to remove potentially unsafe content
        """
        if not text:
            return ""
        
        # Remove obvious injection attempts
        for pattern in cls.INJECTION_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()


# ============================================================================
# Part 5.5: Layer F - Off-Topic Detection Guardrails
# ============================================================================

class OffTopicGuardrails:
    """
    Layer F: Off-Topic Detection Guardrails

    Two-stage detection:
    1. Fast keyword-based filtering (no API call)
    2. LLM-based classification as fallback (when uncertain)

    This ensures users can only ask about pet health topics for dogs and cats.
    """

    # Pet-related keywords (if present, likely on-topic)
    PET_KEYWORDS = [
        # Animals
        "dog", "cat", "puppy", "kitten", "pet", "pup", "kitty", "canine", "feline",
        # Body parts
        "paw", "fur", "tail", "ear", "eye", "nose", "mouth", "gum", "teeth", "leg",
        "belly", "stomach", "skin", "coat", "nail", "claw",
        # Symptoms & health
        "vomit", "diarrhea", "itch", "scratch", "limp", "cough", "sneeze", "wheeze",
        "bleed", "wound", "lump", "bump", "swelling", "rash", "discharge",
        "lethargy", "appetite", "thirst", "urinate", "pee", "poop", "stool",
        "breathing", "panting", "shaking", "seizure", "fever",
        # Actions
        "eating", "drinking", "walking", "running", "playing", "sleeping",
        # Medical
        "vet", "veterinarian", "vaccine", "medication", "treatment", "symptom",
        "sick", "ill", "healthy", "pain", "hurt", "injured",
    ]

    # Clearly off-topic keywords (if present AND no pet keywords, likely off-topic)
    OFF_TOPIC_KEYWORDS = [
        # Weather
        "weather", "rain", "sunny", "cloud", "temperature", "forecast",
        # Food/Cooking (human)
        "recipe", "cook", "bake", "ingredient", "restaurant", "menu",
        # Math/Science
        "calculate", "equation", "formula", "solve", "math", "algebra",
        # Programming
        "code", "program", "python", "javascript", "function", "debug", "api",
        # Travel
        "flight", "hotel", "travel", "vacation", "tourist", "booking",
        # General knowledge
        "history", "politics", "president", "election", "country", "capital",
        # Entertainment
        "movie", "music", "game", "sport", "football", "basketball",
        # Shopping
        "buy", "price", "discount", "amazon", "shopping",
        # Finance
        "stock", "bitcoin", "crypto", "investment", "bank",
    ]

    # Response message for off-topic requests
    OFF_TOPIC_RESPONSE = (
        "I'm a pet health assistant specialized in dogs and cats. "
        "I can only help with pet health-related questions. "
        "Please describe your dog's or cat's symptoms or health concerns."
    )

    @classmethod
    def _contains_pet_keywords(cls, text: str) -> bool:
        """Check if text contains pet-related keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.PET_KEYWORDS)

    @classmethod
    def _contains_offtopic_keywords(cls, text: str) -> bool:
        """Check if text contains off-topic keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.OFF_TOPIC_KEYWORDS)

    @classmethod
    def keyword_check(cls, text: str) -> Tuple[str, Optional[str]]:
        """
        Fast keyword-based topic detection.

        Returns:
            (status, reason)
            - status: "on_topic" | "off_topic" | "uncertain"
            - reason: explanation for the decision
        """
        if not text or len(text.strip()) < 3:
            return "uncertain", "Text too short to determine"

        has_pet_keywords = cls._contains_pet_keywords(text)
        has_offtopic_keywords = cls._contains_offtopic_keywords(text)

        # Case 1: Has pet keywords → likely on-topic
        if has_pet_keywords and not has_offtopic_keywords:
            return "on_topic", "Contains pet health keywords"

        # Case 2: Has off-topic keywords but no pet keywords → likely off-topic
        if has_offtopic_keywords and not has_pet_keywords:
            return "off_topic", "Contains off-topic keywords without pet context"

        # Case 3: Has both or neither → uncertain, need LLM
        if has_pet_keywords and has_offtopic_keywords:
            return "uncertain", "Contains both pet and off-topic keywords"

        # Case 4: No keywords detected → uncertain
        return "uncertain", "No clear keywords detected"

    @classmethod
    def llm_check(cls, text: str) -> Tuple[bool, str]:
        """
        LLM-based topic classification (fallback for uncertain cases).

        Uses a fast model (gpt-4o-mini) to determine if the text is about pet health.

        Returns:
            (is_on_topic, reason)
        """
        try:
            from openai import OpenAI
            import os

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            prompt = f"""You are a classifier that determines if a user's message is about pet health for dogs or cats.

User message: "{text}"

Is this message about dog or cat health/symptoms/care?
Reply with ONLY one word: "YES" or "NO"

Guidelines:
- YES: Questions about dog/cat symptoms, health, behavior, care, feeding, grooming
- NO: Questions about other animals, weather, cooking, math, coding, travel, general knowledge, etc.
- NO: Greetings without health context (just "hello", "hi")
- YES: Even vague pet concerns like "my dog seems off" or "is this normal for cats"
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )

            answer = response.choices[0].message.content.strip().upper()
            is_on_topic = answer.startswith("YES")

            return is_on_topic, f"LLM classified as {'on-topic' if is_on_topic else 'off-topic'}"

        except Exception as e:
            # If LLM fails, default to allowing (fail-open for user experience)
            return True, f"LLM check failed ({str(e)}), defaulting to allow"

    @classmethod
    def check_topic(cls, text: str, use_llm_fallback: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Main method: Check if text is on-topic (pet health for dogs/cats).

        Args:
            text: User input text
            use_llm_fallback: Whether to use LLM for uncertain cases

        Returns:
            (is_on_topic, error_message)
            - is_on_topic: True if on-topic, False if off-topic
            - error_message: None if on-topic, rejection message if off-topic
        """
        # Step 1: Fast keyword check
        status, reason = cls.keyword_check(text)

        if status == "on_topic":
            return True, None

        if status == "off_topic":
            return False, cls.OFF_TOPIC_RESPONSE

        # Step 2: Uncertain - use LLM if enabled
        if use_llm_fallback:
            is_on_topic, llm_reason = cls.llm_check(text)
            if is_on_topic:
                return True, None
            else:
                return False, cls.OFF_TOPIC_RESPONSE

        # If LLM fallback disabled and uncertain, allow (fail-open)
        return True, None


# ============================================================================
# Part 6: Unified Input Guardrails Class
# ============================================================================

class InputGuardrails:
    """
    Unified Input Guardrails Class

    Executes all checks in the order specified by the document:
    1. Sanitize and normalize input text
    2. Scope validation (species + supported categories)
    2.5. Off-topic detection (keyword + LLM fallback) - NEW
    3. Structured field completeness check
    4. Immediate ER pre-check (structured first, then text fallback)
    5. Prompt injection / unsafe request detection
    6. If missing fields → return ≤2 follow-up questions
    """
    
    def __init__(self):
        self.scope = ScopeGuardrails()
        self.fields = StructuredFieldsGuardrails()
        self.er_check = ERPreCheckGuardrails()
        self.quality = InputQualityGuardrails()
        self.safety = SafetyGuardrails()
        self.offtopic = OffTopicGuardrails()
    
    def validate_all(
        self,
        species: str,
        category: str,
        structured_fields: Dict[str, Any],
        user_description: str = "",
        image_size: int = None,
        image_type: str = None
    ) -> Dict[str, Any]:
        """
        Run all input guardrail checks
        
        Returns a result dictionary:
        {
            "passed": bool,              # Whether all checks passed
            "error": str or None,        # Error message
            "is_er": bool,               # Whether ER was triggered
            "er_response": dict or None, # ER template response
            "needs_followup": bool,      # Whether follow-up questions needed
            "followup_questions": list,  # Follow-up question list
            "sanitized_text": str,       # Sanitized text
            "warnings": list             # Warning messages
        }
        """
        result = {
            "passed": False,
            "error": None,
            "is_er": False,
            "er_response": None,
            "needs_followup": False,
            "followup_questions": [],
            "sanitized_text": "",
            "warnings": []
        }
        
        # ===== Step 1: Sanitize and normalize input =====
        sanitized_text = self.quality.sanitize_text(user_description)
        within_limit, sanitized_text = self.quality.check_text_length(sanitized_text)
        if not within_limit:
            result["warnings"].append("Input text was truncated")
        result["sanitized_text"] = sanitized_text
        
        # ===== Step 2: Scope validation =====
        # Check species
        passed, error = self.scope.check_species(species)
        if not passed:
            result["error"] = error
            return result
        
        # Check category
        passed, error = self.scope.check_category(category)
        if not passed:
            result["error"] = error
            return result
        
        # Check symptom input
        passed, error = self.scope.check_symptom_input(sanitized_text)
        if not passed and not structured_fields:
            result["error"] = error
            return result

        # ===== Step 2.5: Off-topic detection =====
        # Only check if there's user text to analyze
        if sanitized_text and len(sanitized_text) >= 5:
            is_on_topic, offtopic_error = self.offtopic.check_topic(
                sanitized_text,
                use_llm_fallback=True
            )
            if not is_on_topic:
                result["error"] = offtopic_error
                return result

        # ===== Step 3: Structured field completeness =====
        complete, error, followup_questions = self.fields.check_completeness(
            category, structured_fields
        )
        if not complete:
            result["needs_followup"] = True
            result["followup_questions"] = followup_questions
        
        # ===== Step 4: Immediate ER pre-check =====
        # Include species and category in structured_fields for ER check
        er_check_fields = {
            "species": species,
            "category": category,
            **structured_fields
        }
        is_er, er_response = self.er_check.run_er_precheck(
            er_check_fields, sanitized_text
        )
        if is_er:
            result["passed"] = True
            result["is_er"] = True
            result["er_response"] = er_response
            return result
        
        # ===== Step 5: Safety detection =====
        is_injection, pattern = self.safety.detect_injection(sanitized_text)
        if is_injection:
            result["warnings"].append("Unusual input pattern detected and ignored")
            sanitized_text = self.safety.sanitize_for_safety(sanitized_text)
            result["sanitized_text"] = sanitized_text
        
        is_unsafe, pattern = self.safety.detect_unsafe_request(sanitized_text)
        if is_unsafe:
            result["warnings"].append("Note: We only provide triage guidance, not medication dosing or diagnosis")
        
        # ===== Step 6: Image validation (if provided) =====
        if image_size is not None and image_type is not None:
            passed, error = self.quality.validate_image(image_size, image_type)
            if not passed:
                result["error"] = error
                return result
        
        # ===== All checks passed =====
        result["passed"] = True
        return result


