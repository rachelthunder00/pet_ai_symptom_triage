"""
Pet Health AI - Tool Functions
=============================

This module contains specialized tool functions called by the agent:
1. vector_search - Search knowledge base (from rag_chain.py)
2. check_red_flags - Rule-based emergency symptom detection
3. find_nearby_vets - Geolocation-based vet finder (OpenStreetMap)
4. analyze_image - GPT-4 Vision analysis (from image_analyzer.py)
5. web_search - Real-time information (Gemini + Google Search)

Usage:
    from tools import find_nearby_vets, check_red_flags, web_search

NOTE: Red flag detection rules have been consolidated into shared/red_flags.py.
This file now imports from the shared module for consistency.
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for shared module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from shared module (single source of truth)
from shared.red_flags import (
    check_red_flags as _check_red_flags_impl,
    check_text_for_red_flags,
    CRITICAL_KEYWORDS,
    URGENT_KEYWORDS, 
    MODERATE_KEYWORDS,
    BLOAT_RISK_BREEDS,
    BRACHYCEPHALIC_BREEDS,
)
from shared.constants import (
    normalize_risk_level,
    SEVERITY_TO_RISK_LEVEL,
)

load_dotenv()

# ============================================================
# Configuration
# ============================================================

# Google AI API Key (for Gemini + Google Search)
# Get from: https://aistudio.google.com/app/apikey
# NOTE: This is used for web_search functionality with Gemini 2.0
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# ============================================================
# Tool 3: Check Red Flags (Emergency Detection)
# ============================================================
# NOTE FOR TEAM: Red flag rules are now defined in shared/red_flags.py
# Modify that file to add/remove emergency symptoms.
# This wrapper maintains backward compatibility.

# Re-export shared constants for backward compatibility
RED_FLAG_SYMPTOMS = {
    "er": {
        "keywords": CRITICAL_KEYWORDS,
        "severity": "ER",
        "action": "EMERGENCY - Seek immediate veterinary care! Call emergency vet now."
    },
    "today": {
        "keywords": URGENT_KEYWORDS,
        "severity": "TODAY",
        "action": "URGENT - Contact your veterinarian today or visit an emergency clinic."
    },
    "soon": {
        "keywords": MODERATE_KEYWORDS,
        "severity": "SOON",
        "action": "Schedule a veterinary appointment soon (within 24-48 hours)."
    }
}

BREED_SPECIFIC_ALERTS = {
    "bloat_risk": BLOAT_RISK_BREEDS,
    "brachycephalic": BRACHYCEPHALIC_BREEDS,
}


def check_red_flags(
    symptoms: str = None,
    pet_species: str = None,
    pet_breed: str = None,
    structured_fields: Dict[str, Any] = None,
    category: str = None
) -> Dict[str, Any]:
    """
    Check for emergency red flags using BOTH text and structured field analysis.

    This is the unified emergency detection tool for the Agent.
    It combines:
    1. Structured field rules (more reliable, from UI forms)
    2. Text keyword matching (fallback for free text)

    Args:
        symptoms: Free text description of the pet's symptoms
        pet_species: 'dog' or 'cat'
        pet_breed: The pet's breed (for breed-specific alerts)
        structured_fields: Structured fields from UI (checkboxes, dropdowns)
        category: Symptom category selected by user

    Returns:
        Dict with:
            - is_emergency: bool - TRUE = go to ER immediately
            - severity: "ER" | "TODAY" | "SOON" | "MONITOR"
            - risk_level: "ER" | "TODAY" | "SOON" | "MONITOR"
            - red_flags: List of detected red flags
            - recommendation: Action advice
            - action: "RETURN_ER_TEMPLATE" | "PROCEED_WITH_URGENCY" | "PROCEED_NORMAL"

    NOTE FOR TEAM:
    - Structured field rules: shared/red_flags.py -> check_immediate_er()
    - Text keyword rules: shared/red_flags.py -> check_text_for_red_flags()
    """
    from shared.red_flags import check_immediate_er, check_text_for_red_flags

    result = {
        "is_emergency": False,
        "severity": "MONITOR",
        "risk_level": "MONITOR",
        "red_flags": [],
        "breed_alerts": [],
        "recommendation": "",
        "action": "PROCEED_NORMAL",
        "category": category or "Something Else"
    }

    # =========================================================================
    # STEP 1: Check structured fields FIRST (more reliable)
    # =========================================================================
    if structured_fields:
        # Build fields dict with all context
        fields = structured_fields.copy()
        if pet_species:
            fields["species"] = pet_species
        if pet_breed:
            fields["breed"] = pet_breed
        if category:
            fields["category"] = category

        er_result = check_immediate_er(fields)

        if er_result.get("is_er"):
            result["is_emergency"] = True
            result["severity"] = "ER"
            result["risk_level"] = "ER"
            result["red_flags"] = er_result.get("red_flags", [])
            result["category"] = er_result.get("category", category)
            result["recommendation"] = "EMERGENCY - Seek immediate veterinary care!"
            result["action"] = "RETURN_ER_TEMPLATE"
            result["reason"] = er_result.get("reason", "Emergency red flag detected")
            result["recommend_nearby_vets"] = True
            return result

    # =========================================================================
    # STEP 2: Check text keywords (fallback)
    # =========================================================================
    if symptoms:
        text_result = check_text_for_red_flags(
            text=symptoms,
            species=pet_species,
            breed=pet_breed
        )

        result["severity"] = text_result.get("severity", "MONITOR")
        result["red_flags"] = text_result.get("matched_symptoms", [])
        result["breed_alerts"] = text_result.get("breed_alerts", [])
        result["recommendation"] = text_result.get("recommendation", "")

        # Map severity to action (severity now uses ER/TODAY/SOON/MONITOR)
        severity_map = {
            "ER": ("ER", True, "RETURN_ER_TEMPLATE"),
            "TODAY": ("TODAY", False, "PROCEED_WITH_URGENCY"),
            "SOON": ("SOON", False, "PROCEED_NORMAL"),
            "MONITOR": ("MONITOR", False, "PROCEED_NORMAL")
        }

        risk_level, is_emergency, action = severity_map.get(
            result["severity"], ("MONITOR", False, "PROCEED_NORMAL")
        )
        result["risk_level"] = risk_level
        result["is_emergency"] = is_emergency
        result["action"] = action
        result["recommend_nearby_vets"] = is_emergency

    # =========================================================================
    # STEP 3: Default if no symptoms provided
    # =========================================================================
    if not result["recommendation"]:
        result["recommendation"] = "Monitor your pet. If symptoms persist or worsen, consult a veterinarian."

    return result


def check_red_flags_for_agent(input_json: str) -> str:
    """
    Agent-friendly wrapper for check_red_flags.

    This wrapper accepts JSON string input and returns JSON string output,
    making it compatible with LangChain Tool binding.

    Args:
        input_json: JSON string with fields:
            {
                "symptoms": "free text description",
                "species": "dog" or "cat",
                "breed": "pet breed",
                "category": "symptom category",
                "structured_fields": {...}  # UI form answers
            }

    Returns:
        JSON string with emergency check results

    Example:
        Input: '{"symptoms": "vomiting blood", "species": "dog"}'
        Output: '{"is_emergency": true, "severity": "ER", ...}'
    """
    try:
        data = json.loads(input_json)

        result = check_red_flags(
            symptoms=data.get("symptoms", ""),
            pet_species=data.get("species"),
            pet_breed=data.get("breed"),
            structured_fields=data.get("structured_fields"),
            category=data.get("category")
        )

        return json.dumps(result, ensure_ascii=False)

    except json.JSONDecodeError as e:
        return json.dumps({
            "error": f"Invalid JSON: {str(e)}",
            "is_emergency": False,
            "action": "PROCEED_NORMAL"
        })
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "is_emergency": False,
            "action": "PROCEED_NORMAL"
        })


# ============================================================
# Tool 4: Find Nearby Vets (OpenStreetMap - FREE)
# ============================================================
# NOTE FOR TEAM: This uses OpenStreetMap Overpass API (completely free!)
# No API key required.
#
# Data source: OpenStreetMap (community-contributed data)
# Limitations: 
# - Data quality varies by region
# - No real-time "open now" information
# - No ratings/reviews
#
# For production, consider supplementing with your own vet database.

def find_nearby_vets(
    latitude: float,
    longitude: float,
    radius_meters: int = 5000,
    emergency_only: bool = False,
    open_now: bool = True,  # Note: OSM doesn't have real-time open status
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Find veterinary clinics near a location using OpenStreetMap (FREE).
    
    Args:
        latitude: User's latitude
        longitude: User's longitude
        radius_meters: Search radius in meters (default 5km)
        emergency_only: If True, prioritize 24-hour/emergency vets
        open_now: Note - OSM doesn't have real-time status, this is ignored
        max_results: Maximum number of results to return
    
    Returns:
        Dict with list of nearby veterinary clinics
    
    NOTE:
    - Uses OpenStreetMap Overpass API (free, no key needed)
    - Data quality depends on community contributions
    - In production, consider supplementing with a dedicated vet database
    """
    
    try:
        import requests
        import math
        
        # Overpass API endpoint (free, no key required)
        overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Build Overpass QL query to find veterinary clinics
        # Search for amenity=veterinary within radius
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="veterinary"](around:{radius_meters},{latitude},{longitude});
          way["amenity"="veterinary"](around:{radius_meters},{latitude},{longitude});
          node["healthcare"="veterinary"](around:{radius_meters},{latitude},{longitude});
          way["healthcare"="veterinary"](around:{radius_meters},{latitude},{longitude});
        );
        out center body;
        """
        
        response = requests.post(
            overpass_url,
            data={"data": overpass_query},
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}",
                "fallback": _get_mock_vet_data(latitude, longitude, emergency_only)
            }
        
        data = response.json()
        elements = data.get("elements", [])
        
        if not elements:
            return {
                "success": True,
                "count": 0,
                "vets": [],
                "message": "No veterinary clinics found nearby. Try increasing search radius.",
                "fallback": _get_mock_vet_data(latitude, longitude, emergency_only)
            }
        
        # Process results
        vets = []
        for element in elements[:max_results * 2]:  # Get extra to filter
            tags = element.get("tags", {})
            
            # Get coordinates (handle both nodes and ways)
            if element.get("type") == "node":
                lat = element.get("lat")
                lon = element.get("lon")
            else:
                # For ways, use center point
                center = element.get("center", {})
                lat = center.get("lat", latitude)
                lon = center.get("lon", longitude)
            
            # Calculate distance
            distance = _calculate_distance(latitude, longitude, lat, lon)
            
            # Calculate distance in miles too
            distance_miles = distance * 0.621371
            
            # Get and format opening hours
            raw_hours = tags.get("opening_hours", "")
            hours_display = _format_opening_hours(raw_hours)
            
            vet_info = {
                "name": tags.get("name", "Veterinary Clinic"),
                "address": _build_address(tags),
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "website": tags.get("website") or tags.get("contact:website"),
                "location": {"lat": lat, "lng": lon},
                "distance_km": round(distance, 2),
                "distance_miles": round(distance_miles, 2),
                "osm_id": element.get("id"),
                "opening_hours": hours_display,
                "is_emergency_clinic": False,
                "is_24_hour": False
            }
            
            # Check if it's an emergency or 24-hour clinic
            name_lower = (tags.get("name") or "").lower()
            if any(term in name_lower for term in ["emergency", "urgent", "notfall"]):
                vet_info["is_emergency_clinic"] = True
            if "24" in name_lower or raw_hours == "24/7":
                vet_info["is_24_hour"] = True
                vet_info["is_emergency_clinic"] = True
            if tags.get("emergency") == "yes":
                vet_info["is_emergency_clinic"] = True
            
            vets.append(vet_info)
        
        # Save all processed vets before filtering
        all_processed_vets = vets.copy()
        
        # Sort by distance, emergency clinics first if emergency_only
        if emergency_only:
            emergency_vets = [v for v in vets if v.get("is_emergency_clinic")]
            if emergency_vets:
                vets = emergency_vets
            else:
                # No emergency clinics found, return all PROCESSED vets (not raw elements!)
                vets = all_processed_vets
        
        vets.sort(key=lambda x: (not x.get("is_emergency_clinic", False), x.get("distance_km", 999)))
        vets = vets[:max_results]
        
        return {
            "success": True,
            "count": len(vets),
            "vets": vets,
            "search_location": {"lat": latitude, "lng": longitude},
            "search_radius_km": radius_meters / 1000,
            "data_source": "OpenStreetMap"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error searching for nearby vets.",
            "fallback": _get_mock_vet_data(latitude, longitude, emergency_only)
        }


def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula."""
    import math
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def _format_opening_hours(raw_hours: str) -> str:
    """Format OSM opening hours into readable format."""
    if not raw_hours:
        return "Hours: Call to confirm"
    
    # Check for 24/7
    if raw_hours == "24/7":
        return "🟢 Open 24/7"
    
    # Try to parse common formats
    raw_hours = raw_hours.strip()
    
    # If it looks like OSM format (Mo-Fr 08:00-18:00), try to simplify
    if "Mo" in raw_hours or "Tu" in raw_hours:
        # It's in OSM format, return as-is but cleaned up
        return f"Hours: {raw_hours}"
    
    # Default - just return what we have
    if raw_hours:
        return f"Hours: {raw_hours}"
    
    return "Hours: Call to confirm"


def _build_address(tags: dict) -> str:
    """Build address string from OSM tags."""
    parts = []
    
    if tags.get("addr:street"):
        street = tags.get("addr:street")
        if tags.get("addr:housenumber"):
            street = f"{tags.get('addr:housenumber')} {street}"
        parts.append(street)
    
    if tags.get("addr:city"):
        parts.append(tags.get("addr:city"))
    
    if tags.get("addr:postcode"):
        parts.append(tags.get("addr:postcode"))
    
    return ", ".join(parts) if parts else "Address not available"


def _get_mock_vet_data(latitude: float, longitude: float, emergency_only: bool) -> Dict[str, Any]:
    """
    Return mock vet data for testing when API is not available.
    
    NOTE FOR TEAM: Replace this with your own test data as needed.
    """
    mock_vets = [
        {
            "name": "City Emergency Animal Hospital",
            "address": "123 Main Street",
            "rating": 4.8,
            "total_reviews": 256,
            "is_open": True,
            "is_emergency_clinic": True,
            "phone": "(555) 123-4567",
            "hours": "24 hours"
        },
        {
            "name": "PetCare Veterinary Clinic",
            "address": "456 Oak Avenue",
            "rating": 4.6,
            "total_reviews": 189,
            "is_open": True,
            "is_emergency_clinic": False,
            "phone": "(555) 234-5678",
            "hours": "8 AM - 8 PM"
        },
        {
            "name": "Animal Wellness Center",
            "address": "789 Park Boulevard",
            "rating": 4.5,
            "total_reviews": 142,
            "is_open": True,
            "is_emergency_clinic": False,
            "phone": "(555) 345-6789",
            "hours": "9 AM - 6 PM"
        }
    ]
    
    if emergency_only:
        mock_vets = [v for v in mock_vets if v.get("is_emergency_clinic")]
    
    return {
        "success": True,
        "count": len(mock_vets),
        "vets": mock_vets,
        "note": "Using mock data - no real vets found nearby"
    }

# ============================================================
# Combined Triage Function
# ============================================================

def triage_and_recommend(
    symptoms: str,
    pet_species: str = None,
    pet_breed: str = None,
    user_latitude: float = None,
    user_longitude: float = None,
    current_time: datetime = None
) -> Dict[str, Any]:
    """
    Complete triage: check symptoms and recommend nearby vets if ER.
    
    This function combines check_red_flags and find_nearby_vets for a
    complete emergency triage workflow.
    
    IMPORTANT: find_nearby_vets is ONLY called when severity is ER
    (life-threatening emergency requiring immediate hospital visit).
    
    Args:
        symptoms: Description of pet's symptoms
        pet_species: 'dog' or 'cat'
        pet_breed: Pet's breed
        user_latitude: User's location latitude (required for vet search)
        user_longitude: User's location longitude (required for vet search)
        current_time: Current datetime (defaults to now if not provided)
    
    Returns:
        Combined result with severity assessment and nearby vet recommendations
    """
    # Get current time
    if current_time is None:
        current_time = datetime.now()
    
    # Step 1: Check symptoms for red flags (RULE-BASED, no LLM)
    red_flag_result = check_red_flags(symptoms, pet_species, pet_breed)
    
    result = {
        "triage": red_flag_result,
        "nearby_vets": None,
        "timestamp": current_time.isoformat(),
        "requires_location": False
    }
    
    # Step 2: ONLY search for nearby vets if severity is ER
    # ER = life-threatening, needs IMMEDIATE hospital visit
    if red_flag_result["severity"] == "ER":
        result["requires_location"] = True
        
        if user_latitude and user_longitude:
            # Search for emergency vets
            result["nearby_vets"] = find_nearby_vets(
                latitude=user_latitude,
                longitude=user_longitude,
                emergency_only=True,  # Prioritize 24-hour emergency clinics
                radius_meters=10000   # Search wider area for emergencies
            )
            result["message"] = "EMERGENCY: Please go to the nearest veterinary hospital immediately!"
        else:
            result["message"] = (
                "EMERGENCY: This appears to be a life-threatening situation. "
                "Please share your location so we can find the nearest emergency vet, "
                "or call your local emergency animal hospital immediately!"
            )
    elif red_flag_result["severity"] == "TODAY":
        result["message"] = (
            "This situation requires veterinary attention today. "
            "Please contact your regular veterinarian or an urgent care clinic."
        )
    
    return result


# ============================================================
# Tool: Web Search (Gemini 2.0 + Google Search Grounding)
# ============================================================
# Uses Gemini 2.0 with Google Search for real-time information.
# 
# Usage scenarios:
# - Get latest treatment information
# - Find recent research or news about pet health
# - Verify or supplement RAG information with current data

#
# The search is combined with LLM reasoning, so results are
# already processed and relevant to the query.

def web_search(
    query: str,
    context: str = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Perform real-time web search using Gemini 2.0 with Google Search Grounding.
    
    This function searches the web and uses Gemini to synthesize the results
    into a coherent, relevant answer.
    
    Args:
        query: The search query (e.g., "latest treatments for dog allergies")
        context: Optional context to help focus the search
        language: Response language ("en" for English, "zh" for Chinese)
    
    Returns:
        Dict with 'answer', 'sources', and 'success' status
    
    NOTE FOR TEAM:
    - Requires GOOGLE_API_KEY in .env
    - Uses Gemini 2.0 Flash model with Google Search grounding
    - Results are AI-processed, not raw search results
    """
    
    if not GOOGLE_API_KEY:
        return {
            "success": False,
            "error": "GOOGLE_API_KEY not configured",
            "message": "Please add GOOGLE_API_KEY to .env file. Get it from https://aistudio.google.com/app/apikey"
        }
    
    try:
        from google import genai
        from google.genai import types
        
        # Initialize client
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # Build the prompt
        if context:
            full_query = f"Context: {context}\n\nQuestion: {query}"
        else:
            full_query = query
        
        # Add language instruction
        if language == "zh":
            full_query += "\n\nPlease respond in Chinese."
        
        # System instruction for pet health focus
        system_instruction = """You are a pet health research assistant. 
When searching for information:
- Focus on veterinary and pet health sources
- Prioritize recent, reliable information
- Include specific details like treatment options, symptoms, and recommendations
- Cite sources when possible
- Note if information might be outdated or if a vet should be consulted"""
        
        # Call Gemini with Google Search grounding
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=full_query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.3  # Lower for more factual responses
            )
        )
        
        # Extract the response
        answer = response.text
        
        # Try to extract grounding sources if available
        sources = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata'):
                grounding = candidate.grounding_metadata
                if hasattr(grounding, 'grounding_chunks'):
                    for chunk in grounding.grounding_chunks[:5]:  # Limit to 5 sources
                        if hasattr(chunk, 'web'):
                            sources.append({
                                "title": getattr(chunk.web, 'title', 'Unknown'),
                                "uri": getattr(chunk.web, 'uri', '')
                            })
        
        return {
            "success": True,
            "answer": answer,
            "sources": sources,
            "model": "gemini-2.0-flash",
            "grounded": True
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "google-genai package not installed",
            "message": "Please install: pip install google-genai"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error performing web search"
        }


def search_and_combine(
    query: str,
    rag_context: str = None,
    pet_info: dict = None
) -> Dict[str, Any]:
    """
    Combine web search results with RAG context for comprehensive answers.
    
    This function:
    1. Performs web search for latest information
    2. Combines with RAG context (if provided)
    3. Returns a unified response
    
    Args:
        query: User's question
        rag_context: Context from RAG vector search (optional)
        pet_info: Pet information for personalized search
    
    Returns:
        Combined answer with both web and RAG sources
    """
    # Build search query with pet context
    search_query = query
    if pet_info:
        if pet_info.get("species"):
            search_query = f"{pet_info['species']} {search_query}"
        if pet_info.get("breed"):
            search_query = f"{pet_info['breed']} {search_query}"
    
    # Perform web search
    web_result = web_search(search_query, context=rag_context)
    
    result = {
        "web_search": web_result,
        "rag_context": rag_context,
        "combined_answer": None
    }
    
    # Combine answers if both sources are available
    if web_result.get("success") and rag_context:
        result["combined_answer"] = f"""## From Our Knowledge Base:
{rag_context}

## Latest Information from Web:
{web_result.get('answer', 'No web results available.')}
"""
    elif web_result.get("success"):
        result["combined_answer"] = web_result.get("answer")
    elif rag_context:
        result["combined_answer"] = rag_context
    
    return result


# ============================================================
# TRIAGE AGENT TOOLS (for structured output)
# ============================================================

def generate_triage_response(
    risk_level: str,
    category: str,
    red_flags: List[str] = None,
    reasoning: List[str] = None,
    actions: List[str] = None,
    monitoring: List[str] = None,
    sources: List[Dict] = None,
    follow_up_questions: List[str] = None
) -> Dict[str, Any]:
    """
    Generate a structured triage response in the required schema format.

    This tool formats the final triage response. The Agent should gather
    all information before calling this.

    Args:
        risk_level: "ER" | "TODAY" | "SOON" | "MONITOR"
        category: Symptom category
        red_flags: List of detected red flags
        reasoning: List of reasoning points (why this risk level)
        actions: List of recommended actions
        monitoring: List of things to watch for
        sources: List of RAG source references (optional)
        follow_up_questions: Questions if more info needed (optional)

    Returns:
        Dict with properly formatted TriageResponse
    """
    # Validate risk level
    valid_levels = ["ER", "TODAY", "SOON", "MONITOR"]
    if risk_level not in valid_levels:
        risk_level = "TODAY"  # Safe default

    # Ensure lists have content
    if not reasoning:
        reasoning = ["Professional evaluation recommended"]
    if not actions:
        actions = ["Monitor your pet and contact a veterinarian if concerned"]

    # Truncate long items (max 120 chars per item)
    def truncate(items, max_len=120):
        if not items:
            return []
        return [item[:max_len-3] + "..." if len(item) > max_len else item for item in items]

    response = {
        "risk_level": risk_level,
        "category": category,
        "red_flags": truncate(red_flags or [])[:5],
        "reasoning_summary": truncate(reasoning)[:3],
        "recommended_actions": truncate(actions)[:6],
        "what_to_monitor": truncate(monitoring or [])[:5],
        "follow_up_questions": truncate(follow_up_questions or [])[:2],
        "sources": (sources or [])[:3] if sources else None,
        "disclaimer": "This is not a veterinary diagnosis. If symptoms worsen or you're concerned, seek veterinary care immediately."
    }

    return response


def generate_triage_response_for_agent(input_json: str) -> str:
    """
    Agent-friendly wrapper for generate_triage_response.

    Args:
        input_json: JSON string with triage response fields

    Returns:
        JSON string with properly formatted TriageResponse
    """
    try:
        data = json.loads(input_json)
        result = generate_triage_response(
            risk_level=data.get("risk_level", "TODAY"),
            category=data.get("category", "Something Else"),
            red_flags=data.get("red_flags"),
            reasoning=data.get("reasoning"),
            actions=data.get("actions"),
            monitoring=data.get("monitoring"),
            sources=data.get("sources"),
            follow_up_questions=data.get("follow_up_questions")
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "risk_level": "TODAY",
            "category": "Something Else",
            "reasoning_summary": ["Unable to complete assessment"],
            "recommended_actions": ["Contact your veterinarian"],
            "disclaimer": "This is not a diagnosis. Seek veterinary care if concerned.",
            "_error": str(e)
        })


def request_followup_questions(missing_info: str) -> Dict[str, Any]:
    """
    Generate follow-up questions when critical information is missing.

    Use this when you need more information to make an accurate assessment.

    Args:
        missing_info: Description of what information is missing.
            E.g., "duration of symptoms, severity of vomiting"

    Returns:
        Dict with PENDING status and follow-up questions
    """
    missing_lower = missing_info.lower()
    questions = []

    # Map common missing info to questions
    question_map = {
        "duration": "How long has this been going on?",
        "frequency": "How often is this happening?",
        "blood": "Have you noticed any blood?",
        "appetite": "Is your pet still eating and drinking?",
        "energy": "Has your pet's energy level changed?",
        "vomiting": "How many times has your pet vomited?",
        "diarrhea": "What does the stool look like?",
        "pain": "Does your pet seem to be in pain?",
        "breathing": "Is there any difficulty breathing?",
        "behavior": "Has there been any change in behavior?",
        "eating": "When did your pet last eat?",
        "drinking": "Is your pet drinking water normally?",
        "urination": "Is your pet urinating normally?",
    }

    for keyword, question in question_map.items():
        if keyword in missing_lower and len(questions) < 3:
            questions.append(question)

    if not questions:
        questions = [
            "Can you describe the symptoms in more detail?",
            "When did you first notice these symptoms?"
        ]

    return {
        "status": "PENDING",
        "risk_level": "PENDING",
        "follow_up_questions": questions[:3],
        "reasoning_summary": ["Need more information to complete assessment"],
        "recommended_actions": ["Please answer the follow-up questions"],
        "what_to_monitor": [],
        "disclaimer": "Please answer the follow-up questions for accurate triage."
    }


def request_followup_for_agent(missing_info: str) -> str:
    """Agent-friendly wrapper for request_followup_questions."""
    try:
        result = request_followup_questions(missing_info)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "PENDING",
            "error": str(e),
            "follow_up_questions": ["Can you provide more details?"]
        })


def get_er_template(category: str) -> Dict[str, Any]:
    """
    Get the pre-built emergency template for a specific category.

    Use this when check_red_flags returns is_emergency=True.
    Returns a complete ER response without needing LLM.

    Args:
        category: The symptom category for the ER template

    Returns:
        Dict with complete ER triage response
    """
    # Import ER templates
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from llm_setup import ER_TEMPLATES
        template = ER_TEMPLATES.get(category, ER_TEMPLATES.get("Something Else", {}))
    except ImportError:
        template = {}

    # Default ER template if import fails
    if not template:
        template = {
            "risk_level": "ER",
            "category": category,
            "red_flags": ["Emergency condition detected"],
            "reasoning_summary": ["Symptoms indicate need for immediate care"],
            "recommended_actions": [
                "Go to emergency vet immediately",
                "Keep your pet calm and warm"
            ],
            "what_to_monitor": ["Overall condition", "Breathing"],
            "disclaimer": "This is not a diagnosis. Seek immediate veterinary care."
        }

    return {
        "risk_level": "ER",
        "category": template.get("category", category),
        "red_flags": template.get("red_flags", ["Emergency detected"]),
        "reasoning_summary": template.get("reasoning_summary", ["Immediate care required"]),
        "recommended_actions": template.get("recommended_actions", ["Go to emergency vet"]),
        "what_to_monitor": template.get("what_to_monitor", ["Overall condition"]),
        "follow_up_questions": [],
        "disclaimer": template.get("disclaimer", "Seek immediate veterinary care.")
    }


def get_er_template_for_agent(category: str) -> str:
    """Agent-friendly wrapper for get_er_template."""
    try:
        result = get_er_template(category)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "risk_level": "ER",
            "category": category,
            "red_flags": ["Emergency detected"],
            "reasoning_summary": ["Immediate care required"],
            "recommended_actions": ["Go to emergency vet immediately"],
            "disclaimer": "Seek immediate veterinary care.",
            "_error": str(e)
        })


# ============================================================
# CLI for Testing
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Pet Health AI - Tools Testing")
    print("=" * 60)
    
    # Test 1: Red flag check
    print("\n--- Test: check_red_flags ---")
    test_symptoms = "My dog has a bloated stomach and keeps trying to vomit but nothing comes out"
    result = check_red_flags(test_symptoms, pet_species="dog", pet_breed="Great Dane")
    print(f"Symptoms: {test_symptoms}")
    print(f"Severity: {result['severity']}")
    print(f"Action: {result['action']}")
    if result['breed_alerts']:
        print(f"Breed Alert: {result['breed_alerts'][0]['message']}")
    

    
    # Test 3: Find nearby vets (mock data)
    print("\n--- Test: find_nearby_vets ---")
    result = find_nearby_vets(latitude=37.7749, longitude=-122.4194)
    print(f"Found {result['count']} vets")
    for vet in result['vets'][:2]:
        print(f"  - {vet['name']} (Rating: {vet.get('rating', 'N/A')})")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
