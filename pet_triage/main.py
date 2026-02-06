# ============================================================================
# File 6: main.py - Main Application (Integrates All Tasks)
# ============================================================================
"""
Main Application: Pet Triage System

Uses LangChain Agent with autonomous tool selection.

Flow:
User Input → Input Guardrails → Agent Loop (autonomous tool calls) → Output Guardrails → Response

The Agent autonomously selects tools:
- check_red_flags: Emergency detection (rule-based)
- vector_search: RAG knowledge base (18,909 records)
- analyze_image: GPT-4V image analysis
- find_nearby_vets: Vet finder (OpenStreetMap)
- generate_triage_response: Format final output

NOTE: This file imports from shared module for consistency.
"""

import json
import sys
import os
from typing import Dict, Any, Optional, List

# Add RAG directory to path for agent imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'RAG'))

# Import from shared module (single source of truth)
from shared.constants import SUPPORTED_CATEGORIES, RiskLevel
from shared.red_flags import check_immediate_er
from shared.schemas import get_fallback_response

# Import from our task files
from llm_setup import (
    get_openai_client,
    get_er_template
)
from input_guardrails import InputGuardrails
from output_guardrails import OutputGuardrails


# Initialize guardrails
input_guardrails = InputGuardrails()
output_guardrails = OutputGuardrails()


# ============================================================================
# AGENT MODE: Autonomous Triage with Tool Selection
# ============================================================================

def run_triage_agent(
    species: str,
    category: str,
    structured_fields: Dict[str, Any],
    user_description: str = "",
    pet_profile: Dict[str, Any] = None,
    image_base64: str = None,
    image_type: str = None,
    image_path: str = None,
    latitude: float = None,
    longitude: float = None,
    triage_history: List[Dict[str, Any]] = None,  # New
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Agent-based triage function with autonomous tool selection.

    This function uses a LangChain Agent that can:
    - Decide which tools to call based on the situation
    - Chain multiple tools together (e.g., check emergency → search knowledge → analyze image)
    - Adapt strategy based on intermediate results

    The workflow is wrapped by mandatory Input/Output Guardrails.

    Args:
        species: Pet species (dog/cat)
        category: Symptom category
        structured_fields: Structured fields from UI
        user_description: User's free text description
        pet_profile: Pet profile information
        image_base64: Base64 encoded image (optional)
        image_type: Image MIME type (optional)
        image_path: Path to image file (optional)
        latitude: User latitude for vet finder (optional)
        longitude: User longitude for vet finder (optional)
        verbose: Print agent reasoning steps

    Returns:
        Triage result dictionary with:
            - success: bool
            - response: TriageResponse dict
            - is_er: bool
            - model_used: str
            - tools_used: List of tools called by agent
            - warnings: List of warnings
    """
    # Import agent here to avoid circular imports
    from core.agent import PetTriageAgent

    result = {
        "success": False,
        "response": None,
        "error": None,
        "warnings": [],
        "is_er": False,
        "model_used": None,
        "tools_used": [],
        "mode": "agent",
        "guardrail_rejected": False  # Flag for input guardrail rejections
    }

    # =========================================================================
    # STEP 1: INPUT GUARDRAILS (Mandatory - runs before Agent)
    # =========================================================================
    print("\n[Agent Mode - Step 1] Running input guardrails...")

    image_size = len(image_base64) if image_base64 else None

    guardrail_result = input_guardrails.validate_all(
        species=species,
        category=category,
        structured_fields=structured_fields,
        user_description=user_description,
        image_size=image_size,
        image_type=image_type
    )

    if not guardrail_result["passed"]:
        result["error"] = guardrail_result["error"]
        result["guardrail_rejected"] = True  # Mark as guardrail rejection
        return result

    result["warnings"] = guardrail_result["warnings"]
    sanitized_description = guardrail_result["sanitized_text"]


    # =========================================================================
    # STEP 1.5: TEXT EMERGENCY PRE-CHECK
    # =========================================================================
    # Check user description for obvious blood/emergency keywords
    text_lower = sanitized_description.lower()
    text_emergency_keywords = ["blood", "bleeding", "not breathing", "unconscious", 
                               "collapsed", "seizure", "hit by car", "poisoning",
                               "ate poison", "choking", "can't breathe", "cant breathe",
                               "blue gums", "pale gums", "white gums", "purple gums"]
    
    if any(keyword in text_lower for keyword in text_emergency_keywords):

        print("[Agent Mode - TEXT EMERGENCY DETECTED] Blood/emergency keyword found - forcing ER response")
        
        # Get ER template
        er_template = get_er_template(category)
        er_template["category"] = category
        matched_keywords = [kw for kw in text_emergency_keywords if kw in text_lower]
        er_template["red_flags"] = matched_keywords[:3]  # Top 3 matched
        er_template["reasoning_summary"] = [f"Emergency symptoms detected: {', '.join(matched_keywords)}"]
        
        # Add nearby vets if location provided
        if latitude and longitude:
            try:
                from core.tools import find_nearby_vets
                # First try emergency vets, then fall back to all vets
                nearby_result = find_nearby_vets(latitude, longitude, radius_meters=15000, max_results=5, emergency_only=True)
                if nearby_result.get("success") and nearby_result.get("vets") and len(nearby_result["vets"]) >= 2:
                    er_template["nearby_vets"] = nearby_result["vets"]
                else:
                    # Not enough emergency vets, get all vets
                    nearby_result = find_nearby_vets(latitude, longitude, radius_meters=15000, max_results=5, emergency_only=False)
                    if nearby_result.get("success") and nearby_result.get("vets"):
                        er_template["nearby_vets"] = nearby_result["vets"]
            except Exception as e:
                print(f"  [Warning] Vet finder failed: {e}")
        
        result["success"] = True
        result["response"] = er_template
        result["is_er"] = True
        result["model_used"] = "rule-based (emergency keywords)"
        result["tools_used"] = [{"tool": "check_emergency_keywords", "input": sanitized_description[:50]}]
        return result

    # =========================================================================
    # STEP 1.6: IMAGE EMERGENCY PRE-CHECK (if image provided)
    # =========================================================================
    # Analyze image FIRST and check for blood/trauma - override to ER immediately
    if image_base64:
        try:
            from core.image_analyzer import analyze_pet_image
            import tempfile
            import base64 as b64
            
            # Save to temp file for analysis
            image_data = b64.b64decode(image_base64)
            suffix = ".jpg" if image_type == "image/jpeg" else ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(image_data)
                temp_path = f.name
            
            # Analyze the image
            image_result = analyze_pet_image(temp_path, user_question=sanitized_description)
            image_description = image_result.get("description", "").lower()
            
            # Clean up
            import os as os_mod
            os_mod.unlink(temp_path)
            
            # Check for blood/emergency keywords in image analysis
            emergency_keywords = ["blood", "bleeding", "wound", "injury", "trauma", 
                                  "laceration", "gash", "cut", "emergency", "er:", 
                                  "immediate", "urgent", "severe"]
            
            if any(keyword in image_description for keyword in emergency_keywords):
                print("[Agent Mode - IMAGE EMERGENCY DETECTED] Blood/injury in image - forcing ER response")
                
                # Get ER template
                er_template = get_er_template(category)
                er_template["category"] = category
                er_template["red_flags"] = ["Blood/injury visible in image"]
                er_template["reasoning_summary"] = ["Image shows blood or injury requiring immediate veterinary attention"]
                
                # Add nearby vets if location provided
                if latitude and longitude:
                    try:
                        from core.tools import find_nearby_vets
                        # First try emergency vets, then fall back to all vets
                        nearby_result = find_nearby_vets(latitude, longitude, radius_meters=15000, max_results=5, emergency_only=True)
                        if nearby_result.get("success") and nearby_result.get("vets") and len(nearby_result["vets"]) >= 2:
                            er_template["nearby_vets"] = nearby_result["vets"]
                        else:
                            nearby_result = find_nearby_vets(latitude, longitude, radius_meters=15000, max_results=5, emergency_only=False)
                            if nearby_result.get("success") and nearby_result.get("vets"):
                                er_template["nearby_vets"] = nearby_result["vets"]
                    except Exception as e:
                        print(f"  [Warning] Vet finder failed: {e}")
                
                result["success"] = True
                result["response"] = er_template
                result["is_er"] = True
                result["model_used"] = "gpt-4o (image analysis)"
                result["tools_used"] = [{"tool": "analyze_image", "input": "image emergency pre-check"}]
                return result
                
        except Exception as e:
            print(f"  [Warning] Image pre-check failed: {e}")
            # Continue with normal flow if image analysis fails

    # =========================================================================
    # STEP 2: AGENT LOOP (Autonomous Decision Making)
    # =========================================================================
    print("[Agent Mode - Step 2] Starting Agent loop...")

    try:
        # Initialize the triage agent
        agent = PetTriageAgent(
            model="gpt-4o",  # Better instruction following
            temperature=0.3,
            max_iterations=8,
            verbose=verbose
        )

        # Run triage through the agent
        agent_result = agent.triage(
            species=species,
            category=category,
            structured_fields=structured_fields,
            user_description=sanitized_description,
            pet_profile=pet_profile,
            image_base64=image_base64,
            image_path=image_path,
            latitude=latitude,
            longitude=longitude,
            triage_history=triage_history  # New
        )

        result["model_used"] = agent.model
        result["tools_used"] = agent_result.get("tools_used", [])
        result["rag_source_count"] = agent_result.get("rag_source_count", 0)
        result["used_web_search"] = agent_result.get("used_web_search", False)

        if not agent_result.get("success"):
            raise Exception(agent_result.get("error", "Agent execution failed"))

        # Get the triage response from agent
        agent_response = agent_result.get("triage_response", {})

        print(f"  Agent completed. Tools used: {len(result['tools_used'])}")
        for tool_info in result["tools_used"]:
            print(f"    - {tool_info['tool']}")

    except Exception as e:
        print(f"  [ERROR] Agent execution failed: {e}")
        result["success"] = True
        result["response"] = output_guardrails.get_fallback(str(e))
        result["model_used"] = "fallback"
        result["warnings"].append(f"Agent failed, using fallback: {str(e)}")
        return result

    # =========================================================================
    # STEP 3: OUTPUT GUARDRAILS (Mandatory - runs after Agent)
    # =========================================================================
    print("[Agent Mode - Step 3] Running output guardrails...")

    # Convert agent response to JSON string for guardrails
    if isinstance(agent_response, dict):
        response_str = json.dumps(agent_response, ensure_ascii=False)
    else:
        response_str = str(agent_response)

    success, processed_response = output_guardrails.validate_and_process(response_str)

    if not success:
        print("  [WARNING] Output validation failed, using fallback")
        result["warnings"].append("Output validation failed, using fallback response")

    if processed_response.get("_risk_escalated"):
        result["warnings"].append(
            f"Risk level was escalated: {processed_response.get('_escalation_reason', 'safety calibration')}"
        )

    result["success"] = True
    result["response"] = processed_response
    result["is_er"] = processed_response.get("risk_level") == "ER"

    # =========================================================================
    # STEP 3.5: ADD SOURCES INFO FROM TOOLS USED
    # =========================================================================
    tools_used = result.get("tools_used", [])
    tool_names = [t.get("tool") if isinstance(t, dict) else str(t) for t in tools_used]
    
    # Check if RAG was used
    if "vector_search" in tool_names and not result["response"].get("sources"):
        # RAG was used - add source indicator
        result["response"]["sources"] = [{"type": "RAG", "count": 3, "label": "Pet Health Knowledge Base"}]
        print("  📚 RAG sources added to response")
    
    # Check if web search was used
    if "web_search_tool" in tool_names:
        sources = result["response"].get("sources") or []
        sources.append({"type": "web", "label": "Google Search"})
        result["response"]["sources"] = sources
        print("  🌐 Web search source added to response")

    # =========================================================================
    # STEP 4: AUTO-ATTACH NEARBY VETS FOR ER CASES (if location provided)
    # =========================================================================
    if result["is_er"] and latitude is not None and longitude is not None:
        print("[Agent Mode - Step 4] Finding nearby emergency vets...")
        try:
            from core.tools import find_nearby_vets as _find_nearby_vets
            nearby_vets = _find_nearby_vets(
                latitude=latitude,
                longitude=longitude,
                emergency_only=True,
                max_results=3
            )
            if nearby_vets and nearby_vets.get("vets"):
                result["response"]["nearby_vets"] = nearby_vets["vets"]
                result["tools_used"].append({"tool": "find_nearby_vets", "auto": True})
                print(f"  Found {len(nearby_vets['vets'])} nearby emergency vets")
            else:
                print("  No nearby vets found")
        except Exception as e:
            print(f"  [WARNING] Failed to find nearby vets: {e}")
            result["warnings"].append(f"Failed to find nearby vets: {str(e)}")

    return result

# Redoing with better targeting. I will update `run_triage` signature first.
def run_triage(
    species: str,
    category: str,
    structured_fields: Dict[str, Any],
    user_description: str = "",
    pet_profile: Dict[str, Any] = None,
    image_base64: str = None,
    image_type: str = None,
    image_path: str = None,
    latitude: float = None,
    longitude: float = None,
    triage_history: List[Dict[str, Any]] = None,  # New
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Main triage function - wrapper for Agent mode.
    """
    return run_triage_agent(
        species=species,
        category=category,
        structured_fields=structured_fields,
        user_description=user_description,
        pet_profile=pet_profile,
        image_base64=image_base64,
        image_type=image_type,
        image_path=image_path,
        latitude=latitude,
        longitude=longitude,
        triage_history=triage_history,  # Pass history
        verbose=verbose
    )


# ============================================================================
# Demo Functions
# ============================================================================

def demo():
    """
    Demo function showing AGENT MODE (autonomous tool selection)
    """
    print("="*60)
    print("PET TRIAGE SYSTEM DEMO - AGENT MODE")
    print("="*60)
    print("\nAgent Mode uses LangChain to autonomously select tools:")
    print("  - check_red_flags: Emergency detection")
    print("  - vector_search: Knowledge base search")
    print("  - analyze_image: Image analysis (GPT-4V)")
    print("  - find_nearby_vets: Vet finder")
    print("  - generate_triage_response: Format output")

    # Demo Case 1: Agent handling a moderate case
    print("\n" + "="*60)
    print("AGENT CASE 1: Dog with skin issues")
    print("="*60)

    result1 = run_triage_agent(
        species="dog",
        category="Itching & Skin Issues",
        structured_fields={
            "duration": "3 days",
            "scratching_frequency": "frequent",
            "visible_rash": "Yes"
        },
        user_description="My dog has been scratching a lot and has a red rash on his belly. It started 3 days ago after we went to the park.",
        pet_profile={
            "name": "Buddy",
            "age": "2 years",
            "breed": "Golden Retriever"
        },
        verbose=True
    )

    print("\nResult:")
    print(f"  Success: {result1['success']}")
    print(f"  Is ER: {result1['is_er']}")
    print(f"  Model used: {result1['model_used']}")
    print(f"  Mode: {result1.get('mode', 'agent')}")
    print(f"  Tools used: {[t['tool'] for t in result1.get('tools_used', [])]}")
    if result1['response']:
        print(f"  Risk Level: {result1['response'].get('risk_level')}")
        print(f"  Reasoning: {result1['response'].get('reasoning_summary', [])[:2]}")

    # Demo Case 2: Emergency via Agent
    print("\n" + "="*60)
    print("AGENT CASE 2: EMERGENCY - Bloat symptoms in large dog")
    print("="*60)

    result2 = run_triage_agent(
        species="dog",
        category="Stomach Upset",
        structured_fields={
            "abdomen_distended": "Yes",
            "unproductive_retching": "Yes",
            "restless": "Yes"
        },
        user_description="My Great Dane has a swollen belly and keeps trying to vomit but nothing comes out. He's very restless and won't lie down.",
        pet_profile={
            "name": "Duke",
            "age": "6 years",
            "breed": "Great Dane"
        },
        verbose=True
    )

    print("\nResult:")
    print(f"  Success: {result2['success']}")
    print(f"  Is ER: {result2['is_er']}")
    print(f"  Tools used: {[t['tool'] for t in result2.get('tools_used', [])]}")
    if result2['response']:
        print(f"  Risk Level: {result2['response'].get('risk_level')}")
        print(f"  Red Flags: {result2['response'].get('red_flags')}")
        print(f"  Actions: {result2['response'].get('recommended_actions', [])[:2]}")

    print("\n" + "="*60)
    print("AGENT MODE DEMO COMPLETE")
    print("="*60)


# ============================================================================
# Test All Tasks
# ============================================================================

def test_all_tasks():
    """
    Run tests for all tasks
    """
    print("="*60)
    print("RUNNING ALL TASK TESTS")
    print("="*60)

    # Test Task 1
    print("\n--- Testing Task 1: LLM Setup ---")
    from tests.test_llm_setup import run_all_tests as test_llm_setup_all
    test_llm_setup_all()

    # Test Task 2
    print("\n--- Testing Task 2: Prompts ---")
    from tests.test_prompts import test_prompts, test_system_prompts
    test_prompts()
    test_system_prompts()

    # Test Task 3
    print("\n--- Testing Task 3: Input Guardrails ---")
    from tests.test_input_guardrails import test_input_guardrails
    test_input_guardrails()

    # Test Task 4
    print("\n--- Testing Task 4: Output Guardrails ---")
    from tests.test_output_guardrails import test_output_guardrails
    test_output_guardrails()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*60)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "test":
            test_all_tasks()
        elif command in ("demo", "demo-agent"):
            demo()
        elif command == "agent":
            # Quick agent test
            print("Running quick agent test...")
            result = run_triage_agent(
                species="dog",
                category="Stomach Upset",
                structured_fields={"vomiting_frequency": "once"},
                user_description="My dog vomited once",
                verbose=True
            )
            print(f"\nResult: {json.dumps(result['response'], indent=2, ensure_ascii=False)}")
        else:
            print("Usage: python main.py [test|demo|agent]")
            print("")
            print("Commands:")
            print("  test  - Run all unit tests")
            print("  demo  - Run agent demo with sample cases")
            print("  agent - Quick agent test with sample input")
    else:
        # Default: run demo
        demo()
