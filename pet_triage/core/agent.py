"""
Pet Health AI - Agent Implementation
==============================

This module implements the autonomous agent using LangChain.
It orchestrates tool usage based on user input and context.

Key Features:
- Autonomous tool selection based on reasoning
- Multi-step execution (e.g., triage -> search -> recommendation)
- Context-aware processing (symptom categories, pet profiles)

Usage:
    from agent import PetHealthAgent
    
    agent = PetHealthAgent()
    result = agent.chat("My dog is vomiting", context={"pet_info": ...})
    print(result["output"])
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangChain imports (updated for LangChain 1.2.x / LangGraph)
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

# Import existing tools (NO modifications to original files!)
# Use aliases to avoid naming conflicts with @tool decorated functions
from .rag_chain import ask_simple, ask_with_image, get_chain
from .tools import (
    check_red_flags as _check_red_flags_func,
    check_red_flags_for_agent,
    find_nearby_vets as _find_nearby_vets_func,
    triage_and_recommend,
    web_search as _web_search_func,
    # New triage tools
    generate_triage_response as _generate_triage_response_func,
    generate_triage_response_for_agent,
    request_followup_questions as _request_followup_questions_func,
    request_followup_for_agent,
    get_er_template as _get_er_template_func,
    get_er_template_for_agent,
)
from .image_analyzer import analyze_pet_image

# Get API key from environment (avoid config import conflicts)
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ============================================================
# Agent System Prompt
# ============================================================

AGENT_SYSTEM_PROMPT = """You are a Pet Health AI Assistant with access to specialized tools.

## Role
You help pet owners understand their pet's health concerns by:
1. Analyzing symptoms and questions
2. Searching medical knowledge databases
3. Detecting emergencies
4. Finding veterinary care when needed
5. Providing evidence-based guidance

## Symptom Category Information
Users may select a symptom category from the interface before describing their concern.
When a category is provided, use it to focus your analysis:
- Toxic Ingestion & Poisoning: Ate toxic substances, poisoning symptoms, toxic plants
- Stomach Upset: Vomiting, diarrhea, appetite changes, abdominal issues
- Itching & Skin Issues: Rashes, itching, hair loss, wounds, lumps, skin abnormalities
- Injury & Bleeding: Physical injuries, cuts, wounds, bleeding, trauma
- Concerning Behaviour Changes: Lethargy, aggression, anxiety, sleep changes, unusual behavior
- Ears, Eyes, and Mouth: Eye discharge, ear infections, dental issues, vision/hearing problems
- Breathing Issues: Coughing, breathing difficulty, respiratory distress, nasal discharge
- Urinary & Genital: Urination changes, accidents, straining, genital issues
- Something Else: General health questions or symptoms not covered above

Use the category to prioritize relevant search terms and tailor your response.


## Available Tools

### Knowledge & Search
- vector_search: Search the pet health knowledge database (18,909 records)
  - Use for: medical questions, conditions, treatments, breed info
  - This is your PRIMARY knowledge source

- web_search_tool: Search the web for current information using Google
  - USE when: Information might have changed recently OR user wants current/updated info
  - Good for: evolving research, treatment advances, product recommendations, news
  - NOT needed for: basic anatomy, established conditions, breed characteristics
  - When in doubt about currency of information, use web search to supplement RAG

### Emergency & Safety
- check_red_flags: Check symptoms for emergency indicators (rule-based)
  - Use for: ANY symptom description
  - ALWAYS use this FIRST when symptoms are mentioned
  - Returns risk_level: ER/TODAY/SOON/MONITOR

- find_nearby_vets: Find veterinary clinics near user location
  - Use when: ER/TODAY risk level, or user asks for vet recommendations
  - Requires: latitude and longitude

- emergency_triage: Combined check + vet finder
  - Use when: User provides symptoms AND location
  - More efficient than calling tools separately

### Pet Information
- Pet Context: Pet profile (breed, age, conditions) is provided in the context directly.

### Image Analysis
- analyze_image: Analyze pet photos with GPT-4 Vision
  - Use when: User provides an image path or URL
  - Input: path or URL to the image
  - Returns: visual observations, severity assessment, recommendations
  - ALWAYS use this when an image is provided

## Decision Making Strategy

### Step 1: Assess the Situation
- Is there an IMAGE? -> Use analyze_image FIRST
- Are there SYMPTOMS? -> Use check_red_flags FIRST
- Is there a SYMPTOM CATEGORY? -> Use it to refine your searches
- Is it a MEDICAL QUESTION? -> Use vector_search
- Could info be outdated or evolving? -> Also use web_search_tool
- Asking about treatments, research, or recommendations? -> Consider web_search_tool

### Step 2: Check Risk Level
- If ER -> find_nearby_vets immediately (emergency)
- If TODAY -> recommend vet visit today + provide info
- If SOON/MONITOR -> provide information and guidance

### Step 3: Provide Complete Answer
- Combine information from multiple tools if needed
- Reference the symptom category if provided
- Always cite sources
- Be clear about when to see a vet

## Important Rules

1. Safety First: ALWAYS check_red_flags for symptoms before giving advice
2. Use Images: ALWAYS analyze_image when image is provided
3. Knowledge Sources: 
   - Use vector_search for medical knowledge
   - ALSO use web_search_tool for: treatments, medications, products, research, diet recommendations
   - Treatments and research evolve - web search provides current info
4. Leverage Category: Use symptom category to focus analysis
5. Be Direct: For emergencies, immediately find vets
6. Cite Sources: Mention which tool provided information
7. Know Limits: You're not a veterinarian - recommend professional care when appropriate

## SCOPE RESTRICTIONS (CRITICAL)

8. ONLY Dogs and Cats: You can ONLY answer questions about dogs and cats. 
   - If the user asks about OTHER animals (birds, reptiles, hamsters, horses, fish, etc.), politely respond:
     "I'm sorry, I can only help with dogs and cats at this time. For [animal type] health concerns, please consult a veterinarian who specializes in exotic or [animal type] care."
   - If the user asks about NON-PET topics (weather, cooking, math, general knowledge, etc.), respond:
     "I'm a pet health assistant specialized in dogs and cats. I can only help with pet health-related questions. How can I help with your dog or cat today?"

9. Image-Only Requests: When the user provides ONLY an image with no text description:
   - FIRST analyze the image using analyze_image
   - THEN ask 1-2 brief follow-up questions to better understand the concern, such as:
     - "I can see your pet in the image. What specific concern would you like me to help with?"
     - "When did you first notice this issue?"
     - "Is your pet showing any other symptoms?"
   - Do NOT provide a full assessment until you understand what the user is worried about

## Response Style
- Acknowledge the symptom category if provided
- Empathetic and clear
- Evidence-based
- Action-oriented for emergencies
- Educational for general questions

Remember: You can use multiple tools in sequence. Think step-by-step and choose the best tools for each situation.
"""


# ============================================================
# Tool Wrapper Functions
# ============================================================
# These wrap existing functions into LangChain Tool format

def _vector_search_wrapper(query: str) -> str:
    """Search the pet health knowledge database and return answer with sources."""
    try:
        from .rag_chain import ask
        answer, sources = ask(query)
        
        result = f"Knowledge Database Result:\n{answer}\n"
        
        if sources:
            result += f"\n📚 Sources ({len(sources)} documents):\n"
            for i, src in enumerate(sources[:3], 1):  # Show top 3 sources
                # Extract source info
                if hasattr(src, 'metadata'):
                    title = src.metadata.get('title', src.metadata.get('source', f'Document {i}'))
                    result += f"  {i}. {title}\n"
                else:
                    result += f"  {i}. Source document {i}\n"
        
        return result
    except Exception as e:
        return f"Error searching database: {str(e)}"


def _check_red_flags_wrapper(input_str: str) -> str:
    """
    Check symptoms for emergency red flags.

    Enhanced to support both simple text AND structured fields (JSON).

    Input can be:
    - Simple text: "vomiting and lethargy"
    - JSON: {"symptoms": "...", "species": "dog", "structured_fields": {...}}
    """
    try:
        # Try to parse as JSON first (structured input)
        try:
            import json
            data = json.loads(input_str)
            result = _check_red_flags_func(
                symptoms=data.get("symptoms", ""),
                pet_species=data.get("species"),
                pet_breed=data.get("breed"),
                structured_fields=data.get("structured_fields"),
                category=data.get("category")
            )
        except json.JSONDecodeError:
            # Fallback to simple text input
            result = _check_red_flags_func(symptoms=input_str)

        severity = result.get("severity", "UNKNOWN")
        is_emergency = result.get("is_emergency", False)
        flags = result.get("red_flags", [])
        recommendation = result.get("recommendation", "")
        action = result.get("action", "PROCEED_NORMAL")

        output = f"SEVERITY: {severity}\n"
        output += f"IS_EMERGENCY: {is_emergency}\n"
        output += f"ACTION: {action}\n"

        if flags:
            output += f"\nRed Flags Detected:\n"
            for flag in flags:
                output += f"- {flag}\n"

        output += f"\nRecommendation: {recommendation}"

        if is_emergency:
            output += "\n\n[EMERGENCY] Use get_er_template tool to return ER response immediately!"

        return output
    except Exception as e:
        return f"Error checking symptoms: {str(e)}"


def _find_vets_wrapper(location_query: str) -> str:
    """
    Find nearby veterinary clinics.
    Input format: "latitude,longitude" or "latitude,longitude,emergency"
    Example: "37.7749,-122.4194" or "37.7749,-122.4194,emergency"
    """
    try:
        parts = location_query.split(",")
        if len(parts) < 2:
            return "Error: Please provide location as 'latitude,longitude'"

        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        emergency = "emergency" in location_query.lower()

        results = _find_nearby_vets_func(
            latitude=lat,
            longitude=lon,
            emergency_only=emergency,
            max_results=5
        )
        
        if not results.get("vets"):
            return "No veterinary clinics found nearby."
        
        output = f"Found {len(results['vets'])} veterinary clinics:\n\n"
        for i, vet in enumerate(results["vets"], 1):
            output += f"{i}. {vet['name']}\n"
            output += f"   Address: {vet.get('address', 'N/A')}\n"
            output += f"   Distance: {vet.get('distance_km', 'N/A')} km\n"
            if vet.get('phone'):
                output += f"   Phone: {vet['phone']}\n"
            output += "\n"
        
        return output
    except Exception as e:
        return f"Error finding vets: {str(e)}"


def _web_search_wrapper(query: str) -> str:
    """Search the web for latest pet health information."""
    try:
        result = _web_search_func(query)
        return f"Web Search Results:\n{result.get('answer', 'No results found.')}"
    except Exception as e:
        return f"Error in web search: {str(e)}"





def _emergency_triage_wrapper(input_str: str) -> str:
    """
    Combined emergency triage and vet finding.
    Input format: "symptoms | latitude,longitude"
    Example: "vomiting and lethargy | 37.7749,-122.4194"
    """
    try:
        if "|" not in input_str:
            return "Error: Please provide input as 'symptoms | latitude,longitude'"
        
        symptoms, location = input_str.split("|", 1)
        symptoms = symptoms.strip()
        lat, lon = location.strip().split(",")
        lat, lon = float(lat), float(lon)
        
        result = triage_and_recommend(
            symptoms=symptoms,
            user_latitude=lat,
            user_longitude=lon
        )
        
        output = f"TRIAGE RESULT\n"
        output += f"Severity: {result['severity']}\n\n"
        
        if result.get('red_flags'):
            output += "Red Flags:\n"
            for flag in result['red_flags']:
                output += f"- {flag}\n"
            output += "\n"
        
        output += f"Recommendation: {result['recommendation']}\n\n"
        
        if result.get('nearby_vets'):
            output += "NEARBY VETERINARY CLINICS:\n"
            for i, vet in enumerate(result['nearby_vets'], 1):
                output += f"{i}. {vet['name']} - {vet.get('distance_km', 'N/A')} km\n"
        
        return output
    except Exception as e:
        return f"Error in triage: {str(e)}"


def _analyze_image_wrapper(image_path: str) -> str:
    """
    Analyze a pet image using GPT-4 Vision.
    Input: path or URL to the pet image
    """
    try:
        result = analyze_pet_image(image_path)

        output = f"IMAGE ANALYSIS RESULTS\n\n"
        output += f"Visual Observations:\n{result.get('description', 'N/A')}\n\n"

        if result.get('severity'):
            output += f"Assessed Severity: {result['severity']}\n\n"

        if result.get('recommendations'):
            output += f"Recommendations:\n"
            for rec in result['recommendations']:
                output += f"- {rec}\n"

        if result.get('concerns'):
            output += f"\nConcerns Identified:\n"
            for concern in result['concerns']:
                output += f"- {concern}\n"

        return output
    except Exception as e:
        return f"Error analyzing image: {str(e)}"


def _generate_triage_wrapper(input_json: str) -> str:
    """
    Generate structured triage response.
    Input: JSON with risk_level, category, reasoning, actions, etc.
    """
    return generate_triage_response_for_agent(input_json)


def _request_followup_wrapper(missing_info: str) -> str:
    """
    Generate follow-up questions when information is missing.
    Input: Description of what info is missing
    """
    return request_followup_for_agent(missing_info)


def _get_er_template_wrapper(category: str) -> str:
    """
    Get pre-built emergency template for a category.
    Use when check_red_flags returns is_emergency=True.
    """
    return get_er_template_for_agent(category)


# ============================================================
# Create LangChain Tools (using @tool decorator for LangChain 1.2.x)
# ============================================================

@tool
def vector_search(query: str) -> str:
    """Search the pet health knowledge database with 18,909 curated records.
    Use this for medical questions, conditions, treatments, breed information.
    Input: a clear question or search query about pet health.
    This should be your PRIMARY source for pet health information.
    """
    return _vector_search_wrapper(query)


@tool
def check_red_flags(input_str: str) -> str:
    """Check symptoms for emergency red flags. ALWAYS use this FIRST!

    CRITICAL: Input MUST be a JSON string with this exact format:
    {"symptoms": "description text", "species": "dog", "breed": "breed name", "category": "symptom category", "structured_fields": {"field1": "value1"}}

    The structured_fields from the user input are critical for accurate emergency detection!

    Output includes: IS_EMERGENCY (True/False), ACTION (RETURN_ER_TEMPLATE if emergency), severity level.
    If IS_EMERGENCY is True, you MUST immediately call get_er_template with the category.
    """
    return _check_red_flags_wrapper(input_str)


@tool
def find_nearby_vets(location_query: str) -> str:
    """Find veterinary clinics near a location.
    Use when risk_level is ER/TODAY or user asks for vet recommendations.
    Input: 'latitude,longitude' or 'latitude,longitude,emergency' for emergency-only clinics.
    Example: '37.7749,-122.4194' or '37.7749,-122.4194,emergency'
    """
    return _find_vets_wrapper(location_query)


@tool
def emergency_triage(input_str: str) -> str:
    """Combined emergency check and vet finder - more efficient than calling separately.
    Use when user provides both symptoms AND location.
    Input: 'symptoms | latitude,longitude'
    Example: 'vomiting and lethargy | 37.7749,-122.4194'
    """
    return _emergency_triage_wrapper(input_str)


@tool
def web_search_tool(query: str) -> str:
    """Search the web for current pet health information using Google Search.
    Use when:
    - Information could be outdated or evolving (treatments, research, products)
    - User wants current recommendations or comparisons
    - RAG results seem incomplete or you want to supplement with fresh data
    NOT needed for: basic breed info, anatomy, well-established conditions.
    Input: a specific search query about pet health topics.
    """
    return _web_search_wrapper(query)


@tool
def analyze_image(image_path: str) -> str:
    """Analyze a pet photo using GPT-4 Vision to identify visible symptoms and concerns.
    ALWAYS use this when user provides an image.
    Input: file path or URL to the pet image.
    Output: visual observations, severity assessment, and recommendations.
    Useful for: skin conditions, wounds, physical abnormalities, posture issues.
    """
    return _analyze_image_wrapper(image_path)


@tool
def get_er_template(category: str) -> str:
    """Get pre-built emergency response template for a symptom category.
    Use this IMMEDIATELY when check_red_flags returns is_emergency=True.
    Input: symptom category string (e.g., 'Urinary & Genital', 'Breathing Issues').
    Output: Complete ER triage response - no LLM reasoning needed.
    """
    return _get_er_template_wrapper(category)


@tool
def request_followup(missing_info: str) -> str:
    """Generate follow-up questions when critical information is missing.
    Use when you cannot make an accurate assessment due to missing info.
    Input: description of what information is missing.
    Example: 'duration of symptoms, severity of vomiting, presence of blood'
    """
    return _request_followup_wrapper(missing_info)


@tool
def generate_triage_response(input_json: str) -> str:
    """Generate final structured triage response. Use this LAST to format output.
    Input: JSON with required fields:
    {"risk_level": "ER|TODAY|SOON|MONITOR", "category": "...",
    "reasoning": ["..."], "actions": ["..."], "monitoring": ["..."]}
    """
    return _generate_triage_wrapper(input_json)


# Base tools (for general health questions)
BASE_TOOLS = [vector_search, check_red_flags, find_nearby_vets, emergency_triage, web_search_tool, analyze_image]

# Triage-specific tools (for structured triage workflow)
TRIAGE_TOOLS = [get_er_template, request_followup, generate_triage_response]

# Combined tools for general use
TOOLS = BASE_TOOLS

# Full tools including triage-specific ones
FULL_TRIAGE_TOOLS = BASE_TOOLS + TRIAGE_TOOLS


# ============================================================
# Agent Class (Updated for LangGraph)
# ============================================================

class PetHealthAgent:
    """
    Autonomous AI Agent for Pet Health assistance.

    Unlike the regular RAG chain, this agent can:
    - Decide which tools to use based on context
    - Chain multiple tools together
    - Adapt strategy based on intermediate results

    Example:
        agent = PetHealthAgent()
        result = agent.chat("My dog is vomiting, should I be worried?")
        print(result["output"])
    """

    def __init__(
        self,
        model: str = "gpt-4o",  # Better instruction following
        temperature: float = 0.7,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        Initialize the Pet Health Agent.

        Args:
            model: OpenAI model to use
            temperature: LLM temperature (0-1)
            max_iterations: Maximum tool calling iterations
            verbose: Print agent reasoning steps
        """
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.verbose = verbose

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=OPENAI_API_KEY
        )

        # Create agent using LangGraph's create_react_agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=TOOLS,
            prompt=AGENT_SYSTEM_PROMPT,
        )

        # Simple message history for conversation
        self.chat_history = []

    def chat(self, user_input: str, context: Dict[str, Any] = None, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Chat with the agent.

        Args:
            user_input: User's question or message
            context: Optional context (pet_info, location, etc.)
            history: Optional list of previous messages [{"role": "user", "content": "..."}, ...]

        Returns:
            Dictionary with:
                - output: Agent's response
                - intermediate_steps: List of tool calls made
                - chat_history: Conversation history
        """
        # Re-hydrate history if provided
        if history:
            for msg in history:
                if msg.get("role") == "user":
                    self.chat_history.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    self.chat_history.append(AIMessage(content=msg.get("content", "")))

        # Add context to input if provided
        # Add context to input if provided
        full_input = user_input
        if context:
            context_str = "\n\nContext:\n"
            if "symptom_category" in context:
                context_str += f"Symptom Category: {context['symptom_category']}\n"
            if "pet_info" in context:
                context_str += f"Pet: {context['pet_info']}\n"
            if "location" in context:
                context_str += f"Location: {context['location']}\n"
            if "image_path" in context:
                context_str += f"Image: {context['image_path']}\n"
            full_input = user_input + context_str

        # Build messages
        messages = self.chat_history + [HumanMessage(content=full_input)]

        # Run agent
        result = self.agent.invoke({"messages": messages})

        # Extract the final response
        output_messages = result.get("messages", [])
        final_output = ""
        tool_calls = []

        for msg in output_messages:
            # Check for tool calls first (AIMessage with tool_calls often has empty content)
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)
            # Then check for final AI response (has content, no tool_call_id)
            elif hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_call_id'):
                # This is the final AI response (not a tool result)
                final_output = msg.content

        # Update history
        self.chat_history.append(HumanMessage(content=user_input))
        if final_output:
            self.chat_history.append(AIMessage(content=final_output))

        return {
            "output": final_output,
            "intermediate_steps": tool_calls,
            "chat_history": self.chat_history
        }

    def reset_memory(self):
        """Clear conversation history."""
        self.chat_history = []

    def get_tool_usage_summary(self, result: Dict[str, Any]) -> str:
        """
        Get a summary of which tools were used.

        Args:
            result: Result from chat() method

        Returns:
            Human-readable summary of tool usage
        """
        steps = result.get("intermediate_steps", [])
        if not steps:
            return "No tools were used."

        summary = "Tools used:\n"
        for i, tool_call in enumerate(steps, 1):
            if isinstance(tool_call, dict):
                tool_name = tool_call.get("name", "unknown")
                tool_input = str(tool_call.get("args", {}))[:50]
            else:
                tool_name = getattr(tool_call, 'name', str(tool_call))
                tool_input = str(getattr(tool_call, 'args', ''))[:50]
            summary += f"{i}. {tool_name}({tool_input})\n"

        return summary


# ============================================================
# TRIAGE AGENT SYSTEM PROMPT
# ============================================================

TRIAGE_AGENT_SYSTEM_PROMPT = """You are a Pet Health Triage Agent. Your job is to assess pet health concerns and provide structured triage responses.

## CRITICAL WORKFLOW - FOLLOW EXACTLY

### MEDICAL HISTORY (If Provided)
You may receive "Pet Medical History" context.
- Use this ONLY to identify chronic/recurring issues.
- If current symptoms match history (e.g. "vomiting again"), consider it a recurring issue (potentially higher risk).
- DO NOT treat past symptoms as current ones unless the user mentions them again today.
- This is for CONTEXT only. Focus on the CURRENT description for triage.

### Step 1: ANALYZE IMAGE FIRST (if provided)
If an image is provided, use `analyze_image` FIRST before anything else.

⚠️ CRITICAL: If the image shows ANY of these, it's an IMMEDIATE EMERGENCY (ER):
- Blood (anywhere on the pet)
- Open wounds or lacerations
- Visible injuries or trauma
- Pale/white/blue gums
- Unconscious or collapsed pet
- Difficulty breathing
- Swelling/distended abdomen

If image shows emergency signs → use `get_er_template` IMMEDIATELY → DO NOT ask follow-up questions!

### Step 2: Check Red Flags
Use the `check_red_flags` tool with a JSON string containing ALL available information.

IMPORTANT: You MUST pass a JSON string to check_red_flags, NOT plain text!
Example format:
{"symptoms": "vomiting, lethargy", "species": "dog", "breed": "Great Dane", "category": "Stomach Upset", "structured_fields": {}}

If the result shows `IS_EMERGENCY: True` or `ACTION: RETURN_ER_TEMPLATE`:
→ IMMEDIATELY use `get_er_template` tool with the category
→ DO NOT use request_followup for emergencies
→ Return the ER template as your final response

### Step 3: Non-Emergency Assessment
Only if NOT an emergency:
- If critical information is missing → use `request_followup` (NEVER use this for emergencies!)
- If you need medical knowledge → use `vector_search`
- If location is provided AND urgent → use `find_nearby_vets`

### Step 4: Generate Final Response
Use `generate_triage_response` tool with:
- risk_level: "ER" | "TODAY" | "SOON" | "MONITOR"
- category: the symptom category (infer from symptoms if "Something Else")
- reasoning: list of reasons for this risk level
- actions: list of recommended actions
- monitoring: what to watch for

## NEVER ASK FOLLOW-UP QUESTIONS FOR:
- Blood visible on pet
- Any bleeding or wounds
- Trauma or injury
- Difficulty breathing
- Unconscious/collapsed pet
- These are ALL emergencies - use get_er_template immediately!

## Risk Level Definitions
- ER: Life-threatening, go to emergency vet NOW
- TODAY: Serious, see a vet within 24 hours
- SOON: Moderate, schedule appointment within 2-3 days
- MONITOR: Low risk, monitor at home, see vet if worsens

## Important Rules
1. SAFETY FIRST: When in doubt, escalate to higher risk level
2. NO DIAGNOSIS: Never say "your pet has X disease"
3. NO MEDICATIONS: Never recommend specific drugs or dosages
4. STRUCTURED OUTPUT: Always use generate_triage_response for final output
5. TOOL ORDER: check_red_flags → (get_er_template if ER) → other tools → generate_triage_response

## Available Tools Summary
- check_red_flags: Check for emergencies (ALWAYS USE FIRST)
- get_er_template: Get ER response template (use if emergency)
- request_followup: Generate follow-up questions (if info missing)
- vector_search: Search medical knowledge base
- web_search_tool: Search web for current treatments, research, products (use for evolving topics)
- analyze_image: Analyze pet photos
- find_nearby_vets: Find veterinary clinics
- generate_triage_response: Format final response (ALWAYS USE LAST)

## SCOPE RESTRICTIONS (CRITICAL)

6. ONLY Dogs and Cats: You can ONLY assess dogs and cats.
   - If species is NOT dog or cat, respond with an error message explaining you only support dogs and cats.
   - Never attempt to triage other animals (birds, reptiles, horses, fish, etc.)

7. Image-Only Requests: When the user provides ONLY an image with no symptom description:
   - FIRST analyze the image using analyze_image to check for emergencies
   - If emergency signs detected (blood, wounds, distress) → use get_er_template immediately
   - If NO emergency signs → use request_followup to ask what specific concern they have
   - Example: "I can see your pet in the image. What specific symptom or concern brought you to us today?"
"""


# ============================================================
# PetTriageAgent Class - Specialized for Triage Workflow
# ============================================================

class PetTriageAgent:
    """
    Specialized Agent for Pet Health Triage.

    Unlike PetHealthAgent (general Q&A), this agent:
    1. Follows a strict triage workflow
    2. Uses structured output (TriageResponse schema)
    3. Prioritizes emergency detection
    4. Works with input/output guardrails

    Usage:
        agent = PetTriageAgent()
        result = agent.triage(
            species="dog",
            category="Stomach Upset",
            structured_fields={"vomiting_frequency": "multiple"},
            user_description="My dog has been vomiting for 3 hours"
        )
        print(result["triage_response"])
    """

    def __init__(
        self,
        model: str = "gpt-4o",  # Better instruction following
        temperature: float = 0.3,  # Lower for consistent triage
        max_iterations: int = 8,
        verbose: bool = True
    ):
        """
        Initialize the Triage Agent.

        Args:
            model: OpenAI model to use
            temperature: LLM temperature (lower = more consistent)
            max_iterations: Maximum tool calling iterations
            verbose: Print agent reasoning steps
        """
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.verbose = verbose

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=OPENAI_API_KEY
        )

        # Create agent using LangGraph's create_react_agent with triage tools
        self.agent = create_react_agent(
            model=self.llm,
            tools=FULL_TRIAGE_TOOLS,
            prompt=TRIAGE_AGENT_SYSTEM_PROMPT,
        )

    def triage(
        self,
        species: str,
        category: str,
        structured_fields: Dict[str, Any] = None,
        user_description: str = "",
        pet_profile: Dict[str, Any] = None,
        image_base64: str = None,
        image_path: str = None,
        latitude: float = None,
        longitude: float = None,
        triage_history: List[Dict[str, Any]] = None  # New: past triage sessions
    ) -> Dict[str, Any]:
        """
        Perform triage assessment.

        This is the main entry point for triage. The agent will:
        1. Check for emergencies
        2. Gather additional information if needed
        3. Return a structured TriageResponse

        Args:
            species: "dog" or "cat"
            category: Symptom category
            structured_fields: UI form answers (checkboxes, dropdowns)
            user_description: Free text description
            pet_profile: Pet info (name, age, breed, weight)
            image_base64: Base64 encoded image (optional)
            image_path: Path to image file (optional)
            latitude: User latitude for vet finder (optional)
            longitude: User longitude for vet finder (optional)
            triage_history: List of past triage session dicts (optional)

        Returns:
            Dict with assessment results
        """
        import json

        result = {
            "success": False,
            "triage_response": None,
            "tools_used": [],
            "is_emergency": False,
            "raw_output": "",
            "rag_source_count": 0,
            "used_web_search": False
        }

        # Build the input message for the agent
        input_parts = []

        input_parts.append(f"Species: {species}")
        input_parts.append(f"Symptom Category: {category}")

        if triage_history:
            history_str = "MEDICAL HISTORY (Past Triage Sessions):\n"
            for i, session in enumerate(triage_history[:5], 1):  # Limit to 5
                date = session.get("created_at", "Unknown Date").split("T")[0]
                risk = session.get("risk_level", "Unknown")
                cat = session.get("category", "Unknown")
                desc = session.get("user_description", "No description")[:100]  # Truncate
                history_str += f"- [{date}] Category: {cat} | Risk: {risk} | Desc: {desc}...\n"
            input_parts.append(history_str)

        if user_description:
            input_parts.append(f"CURRENT DESCRIPTION: {user_description}")
        
        if pet_profile:
            profile_str = ", ".join(f"{k}: {v}" for k, v in pet_profile.items() if v)
            input_parts.append(f"Pet Profile: {profile_str}")

        if structured_fields:
            # Format structured fields for the agent
            fields_str = json.dumps(structured_fields, ensure_ascii=False)
            input_parts.append(f"Structured Fields (from UI form): {fields_str}")

        # Pre-analyze image if provided and add results to input
        image_analysis_result = None
        if image_path or image_base64:
            try:
                image_source = image_path
                if image_base64 and not image_path:
                    # Save base64 to temp file
                    import tempfile
                    import base64
                    image_data = base64.b64decode(image_base64)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                        f.write(image_data)
                        image_source = f.name
                
                from .image_analyzer import analyze_pet_image
                image_analysis_result = analyze_pet_image(image_source, user_question=user_description)
                image_desc = image_analysis_result.get("description", "")
                
                # Add image analysis to input - make it VERY clear if emergency
                input_parts.append("")
                input_parts.append("=== IMAGE ANALYSIS RESULTS ===")
                input_parts.append(image_desc)
                input_parts.append("=== END IMAGE ANALYSIS ===")
                
                # Check for emergency keywords in image analysis
                image_lower = image_desc.lower()
                emergency_in_image = any(kw in image_lower for kw in 
                    ["blood", "bleeding", "wound", "injury", "trauma", "laceration", 
                     "emergency", "er", "immediate", "urgent", "severe"])
                
                if emergency_in_image:
                    input_parts.append("")
                    input_parts.append("⚠️ CRITICAL: Image shows BLOOD/INJURY - this is an EMERGENCY!")
                    input_parts.append("→ You MUST use get_er_template tool immediately!")
                    input_parts.append("→ Do NOT ask follow-up questions!")
                    input_parts.append("→ Do NOT use request_followup!")
                    result["is_emergency"] = True  # Mark as emergency from image
                
                # Track image analysis as a tool used
                result["tools_used"].append({
                    "tool": "analyze_image",
                    "input": "pre-analysis of uploaded image"
                })
                    
                # Clean up temp file if created
                if image_base64 and not image_path and image_source:
                    import os
                    try:
                        os.unlink(image_source)
                    except:
                        pass
                        
            except Exception as e:
                input_parts.append(f"Image analysis failed: {str(e)}")

        if latitude and longitude:
            input_parts.append(f"Location: {latitude},{longitude}")

        # Add instruction
        input_parts.append("")
        input_parts.append("=== INSTRUCTIONS ===")
        input_parts.append("1. If image shows blood/injury/emergency → use get_er_template IMMEDIATELY")
        input_parts.append("2. Check for emergencies using check_red_flags")
        input_parts.append("3. If emergency, use get_er_template and return immediately")
        input_parts.append("4. NEVER use request_followup for blood, injuries, or emergencies")
        input_parts.append("5. Otherwise, use generate_triage_response")

        full_input = "\n".join(input_parts)

        try:
            # Run the agent with LangGraph
            messages = [HumanMessage(content=full_input)]
            agent_result = self.agent.invoke({"messages": messages})

            # Extract the final response and tool usage from messages
            output_messages = agent_result.get("messages", [])
            final_output = ""
            tool_calls = []

            for msg in output_messages:
                # Check for tool calls first (AIMessage with tool_calls often has empty content)
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls.append({
                            "tool": tc.get("name", "unknown"),
                            "input": str(tc.get("args", {}))[:200]
                        })
                # Then check for final AI response (has content, no tool_call_id)
                elif hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_call_id'):
                    # This is the final AI response (not a tool result)
                    final_output = msg.content

            result["raw_output"] = final_output
            result["success"] = True
            result["tools_used"] = tool_calls

            if self.verbose and tool_calls:
                print(f"  Agent used {len(tool_calls)} tools:")
                for tc in tool_calls:
                    print(f"    - {tc['tool']}")

            # Extract triage response from tool messages
            # Look for JSON with risk_level in ToolMessages (from get_er_template or generate_triage_response)
            triage_response = None
            for msg in output_messages:
                if 'ToolMessage' in type(msg).__name__ and msg.content:
                    try:
                        parsed = json.loads(msg.content)
                        if isinstance(parsed, dict) and 'risk_level' in parsed:
                            # Found a valid triage response from tools
                            triage_response = parsed
                            if self.verbose:
                                print(f"  Found triage response in tool output: risk_level={parsed.get('risk_level')}")
                    except json.JSONDecodeError:
                        continue

            # Extract source count from vector_search tool output
            rag_source_count = 0
            used_web_search = False
            for msg in output_messages:
                if 'ToolMessage' in type(msg).__name__ and msg.content:
                    content = msg.content
                    # Check for RAG sources pattern: "📚 Sources (X documents)"
                    import re
                    source_match = re.search(r'Sources \((\d+) documents\)', content)
                    if source_match:
                        rag_source_count = int(source_match.group(1))
                    # Check if web search was used
                    if 'Web Search Result' in content or 'search results' in content.lower():
                        used_web_search = True
            
            result["rag_source_count"] = rag_source_count
            result["used_web_search"] = used_web_search

            if triage_response:
                result["triage_response"] = triage_response
            else:
                # Fallback: try to extract JSON from the final AI output
                raw_output = result["raw_output"]
                try:
                    import re
                    json_match = re.search(r'\{[^{}]*"risk_level"[^{}]*\}', raw_output, re.DOTALL)
                    if json_match:
                        result["triage_response"] = json.loads(json_match.group())
                    else:
                        result["triage_response"] = json.loads(raw_output)
                except json.JSONDecodeError:
                    # If we can't parse JSON, create a basic response from the text
                    result["triage_response"] = {
                        "risk_level": "TODAY",
                        "category": category,
                        "reasoning_summary": [raw_output[:200] if raw_output else "Unable to parse response"],
                        "recommended_actions": ["Contact your veterinarian for evaluation"],
                        "what_to_monitor": [],
                        "disclaimer": "This is not a diagnosis. Seek veterinary care if concerned."
                    }

            # Check if this was an emergency
            result["is_emergency"] = result["triage_response"].get("risk_level") == "ER"

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            if self.verbose:
                print(f"  Agent error: {e}")
            # Return safe fallback
            result["triage_response"] = {
                "risk_level": "TODAY",
                "category": category,
                "reasoning_summary": ["Unable to complete assessment"],
                "recommended_actions": [
                    "Contact your veterinarian for evaluation",
                    "Monitor your pet closely"
                ],
                "what_to_monitor": ["Any worsening symptoms"],
                "disclaimer": "This is not a diagnosis. Seek veterinary care if concerned."
            }

        return result

    def get_tool_usage_summary(self, result: Dict[str, Any]) -> str:
        """Get a summary of which tools were used."""
        tools = result.get("tools_used", [])
        if not tools:
            return "No tools were used."

        summary = "Tools used:\n"
        for i, tool_info in enumerate(tools, 1):
            summary += f"{i}. {tool_info['tool']}({tool_info['input'][:50]}...)\n"

        return summary


# ============================================================
# Convenience Functions
# ============================================================

def quick_ask(question: str, verbose: bool = False) -> str:
    """
    Quick one-off question (no conversation memory).
    
    Args:
        question: User's question
        verbose: Print agent reasoning
    
    Returns:
        Agent's answer
    """
    agent = PetHealthAgent(verbose=verbose)
    result = agent.chat(question)
    return result["output"]


def emergency_check(symptoms: str, location: tuple = None, verbose: bool = False) -> str:
    """
    Quick emergency check with optional vet finding.
    
    Args:
        symptoms: Description of symptoms
        location: (latitude, longitude) tuple
        verbose: Print agent reasoning
    
    Returns:
        Emergency assessment and recommendations
    """
    agent = PetHealthAgent(verbose=verbose)
    
    question = f"Emergency check: {symptoms}"
    context = {}
    if location:
        context["location"] = f"Latitude: {location[0]}, Longitude: {location[1]}"
    
    result = agent.chat(question, context=context)
    return result["output"]


# ============================================================
# Example Usage
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Pet Health AI - Agent Version")
    print("=" * 60)
    print()
    
    # Examples for local testing
    
    # Example 1: Simple medical question
    print("Example 1: Simple Question")
    print("-" * 60)
    result = quick_ask(
        "What are the signs of diabetes in dogs?",
        verbose=True
    )
    print(f"\nAnswer: {result}")
    print()
    
    # Example 2: Emergency scenario with symptom category
    print("\n" + "=" * 60)
    print("Example 2: Emergency with Symptom Category")
    print("-" * 60)
    agent = PetHealthAgent(verbose=True)
    
    # User selects "Stomach Upset" category and describes symptoms
    result = agent.chat(
        "My dog has been vomiting for 3 hours and won't drink water",
        context={"symptom_category": "Stomach Upset"}
    )
    print(f"\nAgent: {result['output']}")
    print(f"\n{agent.get_tool_usage_summary(result)}")
    
    # Example 3: Image analysis placeholder
    print("\n" + "=" * 60)
    print("Example 3: Image Analysis (Placeholder)")
    print("-" * 60)
    print("Uncomment code in main block to test with actual image path.")
    
    # Example 4: Multi-turn conversation
    print("\n" + "=" * 60)
    print("Example 4: Multi-turn with Category")
    print("-" * 60)
    agent2 = PetHealthAgent(verbose=True)
    
    # Turn 1: User describes breathing symptoms
    result1 = agent2.chat(
        "My cat is coughing and seems to have trouble breathing",
        context={"symptom_category": "Breathing Issues"}
    )
    print(f"\nAgent: {result1['output'][:200]}...")
    
    # Turn 2: User provides location for vet finder
    result2 = agent2.chat(
        "Can you find nearby vets?",
        context={"location": "37.7749,-122.4194"}
    )
    print(f"\nAgent: {result2['output'][:200]}...")

    
    print("\n" + "=" * 60)
    print("Usage Example for Frontend Integration:")
    print("-" * 60)
    print("""
    # Frontend sends:
    {
        "query": "My dog is limping",
        "symptom_category": "Musculoskeletal",  # From dropdown
        "image_path": "https://...",  # Optional
        "location": {
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    }
    
    # Backend processes:
    agent = PetHealthAgent()
    result = agent.chat(
        query,
        context={
            "symptom_category": symptom_category,
            "image_path": image_path,
            "location": f"{lat},{lon}"
        }
    )
    """)
    
    print("\n" + "=" * 60)
    print("Agent examples completed!")
    print("=" * 60)

