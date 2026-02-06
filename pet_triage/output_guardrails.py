# ============================================================================
# File 5: task4_output_guardrails.py - Task 3.4 Output Guardrails
# ============================================================================
"""
Task 3.4: Output Guardrails

This file implements the 6-layer output guardrails from the document:
Guardrail A - Strict JSON Schema Validation
Guardrail B - Content Safety Restrictions (No Diagnosis/Dosing)
Guardrail C - Risk Level Calibration (Prevent Under-triage)
Guardrail D - Mandatory Disclaimer
Guardrail E - UI Constraints (Short Lists + Length Limits)
Guardrail F - Safe Fallback (Never break the app)

According to the document:
"All LLM outputs must follow a fixed JSON schema so the mobile UI 
 can render urgency level, red flags, and next actions consistently."

NOTE: This file now imports from shared module for consistency.
"""

import json
import re
from typing import Dict, Any, Tuple, Optional, List

# Import from shared module (single source of truth)
from shared.constants import (
    OUTPUT_LIMITS,
    RISK_LEVEL_DESCRIPTIONS as RISK_LEVELS,
    RiskLevel,
)


# ============================================================================
# Part 1: Output JSON Schema Definition
# ============================================================================

REQUIRED_OUTPUT_SCHEMA = {
    "risk_level": str,           # ER | TODAY | SOON | MONITOR
    "category": str,             # One of 9 categories
    "red_flags": list,           # Red flag signals
    "reasoning_summary": list,   # 1-3 reasons
    "recommended_actions": list, # 3-6 actions
    "what_to_monitor": list,     # 2-5 monitoring items
    "follow_up_questions": list, # 0-2 follow-up questions
    "disclaimer": str            # Disclaimer
}

VALID_RISK_LEVELS = ["ER", "TODAY", "SOON", "MONITOR"]


# ============================================================================
# Part 2: Guardrail A - JSON Schema Validation
# ============================================================================

class SchemaGuardrail:
    """
    Guardrail A: Strict JSON Schema Validation
    
    Ensure all LLM outputs conform to the predefined JSON structure
    """
    
    @staticmethod
    def parse_json(response_text: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Parse JSON response
        
        Returns: (success, parsed_result, error_message)
        """
        try:
            data = json.loads(response_text)
            return True, data, None
        except json.JSONDecodeError as e:
            # Try to extract JSON (sometimes model adds extra text)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    return True, data, None
                except:
                    pass
            return False, None, f"JSON parse failed: {str(e)}"
    
    @staticmethod
    def validate_schema(data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate JSON conforms to schema
        
        Returns: (is_valid, missing_fields_list)
        """
        missing_fields = []
        
        for field, expected_type in REQUIRED_OUTPUT_SCHEMA.items():
            if field not in data:
                missing_fields.append(field)
            elif not isinstance(data[field], expected_type):
                missing_fields.append(f"{field}(wrong type)")
        
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def validate_risk_level(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate risk level is valid
        
        Returns: (is_valid, corrected_risk_level)
        """
        risk_level = data.get("risk_level", "").upper()
        
        if risk_level in VALID_RISK_LEVELS:
            return True, risk_level
        
        # Try to correct common variants
        corrections = {
            "EMERGENCY": "ER",
            "HIGH": "ER",
            "MEDIUM": "TODAY",
            "LOW": "MONITOR",
            "URGENT": "ER",
            "CRITICAL": "ER"
        }
        
        for key, value in corrections.items():
            if key in risk_level:
                return True, value
        
        # Default to TODAY (conservative)
        return False, "TODAY"


# ============================================================================
# Part 3: Guardrail B - Content Safety Restrictions
# ============================================================================

class ContentSafetyGuardrail:
    """
    Guardrail B: Content Safety Restrictions
    
    Detect and remove disallowed content:
    - Definitive diagnosis
    - Medication dosing
    - Dangerous procedure instructions
    - Absolute guarantees
    """
    
    # Forbidden content patterns
    FORBIDDEN_PATTERNS = {
        "diagnosis": [
            r'your (dog|cat|pet) has',
            r'diagnosis is',
            r'definitely has',
            r'this is \w+ disease',
            r'suffering from \w+',
        ],
        "dosing": [
            r'\d+\s*(mg|ml|milligram|milliliter)',
            r'give.*\d+.*mg',
            r'dosage',
            r'prescribe',
            r'administer.*medication',
        ],
        "dangerous": [
            r'cut.*open',
            r'perform.*surgery',
            r'force.*vomit',
            r'induce vomiting yourself',
        ],
        "guarantee": [
            r'100%.*safe',
            r'definitely.*fine',
            r'guarantee',
            r'nothing to worry about',
            r'completely safe',
        ]
    }
    
    @classmethod
    def check_content(cls, data: Dict) -> Tuple[bool, List[str]]:
        """
        Check if content contains forbidden content
        
        Returns: (is_safe, issues_list)
        """
        issues = []
        
        # Combine all text fields
        all_text = json.dumps(data, ensure_ascii=False).lower()
        
        for category, patterns in cls.FORBIDDEN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    issues.append(f"Detected forbidden content: {category}")
                    break
        
        return len(issues) == 0, issues
    
    @classmethod
    def sanitize_content(cls, data: Dict) -> Dict:
        """
        Sanitize content to remove forbidden content
        
        Returns: Sanitized data
        """
        text_fields = ["reasoning_summary", "recommended_actions", "what_to_monitor", "disclaimer"]
        
        for field in text_fields:
            if field in data and isinstance(data[field], list):
                cleaned_items = []
                for item in data[field]:
                    if isinstance(item, str):
                        # Remove dosing info
                        item = re.sub(r'\d+\s*(mg|ml)[^\.,]*', '', item)
                        # Remove diagnosis statements
                        item = re.sub(r'diagnosis is[^\.,]*', '', item)
                        if item.strip():
                            cleaned_items.append(item.strip())
                data[field] = cleaned_items
        
        return data


# ============================================================================
# Part 4: Guardrail C - Risk Level Calibration
# ============================================================================

class RiskCalibrationGuardrail:
    """
    Guardrail C: Risk Level Calibration
    
    Prevent under-triage - auto-escalate if high-risk signals detected
    
    According to the document:
    "In triage, under-triage is more dangerous than over-triage. 
     Conservative escalation is safer."
    """
    
    # Emergency signal keywords
    ER_SIGNALS = [
        "breathing difficulty", "open mouth breathing", "blue gums", "purple gums",
        "seizure", "convulsion", "unconscious", "unresponsive",
        "urinary blockage", "can't urinate", "male cat straining",
        "bloat", "gdv", "gastric dilatation", "stomach twisted",
        "heavy bleeding", "won't stop bleeding",
        "eye popped out", "proptosis",
        "poisoning", "ate chocolate", "ate lilies", "ate antifreeze"
    ]
    
    # Today signals
    TODAY_SIGNALS = [
        "repeated vomiting", "blood in stool", "not eating for 24 hours",
        "very lethargic", "fever", "obvious pain", "blood in vomit"
    ]
    
    @classmethod
    def calibrate_risk(cls, data: Dict) -> Dict:
        """
        Calibrate risk level based on content
        
        Check if risk level matches the severity in the content
        """
        # Combine all text
        all_text = json.dumps(data, ensure_ascii=False).lower()
        current_risk = data.get("risk_level", "").upper()
        
        # Check for ER signals
        has_er_signal = any(signal in all_text for signal in cls.ER_SIGNALS)
        if has_er_signal and current_risk != "ER":
            data["risk_level"] = "ER"
            data["_risk_escalated"] = True
            data["_escalation_reason"] = "Emergency signals detected in assessment"
        
        # Check for TODAY signals
        has_today_signal = any(signal in all_text for signal in cls.TODAY_SIGNALS)
        if has_today_signal and current_risk == "MONITOR":
            data["risk_level"] = "TODAY"
            data["_risk_escalated"] = True
            data["_escalation_reason"] = "Elevated risk signals detected"
        
        # Red flags present should not be MONITOR
        red_flags = data.get("red_flags", [])
        if len(red_flags) > 0 and current_risk == "MONITOR":
            data["risk_level"] = "SOON"
            data["_risk_escalated"] = True
        
        return data


# ============================================================================
# Part 5: Guardrail D - Mandatory Disclaimer
# ============================================================================

class DisclaimerGuardrail:
    """
    Guardrail D: Mandatory Disclaimer
    
    Every response must include a clear disclaimer
    """
    
    DEFAULT_DISCLAIMER = (
        "This is not a veterinary diagnosis. If symptoms worsen or you're concerned, "
        "seek veterinary care immediately."
    )
    
    @classmethod
    def ensure_disclaimer(cls, data: Dict) -> Dict:
        """
        Ensure disclaimer is present and adequate
        """
        disclaimer = data.get("disclaimer", "")
        
        # Check if disclaimer exists and is adequate
        if not disclaimer or len(disclaimer) < 20:
            data["disclaimer"] = cls.DEFAULT_DISCLAIMER
        
        # Ensure it contains key phrases
        required_phrases = ["not", "diagnosis", "veterinary", "vet"]
        disclaimer_lower = disclaimer.lower()
        
        has_required = sum(1 for phrase in required_phrases if phrase in disclaimer_lower)
        if has_required < 2:
            data["disclaimer"] = cls.DEFAULT_DISCLAIMER
        
        return data


# ============================================================================
# Part 6: Guardrail E - UI Constraints
# ============================================================================

class UIConstraintsGuardrail:
    """
    Guardrail E: UI Constraints
    
    Enforce short lists and length limits for mobile UI
    """
    
    @classmethod
    def enforce_limits(cls, data: Dict) -> Dict:
        """
        Enforce UI constraints on output
        """
        # Truncate lists to max lengths
        list_limits = {
            "reasoning_summary": OUTPUT_LIMITS.get("reasoning_summary", 3),
            "recommended_actions": OUTPUT_LIMITS.get("recommended_actions", 6),
            "what_to_monitor": OUTPUT_LIMITS.get("what_to_monitor", 5),
            "follow_up_questions": OUTPUT_LIMITS.get("follow_up_questions", 2),
            "red_flags": OUTPUT_LIMITS.get("red_flags", 5)
        }
        
        for field, limit in list_limits.items():
            if field in data and isinstance(data[field], list):
                data[field] = data[field][:limit]
                
                # Also truncate individual items
                truncated_items = []
                for item in data[field]:
                    if isinstance(item, str) and len(item) > OUTPUT_LIMITS["max_item_length"]:
                        # Truncate at word boundary
                        truncated = item[:OUTPUT_LIMITS["max_item_length"]]
                        last_space = truncated.rfind(' ')
                        if last_space > OUTPUT_LIMITS["max_item_length"] * 0.7:
                            truncated = truncated[:last_space]
                        truncated_items.append(truncated.strip())
                    else:
                        truncated_items.append(item)
                data[field] = truncated_items
        
        return data


# ============================================================================
# Part 7: Guardrail F - Safe Fallback
# ============================================================================

class FallbackGuardrail:
    """
    Guardrail F: Safe Fallback
    
    Return a safe, conservative response when model output is invalid
    """
    
    DEFAULT_FALLBACK = {
        "risk_level": "TODAY",
        "category": "Something Else",
        "red_flags": [],
        "reasoning_summary": [
            "Unable to complete full assessment",
            "Professional evaluation recommended"
        ],
        "recommended_actions": [
            "Contact your regular veterinarian during business hours",
            "Monitor your pet closely for any changes",
            "If symptoms worsen, seek emergency veterinary care"
        ],
        "what_to_monitor": [
            "Breathing difficulty",
            "Collapse or weakness",
            "Severe pain signs",
            "Worsening of current symptoms"
        ],
        "follow_up_questions": [],
        "disclaimer": "This is not a veterinary diagnosis. If symptoms worsen or you're concerned, seek veterinary care.",
        "_is_fallback": True
    }
    
    @classmethod
    def get_fallback_response(cls, reason: str = None) -> Dict:
        """
        Get safe fallback response
        """
        response = cls.DEFAULT_FALLBACK.copy()
        if reason:
            response["_fallback_reason"] = reason
        return response


# ============================================================================
# Part 8: Unified Output Guardrails Class
# ============================================================================

class OutputGuardrails:
    """
    Unified Output Guardrails Class
    
    Executes all output checks in order:
    1. JSON Schema Validation
    2. Content Safety Check
    3. Risk Level Calibration
    4. Disclaimer Enforcement
    5. UI Constraints
    6. Fallback if needed
    """
    
    def __init__(self):
        self.schema = SchemaGuardrail()
        self.content_safety = ContentSafetyGuardrail()
        self.risk_calibration = RiskCalibrationGuardrail()
        self.disclaimer = DisclaimerGuardrail()
        self.ui_constraints = UIConstraintsGuardrail()
        self.fallback = FallbackGuardrail()
    
    def validate_and_process(self, llm_response: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate and process LLM response through all guardrails
        
        Args:
            llm_response: Raw LLM response text
            
        Returns:
            (success, processed_data_or_fallback)
        """
        # ===== Step 1: Parse JSON =====
        success, data, error = self.schema.parse_json(llm_response)
        if not success:
            print(f"JSON parse failed: {error}")
            return False, self.fallback.get_fallback_response(error)
        
        # ===== Step 2: Validate Schema =====
        valid, missing = self.schema.validate_schema(data)
        if not valid:
            print(f"Schema validation failed. Missing: {missing}")
            # Try to fill in missing fields
            for field in missing:
                if field == "risk_level":
                    data["risk_level"] = "TODAY"
                elif field == "category":
                    data["category"] = "Something Else"
                elif field in ["red_flags", "reasoning_summary", "recommended_actions", "what_to_monitor", "follow_up_questions"]:
                    data[field] = []
                elif field == "disclaimer":
                    data["disclaimer"] = self.disclaimer.DEFAULT_DISCLAIMER
        
        # ===== Step 3: Validate and Correct Risk Level =====
        valid, corrected_risk = self.schema.validate_risk_level(data)
        data["risk_level"] = corrected_risk
        
        # ===== Step 4: Content Safety Check =====
        is_safe, issues = self.content_safety.check_content(data)
        if not is_safe:
            print(f"Content safety issues: {issues}")
            data = self.content_safety.sanitize_content(data)
        
        # ===== Step 5: Risk Level Calibration =====
        data = self.risk_calibration.calibrate_risk(data)
        
        # ===== Step 6: Ensure Disclaimer =====
        data = self.disclaimer.ensure_disclaimer(data)
        
        # ===== Step 7: Enforce UI Constraints =====
        data = self.ui_constraints.enforce_limits(data)
        
        return True, data
    
    def get_fallback(self, reason: str = None) -> Dict[str, Any]:
        """
        Get fallback response
        """
        return self.fallback.get_fallback_response(reason)


