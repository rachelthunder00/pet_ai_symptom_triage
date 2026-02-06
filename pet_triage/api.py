"""
Pet Triage API Server
=====================

FastAPI server that exposes the pet triage functionality as HTTP endpoints.
This enables the Next.js frontend to communicate with the Python AI backend.

Usage:
    uvicorn api:app --reload --port 8000

Endpoints:
    POST /api/triage     - Main triage assessment
    POST /api/chat       - Conversational follow-up
    GET  /api/health     - Health check
    GET  /api/categories - Get supported symptom categories
"""

import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from our modules
from main import run_triage, run_triage_agent
from shared.constants import SUPPORTED_CATEGORIES, SUPPORTED_SPECIES
from shared.schemas import TriageResponse, get_fallback_response
from core.tools import find_nearby_vets
from auth import (
    UserRegister, UserLogin, AuthResponse,
    register_user, login_user, get_current_user, verify_token
)
from database import (
    create_or_update_pet_profile,
    get_pet_profile,
    save_triage_session,
    get_triage_sessions,
    get_triage_session_by_id
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# FastAPI App Setup
# =============================================================================

app = FastAPI(
    title="Fuzzy Friend - Pet Triage API",
    description="AI-powered pet symptom assessment and triage guidance",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS configuration - allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev server
        "http://127.0.0.1:3000",
         "http://localhost:3003",
         "http://127.0.0.1:3003",
        "https://localhost:3000",
        # Add production domains here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================

class PetProfile(BaseModel):
    """Pet profile information."""
    name: Optional[str] = None
    species: str = Field(..., description="Pet species: 'dog' or 'cat'")
    breed: Optional[str] = None
    age: Optional[str] = None
    weight: Optional[str] = None
    sex: Optional[str] = None
    known_conditions: Optional[List[str]] = None


class TriageRequest(BaseModel):
    """Request payload for triage assessment."""
    species: str = Field(..., description="Pet species: 'dog' or 'cat'")
    category: str = Field(..., description="Symptom category")
    structured_fields: Dict[str, Any] = Field(default_factory=dict, description="UI form fields")
    user_description: str = Field(default="", max_length=1500, description="Free text symptom description")
    pet_profile: Optional[PetProfile] = None
    
    # Optional image (base64 encoded)
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded pet image")
    image_type: Optional[str] = Field(default=None, description="Image MIME type (image/jpeg, image/png)")
    
    # Optional location for vet finder
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class ChatMessage(BaseModel):
    """Chat message for conversational follow-up."""
    message: str = Field(..., max_length=1000)
    session_id: Optional[str] = None
    pet_context: Optional[Dict[str, Any]] = None
    # Optional image for analysis
    image_base64: Optional[str] = None
    image_type: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []  # New field for conversation history


class APIResponse(BaseModel):
    """Unified API response wrapper."""
    success: bool
    trace_id: str
    timestamp: str
    processing_time_ms: int
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    is_er: bool = False


# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "pet-triage-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# =============================================================================
# Authentication Endpoints
# =============================================================================

@app.post("/api/auth/register", response_model=AuthResponse)
async def auth_register(request: UserRegister):
    """
    Register a new user.
    
    Returns JWT token (no expiry) on success.
    """
    result = register_user(
        name=request.name,
        email=request.email,
        password=request.password
    )
    return result


@app.post("/api/auth/login", response_model=AuthResponse)
async def auth_login(request: UserLogin):
    """
    Login with email and password.
    
    Returns JWT token (no expiry) on success.
    """
    result = login_user(
        email=request.email,
        password=request.password
    )
    return result


@app.get("/api/auth/me")
async def auth_me(request: Request):
    """
    Get current user from Authorization header.
    
    Expects: Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"success": False, "error": "No token provided"}
    
    token = auth_header.replace("Bearer ", "")
    user = get_current_user(token)
    
    if not user:
        return {"success": False, "error": "Invalid token"}
    
    # Also get pet profile
    pet_profile = get_pet_profile(user.id) if user else None
    return {"success": True, "user": user, "pet_profile": pet_profile}


# =============================================================================
# Pet Profile Endpoints
# =============================================================================

class PetProfileRequest(BaseModel):
    """Pet profile save request."""
    name: str
    species: str
    breed: Optional[str] = None
    age_years: Optional[int] = None
    weight: Optional[float] = None
    weight_unit: str = "kg"
    sex: Optional[str] = None
    spay_neuter_status: Optional[str] = None
    last_heat_cycle: Optional[str] = None
    vaccination_status: Optional[str] = None
    lifestyle: Optional[str] = None
    allergies: Optional[str] = None
    medical_history_flags: Optional[List[str]] = None


def get_user_id_from_token(request: Request) -> Optional[str]:
    """Extract user ID from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    return payload.get("sub") if payload else None


@app.post("/api/pet-profile")
async def save_pet_profile(request: Request, profile: PetProfileRequest):
    """
    Save or update pet profile for the authenticated user.
    """
    user_id = get_user_id_from_token(request)
    if not user_id:
        return {"success": False, "error": "Authentication required"}
    
    try:
        saved_profile = create_or_update_pet_profile(
            user_id=user_id,
            name=profile.name,
            species=profile.species,
            breed=profile.breed,
            age_years=profile.age_years,
            weight=profile.weight,
            weight_unit=profile.weight_unit,
            sex=profile.sex,
            spay_neuter_status=profile.spay_neuter_status,
            last_heat_cycle=profile.last_heat_cycle,
            vaccination_status=profile.vaccination_status,
            lifestyle=profile.lifestyle,
            allergies=profile.allergies,
            medical_history_flags=profile.medical_history_flags
        )
        return {"success": True, "profile": saved_profile}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/pet-profile")
async def get_pet_profile_endpoint(request: Request):
    """
    Get pet profile for the authenticated user.
    """
    user_id = get_user_id_from_token(request)
    if not user_id:
        return {"success": False, "error": "Authentication required"}
    
    profile = get_pet_profile(user_id)
    if profile:
        return {"success": True, "profile": profile}
    else:
        return {"success": True, "profile": None, "message": "No pet profile found"}


# =============================================================================
# Categories Endpoint
# =============================================================================

@app.get("/api/categories")
async def get_categories():
    """Get supported symptom categories."""
    return {
        "categories": SUPPORTED_CATEGORIES,
        "species": SUPPORTED_SPECIES
    }


# =============================================================================
# Nearby Vets Endpoint
# =============================================================================

class NearbyVetsRequest(BaseModel):
    """Request model for nearby vets search."""
    latitude: float = Field(..., description="User's latitude")
    longitude: float = Field(..., description="User's longitude")
    radius_meters: int = Field(default=5000, description="Search radius in meters")
    max_results: int = Field(default=5, description="Maximum number of results")

@app.post("/api/nearby-vets")
async def get_nearby_vets(request: NearbyVetsRequest):
    """
    Get nearby veterinary clinics based on location.
    Uses OpenStreetMap Overpass API (free, no API key needed).
    """
    try:
        result = find_nearby_vets(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "count": result.get("count", 0),
            "vets": result.get("vets", []),
            "search_radius_km": request.radius_meters / 1000
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "vets": []
        }


# =============================================================================
# Main Triage Endpoint
# =============================================================================

@app.post("/api/triage", response_model=APIResponse)
async def triage_assessment(request: TriageRequest, http_request: Request):
    """
    Main triage assessment endpoint.
    
    Accepts symptom information and returns urgency assessment with recommendations.
    """
    trace_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        # Validate species
        if request.species.lower() not in ["dog", "cat"]:
            return APIResponse(
                success=False,
                trace_id=trace_id,
                timestamp=datetime.utcnow().isoformat(),
                processing_time_ms=int((time.time() - start_time) * 1000),
                error_code="INVALID_SPECIES",
                error_message="Only dogs and cats are supported"
            )
        
        # Validate category (allow "auto" for AI-inferred category)
        category = request.category
        if category == "auto":
            # AI will infer category from user description
            category = "Something Else"  # Default fallback, agent will determine actual category
        elif category not in SUPPORTED_CATEGORIES:
            return APIResponse(
                success=False,
                trace_id=trace_id,
                timestamp=datetime.utcnow().isoformat(),
                processing_time_ms=int((time.time() - start_time) * 1000),
                error_code="INVALID_CATEGORY",
                error_message=f"Invalid category. Supported: {SUPPORTED_CATEGORIES}"
            )
        
        # Build pet profile dict
        pet_profile = None
        if request.pet_profile:
            pet_profile = {
                "name": request.pet_profile.name,
                "species": request.pet_profile.species,
                "breed": request.pet_profile.breed,
                "age": request.pet_profile.age,
                "weight": request.pet_profile.weight,
                "sex": request.pet_profile.sex,
            }
        
        # Get user ID and fetch history if authenticated
        user_id = get_user_id_from_token(http_request)
        triage_history = []
        if user_id:
            try:
                triage_history = get_triage_sessions(user_id, limit=5)
            except Exception as e:
                print(f"Failed to fetch triage history: {e}")

        # Run triage
        result = run_triage(
            species=request.species.lower(),
            category=category,
            structured_fields=request.structured_fields,
            user_description=request.user_description,
            pet_profile=pet_profile,
            image_base64=request.image_base64,
            image_type=request.image_type,
            latitude=request.latitude,
            longitude=request.longitude,
            triage_history=triage_history,  # Pass history
            verbose=False  # Disable verbose logging for API
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        if result.get("success"):
            # Save triage session to database (if user is authenticated)
            user_id = get_user_id_from_token(http_request)
            try:
                import json
                response_data = result.get("response", {})
                save_triage_session(
                    session_id=trace_id,
                    species=request.species,
                    category=category,
                    user_description=request.user_description[:500] if request.user_description else None,
                    risk_level=response_data.get("risk_level"),
                    response_json=json.dumps(response_data),
                    user_id=user_id
                )
            except Exception as save_err:
                print(f"Failed to save triage session: {save_err}")
            
            return APIResponse(
                success=True,
                trace_id=trace_id,
                timestamp=datetime.utcnow().isoformat(),
                processing_time_ms=processing_time,
                data={
                    **result.get("response", {}),
                    "tools_used": result.get("tools_used", []),
                    "model_used": result.get("model_used", "unknown"),
                    "rag_source_count": result.get("rag_source_count", 0),
                    "used_web_search": result.get("used_web_search", False)
                },
                warnings=result.get("warnings", []),
                is_er=result.get("is_er", False)
            )
        else:
            # Check if this is a guardrail rejection (off-topic, wrong species, etc.)
            if result.get("guardrail_rejected"):
                # Return the rejection message directly to the user
                return APIResponse(
                    success=False,
                    trace_id=trace_id,
                    timestamp=datetime.utcnow().isoformat(),
                    processing_time_ms=processing_time,
                    error_code="GUARDRAIL_REJECTED",
                    error_message=result.get("error", "Request rejected by input guardrails"),
                    is_er=False
                )

            # Triage failed for other reasons, return fallback
            fallback = get_fallback_response(result.get("error"))
            return APIResponse(
                success=True,  # Still return success with fallback
                trace_id=trace_id,
                timestamp=datetime.utcnow().isoformat(),
                processing_time_ms=processing_time,
                data=fallback.model_dump(),
                warnings=["Using fallback response: " + str(result.get("error", "Unknown error"))],
                is_er=False
            )
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        # Return safe fallback on any error
        fallback = get_fallback_response(str(e))
        return APIResponse(
            success=True,  # Return success with fallback to not break app
            trace_id=trace_id,
            timestamp=datetime.utcnow().isoformat(),
            processing_time_ms=processing_time,
            data=fallback.model_dump(),
            warnings=[f"Error occurred, using fallback: {str(e)}"],
            is_er=False
        )


# =============================================================================
# Triage History Endpoints
# =============================================================================

@app.get("/api/triage/history")
async def get_triage_history(request: Request, limit: int = 20):
    """
    Get triage history for the authenticated user.
    
    Returns list of past triage sessions (most recent first).
    """
    user_id = get_user_id_from_token(request)
    if not user_id:
        return {"success": False, "error": "Authentication required", "sessions": []}
    
    sessions = get_triage_sessions(user_id, limit=limit)
    return {
        "success": True,
        "sessions": sessions,
        "count": len(sessions)
    }


@app.get("/api/triage/{session_id}")
async def get_triage_detail(session_id: str, request: Request):
    """
    Get details of a specific triage session.
    
    Returns full session data including the complete response.
    """
    session = get_triage_session_by_id(session_id)
    
    if not session:
        return {"success": False, "error": "Session not found"}
    
    # Check ownership if user is logged in
    user_id = get_user_id_from_token(request)
    if session.get("user_id") and session.get("user_id") != user_id:
        return {"success": False, "error": "Access denied"}
    
    return {
        "success": True,
        "session": session
    }


# =============================================================================
# Chat Endpoint (Conversational Follow-up)
# =============================================================================

@app.post("/api/chat")
async def chat_followup(request: ChatMessage):
    """
    Conversational follow-up endpoint for general pet health questions.
    
    This uses the PetHealthAgent for open-ended Q&A (not structured triage).
    """
    trace_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        # Import agent here to avoid circular imports
        from core.agent import PetHealthAgent
        
        # Create agent instance
        agent = PetHealthAgent(
            model="gpt-4o-mini",  # Fast model
            temperature=0.5,
            verbose=False
        )
        
        # Build context from pet info
        pet_ctx = request.pet_context or {}
        
        # Build comprehensive pet profile string
        pet_profile_str = ""
        if pet_ctx:
            profile_parts = []
            if pet_ctx.get("name"):
                profile_parts.append(f"Name: {pet_ctx['name']}")
            if pet_ctx.get("species"):
                profile_parts.append(f"Species: {pet_ctx['species']}")
            if pet_ctx.get("breed"):
                profile_parts.append(f"Breed: {pet_ctx['breed']}")
            if pet_ctx.get("age_years"):
                profile_parts.append(f"Age: {pet_ctx['age_years']} years")
            if pet_ctx.get("weight"):
                unit = pet_ctx.get("weight_unit", "kg")
                profile_parts.append(f"Weight: {pet_ctx['weight']} {unit}")
            if profile_parts:
                pet_profile_str = " | ".join(profile_parts)
        
        # For questions about "my dog/pet", include profile directly in message
        user_msg = request.message
        msg_lower = user_msg.lower()
        
        # Check if user is asking about their own pet
        asking_about_own_pet = any(phrase in msg_lower for phrase in [
            "my dog", "my pet", "my cat", "about my", "tell me about", 
            "what is my", "what's my", "whats my", "who is my"
        ])
        
        # Prepend pet profile context if available and relevant
        if pet_profile_str and asking_about_own_pet:
            user_msg = f"[User's Pet Profile: {pet_profile_str}]\n\nQuestion: {user_msg}"
        elif pet_profile_str:
            user_msg = f"[User's Pet: {pet_profile_str}]\n\nQuestion: {user_msg}"
        
        context = {}
        if pet_profile_str:
            context["pet_info"] = pet_profile_str
        
        # Handle image if provided
        image_analysis = None
        if request.image_base64:
            try:
                from core.image_analyzer import analyze_pet_image
                import tempfile
                import base64
                
                # Save base64 to temp file
                image_data = base64.b64decode(request.image_base64)
                suffix = ".jpg" if request.image_type == "image/jpeg" else ".png"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                    f.write(image_data)
                    temp_path = f.name
                
                # Analyze image
                image_result = analyze_pet_image(temp_path, user_question=request.message)
                image_analysis = image_result.get("description", "")
                
                # Add image analysis to user message
                user_msg = f"[Image Analysis: {image_analysis}]\n\n{user_msg}"
                
                # Clean up temp file
                import os
                os.unlink(temp_path)
            except Exception as e:
                print(f"Image analysis failed: {e}")
        
        # Run chat
        result = agent.chat(user_msg, context=context, history=request.history)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Build tools list
        tools_used = [
            tc.get("name", "unknown") if isinstance(tc, dict) else str(tc)
            for tc in result.get("intermediate_steps", [])
        ]
        if image_analysis:
            tools_used.insert(0, "analyze_image")
        
        return {
            "success": True,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time_ms": processing_time,
            "response": result.get("output", ""),
            "tools_used": tools_used
        }
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time_ms": processing_time,
            "error": str(e),
            "response": "I apologize, but I encountered an error. Please try again or consult your veterinarian if you have urgent concerns."
        }


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure API never crashes."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "error_message": "An internal error occurred. Please try again.",
            "trace_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# =============================================================================
# Run Server (for development)
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting Pet Triage API server...")
    print("Docs available at: http://localhost:8000/api/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
