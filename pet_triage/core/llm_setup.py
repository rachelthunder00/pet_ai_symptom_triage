# ============================================================================
# File 2: task1_llm_setup.py - Task 3.1 LLM Selection & API Setup
# ============================================================================
"""
Task 3.1: LLM Selection & API Setup

This file handles:
1. OpenAI API connection setup
2. Model routing logic (which model to use)
3. Emergency hard-routing (ER cases return template directly, skip LLM)

According to the document architecture:
- gpt-4o-mini: Low-cost intake layer for classification and info extraction
- gpt-4.1-mini: Main triage engine
- gpt-4.1: Fallback model

NOTE: Red flag rules have been consolidated into shared/red_flags.py.
This file now imports from the shared module for consistency.
"""

import os
import logging
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from ratelimit import limits, sleep_and_retry

# Import from shared module (single source of truth)
from shared.constants import (
    MODEL_CONFIG,
    SUPPORTED_CATEGORIES,
    RiskLevel,
    DEFAULT_DISCLAIMER,
    TIMEOUT_CONFIG,
    RATE_LIMIT_CONFIG,
)

# Set up logger for retry logging
logger = logging.getLogger(__name__)

# Rate limit constants (extracted for decorator use)
LLM_CALLS_PER_MINUTE = RATE_LIMIT_CONFIG["llm_calls_per_minute"]
IMAGE_CALLS_PER_MINUTE = RATE_LIMIT_CONFIG["image_calls_per_minute"]
from shared.red_flags import (
    check_immediate_er,
    EMERGENCY_GUM_COLORS,
    DANGEROUS_SUBSTANCES,
    BLOAT_RISK_BREEDS,
)

# Load environment variables
load_dotenv()

# ============================================================================
# Part 1: API Client Initialization
# ============================================================================

def get_openai_client() -> OpenAI:
    """
    Get OpenAI client
    
    Setup:
    1. Create .env file in project root
    2. Add: OPENAI_API_KEY=sk-your-key-here
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found!\n"
            "Please create a .env file in project root with:\n"
            "OPENAI_API_KEY=sk-your-api-key"
        )
    
    return OpenAI(api_key=api_key)


# ============================================================================
# Part 2: ER Template Library (Hard-coded, no LLM needed)
# ============================================================================

ER_TEMPLATES = {
    "Toxic Ingestion & Poisoning": {
        "risk_level": "ER",
        "category": "Toxic Ingestion & Poisoning",
        "red_flags": ["Possible poisoning or airway blockage"],
        "reasoning_summary": ["Toxic substance ingestion can be life-threatening", "Requires immediate professional treatment"],
        "recommended_actions": [
            "Go to an emergency vet now",
            "Do not force vomiting unless a vet instructs you",
            "Bring any packaging or details of what was eaten"
        ],
        "what_to_monitor": ["Breathing status", "Consciousness", "Seizure activity"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    },

    "Stomach Upset": {
        "risk_level": "ER",
        "category": "Stomach Upset",
        "red_flags": ["High-risk vomiting/diarrhea/bloat symptoms"],
        "reasoning_summary": ["Possible gastric dilatation-volvulus (GDV)", "Can lead to shock or death"],
        "recommended_actions": [
            "Go to an emergency vet immediately",
            "Avoid food and water unless a vet tells you otherwise",
            "Keep your pet calm and still"
        ],
        "what_to_monitor": ["Abdomen distension", "Ability to lie down", "Gum color"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    },

    "Itching & Skin Issues": {
        "risk_level": "ER",
        "category": "Itching & Skin Issues",
        "red_flags": ["Possible severe allergic reaction"],
        "reasoning_summary": ["Rapid swelling can affect breathing", "Systemic symptoms can worsen quickly"],
        "recommended_actions": [
            "Go to an emergency vet now",
            "Do not apply random human creams or medications",
            "Watch for breathing changes"
        ],
        "what_to_monitor": ["Facial/throat swelling", "Breathing changes", "Mental status"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    },

    "Injury & Bleeding": {
        "risk_level": "ER",
        "category": "Injury & Bleeding",
        "red_flags": ["Bleeding or serious wound risk"],
        "reasoning_summary": ["Excessive blood loss can be life-threatening", "Deep wounds risk infection"],
        "recommended_actions": [
            "Apply firm pressure with a clean cloth and keep pressure on",
            "Go to an emergency vet now",
            "Keep movement minimal during transport"
        ],
        "what_to_monitor": ["Bleeding reduction", "Gum color", "Consciousness"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    },

    "Concerning Behaviour Changes": {
        "risk_level": "ER",
        "category": "Concerning Behaviour Changes",
        "red_flags": ["Severe neurological or systemic symptoms"],
        "reasoning_summary": ["Seizures or collapse require urgent care", "Could indicate poisoning or serious illness"],
        "recommended_actions": [
            "Go to an emergency vet now",
            "Keep the area safe",
            "Track timing if a seizure is happening"
        ],
        "what_to_monitor": ["Seizure duration", "Number of episodes", "Recovery status"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    },

    "Ears, Eyes, and Mouth": {
        "risk_level": "ER",
        "category": "Ears, Eyes, and Mouth",
        "red_flags": ["Eye or facial emergency"],
        "reasoning_summary": ["Serious eye issues can worsen rapidly", "Can cause permanent damage"],
        "recommended_actions": [
            "Go to an emergency vet immediately",
            "Prevent rubbing (use a cone if available)",
            "Do not attempt to treat the eye yourself"
        ],
        "what_to_monitor": ["Eye size changes", "Discharge", "Vision"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    },

    "Breathing Issues": {
        "risk_level": "ER",
        "category": "Breathing Issues",
        "red_flags": ["Breathing distress detected"],
        "reasoning_summary": ["Breathing trouble is life-threatening", "Can worsen rapidly"],
        "recommended_actions": [
            "Go to an emergency vet now",
            "Keep your pet calm",
            "Do not force them to lie down"
        ],
        "what_to_monitor": ["Breathing rate", "Gum color", "Open-mouth breathing"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    },

    "Urinary & Genital": {
        "risk_level": "ER",
        "category": "Urinary & Genital",
        "red_flags": ["Possible urinary blockage"],
        "reasoning_summary": ["Urinary blockage can be fatal quickly, especially in male cats", "Can cause death within 24-48 hours"],
        "recommended_actions": [
            "Go to an emergency vet now",
            "Do not press the belly",
            "Note the last time urine was produced"
        ],
        "what_to_monitor": ["Any urine production", "Mental status", "Vomiting"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    },

    "Something Else": {
        "risk_level": "ER",
        "category": "Something Else",
        "red_flags": ["High-risk signs detected"],
        "reasoning_summary": ["Symptoms may indicate a serious condition", "Professional evaluation needed"],
        "recommended_actions": [
            "Go to an emergency vet now",
            "Keep warm and quiet",
            "Transport immediately"
        ],
        "what_to_monitor": ["Overall status", "Breathing", "Consciousness"],
        "follow_up_questions": [],
        "disclaimer": "This is not a diagnosis. If symptoms worsen, seek immediate care."
    }
}


# ============================================================================
# Part 3: Emergency Rules Engine (Runs before LLM)
# ============================================================================

def check_immediate_er_rules(structured_fields: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Check if immediate ER rules are triggered.

    This function delegates to the shared module's check_immediate_er() function
    to maintain a single source of truth for emergency detection rules.

    This is the core design from the document:
    "If any Immediate ER red flag is triggered from structured fields
     → risk_level = ER
     → Return category-specific ER template
     → End"

    Args:
        structured_fields: Structured fields collected from UI

    Returns:
        (is_er_triggered, triggered_category)
    """
    # Delegate to shared module and convert dict to tuple
    result = check_immediate_er(structured_fields)
    return (result["is_er"], result.get("category"))


def get_er_template(category: str) -> Dict[str, Any]:
    """
    Get ER template for specified category
    
    Args:
        category: Symptom category
        
    Returns:
        ER template dictionary
    """
    return ER_TEMPLATES.get(category, ER_TEMPLATES["Something Else"])


# ============================================================================
# Part 4: Model Router
# ============================================================================

def select_model(
    is_simple_case: bool = False,
    needs_fallback: bool = False,
    has_image: bool = False
) -> str:
    """
    Select which model to use based on the situation

    Document routing logic:
    - Simple low-risk cases → gpt-4o-mini
    - Main triage → gpt-4.1-mini
    - Uncertain/complex cases → gpt-4.1

    Args:
        is_simple_case: Whether it's a simple case
        needs_fallback: Whether fallback model is needed
        has_image: Whether there's an image to analyze

    Returns:
        Model name string
    """
    if needs_fallback:
        return MODEL_CONFIG["fallback"]  # gpt-4.1

    if is_simple_case:
        return MODEL_CONFIG["intake"]    # gpt-4o-mini

    # Default to main triage model
    return MODEL_CONFIG["triage"]        # gpt-4.1-mini


# ============================================================================
# Part 5: API Call Wrappers
# ============================================================================

@sleep_and_retry
@limits(calls=LLM_CALLS_PER_MINUTE, period=60)
@retry(
    retry=retry_if_exception_type((APIError, APIConnectionError, RateLimitError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(
        multiplier=TIMEOUT_CONFIG["llm_retry_backoff"],
        min=1,
        max=10
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def call_llm(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.3,
    max_tokens: int = 1000,
    json_mode: bool = True
) -> str:
    """
    Unified LLM call function with automatic retry on transient failures.

    Retry behavior:
    - Max 3 attempts
    - Exponential backoff: 1s → 2s → 4s (max 10s)
    - Retries on: APIError, APIConnectionError, RateLimitError

    Args:
        client: OpenAI client
        model: Model name
        system_prompt: System prompt
        user_message: User message
        temperature: Temperature (0.3 is conservative for medical)
        max_tokens: Max tokens
        json_mode: Whether to force JSON output

    Returns:
        Model response text
    """
    request_params = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": TIMEOUT_CONFIG["llm_call"]
    }

    if json_mode:
        request_params["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**request_params)

    return response.choices[0].message.content


@sleep_and_retry
@limits(calls=IMAGE_CALLS_PER_MINUTE, period=60)
@retry(
    retry=retry_if_exception_type((APIError, APIConnectionError, RateLimitError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(
        multiplier=TIMEOUT_CONFIG["llm_retry_backoff"],
        min=1,
        max=10
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def call_llm_with_image(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_message: str,
    image_base64: str,
    image_type: str = "image/jpeg",
    temperature: float = 0.3,
    max_tokens: int = 1000
) -> str:
    """
    LLM call with image, with automatic retry on transient failures.

    Retry behavior:
    - Max 3 attempts
    - Exponential backoff: 1s → 2s → 4s (max 10s)
    - Retries on: APIError, APIConnectionError, RateLimitError

    Args:
        client: OpenAI client
        model: Model name (must support vision, e.g., gpt-4o)
        system_prompt: System prompt
        user_message: User message
        image_base64: Base64 encoded image
        image_type: Image MIME type
        temperature: Temperature
        max_tokens: Max tokens

    Returns:
        Model response text
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_type};base64,{image_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=TIMEOUT_CONFIG["image_analysis"]
    )

    return response.choices[0].message.content


