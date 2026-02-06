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

# Import existing tools
# Aliases avoid naming conflicts with @tool decorated functions (used by PetHealthAgent)
from .rag_chain import ask
from .tools import (
    check_red_flags as _check_red_flags_func,
    find_nearby_vets as _find_nearby_vets_func,
    web_search as _web_search_func,
    get_er_template as _get_er_template_func,
    generate_triage_response as _generate_triage_response_func,
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


# Tools for PetHealthAgent (ReAct - general Q&A)
TOOLS = [vector_search, check_red_flags, find_nearby_vets, web_search_tool, analyze_image]


# ============================================================
# PetHealthAgent Class (ReAct - General Q&A)
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
# Triage Assessment Prompt (for single LLM call in pipeline)
# ============================================================

TRIAGE_ASSESSMENT_PROMPT = """You are a pet health triage assistant. Based on the provided context, generate a structured triage assessment as JSON.

## Output Format (JSON only, no other text)
{{
  "risk_level": "TODAY|SOON|MONITOR",
  "reasoning_summary": ["reason1", "reason2", "reason3"],
  "recommended_actions": ["action1", "action2"],
  "what_to_monitor": ["item1", "item2"]
}}

## Rules
- risk_level MUST be >= {min_severity} (baseline from symptom check)
- Severity order: ER > TODAY > SOON > MONITOR
- When in doubt, escalate to higher risk level
- Never diagnose specific diseases (no "your pet has X")
- Never recommend specific medications or dosages
- Max 3 reasoning items, 6 actions, 5 monitoring items
- Keep each item under 120 characters

## Context
Species: {species}
Category: {category}
{pet_profile_section}
{history_section}
Symptom Description: {user_description}
{image_section}
Red Flag Check Result: severity={severity}, flags={red_flags}
{knowledge_section}"""


# ============================================================
# PetTriageAgent Class (Pipeline - Structured Triage)
# ============================================================

class PetTriageAgent:
    """
    Pipeline-based triage agent with deterministic flow.

    Flow: image analysis → red flag check → (ER template | RAG + LLM assessment)
    Only one LLM call for non-emergency cases (vs. ReAct's multi-turn loop).
    """

    # Severity ordering for baseline enforcement
    _SEVERITY_ORDER = {"MONITOR": 0, "SOON": 1, "TODAY": 2, "ER": 3}

    # Emergency keywords for image analysis
    _IMAGE_EMERGENCY_KEYWORDS = [
        "blood", "bleeding", "wound", "injury", "trauma", "laceration",
        "emergency", "immediate", "urgent", "severe"
    ]

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_iterations: int = 8,  # kept for interface compatibility
        verbose: bool = True
    ):
        self.model = model
        self.verbose = verbose
        self.llm = ChatOpenAI(
            model=model, temperature=temperature, api_key=OPENAI_API_KEY,
            model_kwargs={"response_format": {"type": "json_object"}}
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
        triage_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform triage via deterministic pipeline. Interface unchanged from ReAct version."""
        import json

        result = {
            "success": False, "triage_response": None, "tools_used": [],
            "is_emergency": False, "raw_output": "", "rag_source_count": 0,
            "used_web_search": False
        }
        breed = pet_profile.get("breed") if pet_profile else None

        try:
            # ----------------------------------------------------------
            # Step 1: Image analysis (if provided)
            # ----------------------------------------------------------
            image_desc = ""
            if image_path or image_base64:
                image_desc = self._analyze_image(image_base64, image_path, user_description)
                result["tools_used"].append({"tool": "analyze_image", "input": "uploaded image"})

                if self._is_image_emergency(image_desc):
                    if self.verbose:
                        print("  [Pipeline] Image emergency detected → ER template")
                    return self._build_er_result(
                        result, category, ["Blood/injury visible in image"],
                        ["Image shows blood or injury requiring immediate veterinary attention"]
                    )

            # ----------------------------------------------------------
            # Step 2: Check red flags (rule-based, always runs)
            # ----------------------------------------------------------
            red_flag_result = _check_red_flags_func(
                symptoms=user_description,
                pet_species=species,
                pet_breed=breed,
                structured_fields=structured_fields or {},
                category=category
            )
            result["tools_used"].append({"tool": "check_red_flags", "input": user_description[:200]})

            if self.verbose:
                print(f"  [Pipeline] Red flags: severity={red_flag_result['severity']}, "
                      f"is_emergency={red_flag_result['is_emergency']}")

            if red_flag_result["is_emergency"]:
                return self._build_er_result(
                    result, category,
                    red_flag_result.get("red_flags", []),
                    [red_flag_result.get("recommendation", "Emergency detected")]
                )

            # ----------------------------------------------------------
            # Step 3: Knowledge search (RAG)
            # ----------------------------------------------------------
            knowledge = ""
            if user_description:
                try:
                    answer, sources = ask(user_description)
                    knowledge = answer
                    result["rag_source_count"] = len(sources)
                    result["tools_used"].append({"tool": "vector_search", "input": user_description[:200]})
                    if self.verbose:
                        print(f"  [Pipeline] RAG search: {len(sources)} sources")
                except Exception as e:
                    if self.verbose:
                        print(f"  [Pipeline] RAG search failed: {e}")

            # ----------------------------------------------------------
            # Step 4: Single LLM call for assessment
            # ----------------------------------------------------------
            triage_response = self._assess(
                species=species, category=category,
                user_description=user_description,
                pet_profile=pet_profile,
                structured_fields=structured_fields,
                triage_history=triage_history,
                red_flag_result=red_flag_result,
                knowledge=knowledge,
                image_desc=image_desc
            )
            result["tools_used"].append({"tool": "llm_assessment", "input": category})

            result["success"] = True
            result["triage_response"] = triage_response
            result["is_emergency"] = triage_response.get("risk_level") == "ER"

            if self.verbose:
                print(f"  [Pipeline] Assessment complete: risk_level={triage_response.get('risk_level')}")

        except Exception as e:
            if self.verbose:
                print(f"  [Pipeline] Error: {e}")
            result["success"] = True
            result["triage_response"] = self._fallback_response(category)

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _analyze_image(self, image_base64: str, image_path: str, user_description: str) -> str:
        """Analyze image and return description text."""
        import tempfile, base64
        image_source = image_path
        temp_path = None
        try:
            if image_base64 and not image_path:
                image_data = base64.b64decode(image_base64)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                    f.write(image_data)
                    image_source = temp_path = f.name
            result = analyze_pet_image(image_source, user_question=user_description)
            return result.get("description", "") or result.get("analysis", "")
        except Exception as e:
            if self.verbose:
                print(f"  [Pipeline] Image analysis failed: {e}")
            return ""
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    def _is_image_emergency(self, image_desc: str) -> bool:
        """Check if image analysis indicates emergency."""
        desc_lower = image_desc.lower()
        return any(kw in desc_lower for kw in self._IMAGE_EMERGENCY_KEYWORDS)

    def _build_er_result(self, result: Dict, category: str,
                         red_flags: List[str], reasoning: List[str]) -> Dict:
        """Build and return an ER result using the template."""
        er_response = _get_er_template_func(category)
        er_response["red_flags"] = red_flags[:5]
        er_response["reasoning_summary"] = reasoning[:3]
        result["tools_used"].append({"tool": "get_er_template", "input": category})
        result.update({"success": True, "triage_response": er_response, "is_emergency": True})
        return result

    def _assess(self, species: str, category: str, user_description: str,
                pet_profile: Dict, structured_fields: Dict,
                triage_history: List, red_flag_result: Dict,
                knowledge: str, image_desc: str) -> Dict:
        """Single LLM call to generate structured triage assessment."""
        import json

        # Build context sections
        profile_section = ""
        if pet_profile:
            profile_section = "Pet Profile: " + ", ".join(
                f"{k}: {v}" for k, v in pet_profile.items() if v)

        history_section = ""
        if triage_history:
            lines = []
            for s in triage_history[:5]:
                date = s.get("created_at", "?").split("T")[0]
                lines.append(f"- [{date}] {s.get('category', '?')} | "
                             f"Risk: {s.get('risk_level', '?')} | {s.get('user_description', '')[:80]}")
            history_section = "Medical History:\n" + "\n".join(lines)

        image_section = f"Image Analysis: {image_desc}" if image_desc else ""
        knowledge_section = f"Knowledge Base:\n{knowledge}" if knowledge else ""

        min_severity = red_flag_result.get("severity", "MONITOR")
        prompt = TRIAGE_ASSESSMENT_PROMPT.format(
            species=species, category=category,
            user_description=user_description or "(no description)",
            pet_profile_section=profile_section,
            history_section=history_section,
            image_section=image_section,
            severity=min_severity,
            red_flags=red_flag_result.get("red_flags", []),
            knowledge_section=knowledge_section,
            min_severity=min_severity
        )

        # Single LLM call with JSON mode
        response = self.llm.invoke([HumanMessage(content=prompt)])
        raw = response.content
        parsed = json.loads(raw)

        # Enforce minimum severity from red flag check
        llm_level = parsed.get("risk_level", "TODAY")
        if self._SEVERITY_ORDER.get(llm_level, 0) < self._SEVERITY_ORDER.get(min_severity, 0):
            parsed["risk_level"] = min_severity

        # Format through generate_triage_response for consistent schema
        return _generate_triage_response_func(
            risk_level=parsed.get("risk_level", "TODAY"),
            category=category,
            red_flags=red_flag_result.get("red_flags"),
            reasoning=parsed.get("reasoning_summary"),
            actions=parsed.get("recommended_actions"),
            monitoring=parsed.get("what_to_monitor"),
        )

    @staticmethod
    def _fallback_response(category: str) -> Dict:
        """Safe fallback when pipeline fails."""
        return {
            "risk_level": "TODAY",
            "category": category,
            "reasoning_summary": ["Unable to complete assessment"],
            "recommended_actions": ["Contact your veterinarian for evaluation",
                                    "Monitor your pet closely"],
            "what_to_monitor": ["Any worsening symptoms"],
            "disclaimer": "This is not a diagnosis. Seek veterinary care if concerned."
        }

    def get_tool_usage_summary(self, result: Dict[str, Any]) -> str:
        """Get a summary of which tools were used."""
        tools = result.get("tools_used", [])
        if not tools:
            return "No tools were used."
        return "Tools used:\n" + "".join(
            f"{i}. {t['tool']}({t['input'][:50]}...)\n"
            for i, t in enumerate(tools, 1)
        )


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

