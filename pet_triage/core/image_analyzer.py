"""
Pet Health AI - Image Analysis Module
====================================

This module handles image processing using OpenAI's GPT-4 Turbo with Vision.
It analyzes pet images to detect:
1. Visible symptoms (rashes, wounds, swelling)
2. Severity indicators
3. Breed characteristics (where relevant to health)

Usage:
    from image_analyzer import analyze_pet_image
    
    result = analyze_pet_image("path/to/image.jpg")
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# ============================================================
# Configuration
# ============================================================

VISION_MODEL = "gpt-4o"  # GPT-4o has vision capabilities

# ============================================================
# Image Analysis Prompt Configuration
# ============================================================
# NOTE FOR TEAM: This prompt controls how the AI analyzes pet images.
# Prompt Engineering team can modify this to:
# - Adjust what the AI looks for in images
# - Change the structure of the analysis output
# - Add/remove specific health indicators to check
# - Modify severity classification criteria
# - Change language and tone of responses
#
# Key sections in the prompt:
# - Pet Identification: What animal info to extract
# - Health Observations: What symptoms/conditions to look for
# - Health Assessment: How to classify severity
# - Recommendations: What advice to give
# ============================================================

IMAGE_ANALYSIS_PROMPT = """You are PetCare AI, a professional pet health advisor with image analysis capabilities.

Analyze this pet photo and provide a structured health assessment:

## CRITICAL - CHECK FOR EMERGENCY SIGNS FIRST:
Look carefully for ANY of these - if present, Risk Level MUST be ER:
⚠️ BLOOD - Any red/blood on fur, face, body, mouth, or around the pet
⚠️ WOUNDS - Open cuts, lacerations, punctures, bite marks
⚠️ TRAUMA - Signs of injury, swelling, deformity
⚠️ DISTRESS - Labored breathing, collapsed posture, unconscious
⚠️ PALE GUMS - White, blue, or very pale gum color

## 1. Pet Identification
- Species (dog/cat/other)
- Possible breed (if identifiable)

## 2. Visible Health Observations
LOOK CAREFULLY FOR:
- **BLOOD**: Any red staining, fresh or dried blood on fur, face, body, paws
- **Injuries**: Wounds, cuts, lacerations, punctures, bite marks
- **Swelling**: Abnormal lumps, distended areas, facial swelling
- **Skin condition**: Rashes, hot spots, hair loss, wounds, lumps
- **Eye condition**: Discharge, redness, cloudiness, swelling, injury
- **Posture**: Signs of pain, difficulty standing, collapsed

## 3. Health Assessment
RISK LEVEL - Choose one:
- **ER**: ANY blood visible, wounds, trauma, difficulty breathing, unconscious → ALWAYS ER!
- **TODAY**: Significant symptoms needing same-day vet visit
- **SOON**: Minor issues, vet visit within 24-48 hours
- **MONITOR**: No concerning signs

## 4. Recommendations
- For ER: "EMERGENCY - Seek immediate veterinary care NOW"
- Immediate actions
- When to seek care

## IMPORTANT:
- If you see RED COLOR on the pet that could be blood → ALWAYS classify as ER
- Do NOT underestimate injuries - when in doubt, err on the side of caution
- Blood on face, around mouth, on fur = EMERGENCY
- Ignore watermarks and background - focus on the pet

Provide your analysis in a clear, organized format."""


def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_media_type(image_path: str) -> str:
    """Determine the media type based on file extension."""
    extension = Path(image_path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    return media_types.get(extension, "image/jpeg")


def analyze_pet_image(
    image_source: str,
    user_question: str = None,
    openai_api_key: str = None
) -> Dict[str, Any]:
    """
    Analyze a pet image using GPT-4 Vision.
    
    Args:
        image_source: Path to local file or URL of the image
        user_question: Optional specific question about the image
        openai_api_key: OpenAI API key
    
    Returns:
        Dict containing analysis results (description, severity, recommendations)
    """
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    client = OpenAI(api_key=api_key)
    
    # Build the image content based on source type
    if image_source.startswith(("http://", "https://")):
        # URL-based image
        image_content = {
            "type": "image_url",
            "image_url": {"url": image_source}
        }
    else:
        # Local file - convert to base64
        if not os.path.exists(image_source):
            raise FileNotFoundError(f"Image file not found: {image_source}")
        
        base64_image = encode_image_to_base64(image_source)
        media_type = get_image_media_type(image_source)
        image_content = {
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{base64_image}"
            }
        }
    
    # Build message content
    content = [image_content]
    
    # Add user's question if provided
    if user_question:
        content.append({
            "type": "text",
            "text": f"User's question: {user_question}"
        })
    
    # Call GPT-4 Vision
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": IMAGE_ANALYSIS_PROMPT},
            {"role": "user", "content": content}
        ],
        max_tokens=1000,
        temperature=0.3  # Lower temperature for more consistent analysis
    )
    
    analysis = response.choices[0].message.content

    # Extract risk level from analysis (GPT outputs ER/TODAY/SOON/MONITOR)
    # Priority order: check most severe first
    if "ER" in analysis or "emergency" in analysis.lower():
        risk_level = "ER"
    elif "TODAY" in analysis:
        risk_level = "TODAY"
    elif "SOON" in analysis:
        risk_level = "SOON"
    else:
        risk_level = "MONITOR"

    return {
        "analysis": analysis,
        "risk_level": risk_level,  # Unified format: ER/TODAY/SOON/MONITOR
        "model": VISION_MODEL
    }


def analyze_with_context(
    image_source: str,
    user_question: str = None,
    pet_history: dict = None,
    openai_api_key: str = None
) -> dict:
    """
    Analyze image with additional pet history context.
    
    Args:
        image_source: File path or URL to the image
        user_question: User's question about the image
        pet_history: Optional dict with pet info (breed, age, known conditions)
        openai_api_key: OpenAI API key
    
    Returns:
        Analysis result dict
    """
    # Build context from pet history
    context_parts = []
    if pet_history:
        if pet_history.get("name"):
            context_parts.append(f"Pet name: {pet_history['name']}")
        if pet_history.get("species"):
            context_parts.append(f"Species: {pet_history['species']}")
        if pet_history.get("breed"):
            context_parts.append(f"Breed: {pet_history['breed']}")
        if pet_history.get("age"):
            context_parts.append(f"Age: {pet_history['age']}")
        if pet_history.get("known_conditions"):
            context_parts.append(f"Known conditions: {', '.join(pet_history['known_conditions'])}")
    
    # Combine context with user question
    full_question = ""
    if context_parts:
        full_question = "Pet information: " + "; ".join(context_parts) + "\n\n"
    if user_question:
        full_question += user_question
    
    return analyze_pet_image(
        image_source=image_source,
        user_question=full_question if full_question else None,
        openai_api_key=openai_api_key
    )


# ============================================================
# CLI for Testing
# ============================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("PetCare AI - Image Analyzer")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python image_analyzer.py <image_path_or_url> [question]")
        print("\nExamples:")
        print("  python image_analyzer.py ./pet_photo.jpg")
        print("  python image_analyzer.py ./pet_photo.jpg 'Is this rash serious?'")
        print("  python image_analyzer.py https://example.com/pet.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"\nAnalyzing image: {image_path}")
    if question:
        print(f"Question: {question}")
    print("-" * 60)
    
    try:
        result = analyze_pet_image(image_path, question)
        print(f"\nRisk Level: {result['risk_level']}")
        print(f"\n{result['analysis']}")
    except Exception as e:
        print(f"Error: {e}")
