# 🩺 Pet Triage AI Backend

An AI-powered symptom triage system for dogs and cats using OpenAI GPT models and LangGraph Agents. Designed for mobile app integration with a safety-first approach.

---

## 🏗️ Project Structure

```
pet_triage/
├── api.py                  # FastAPI entry point (all endpoints)
├── auth.py                 # JWT authentication
├── database.py             # SQLite database operations
├── main.py                 # Main triage orchestration
├── llm_setup.py            # OpenAI client, ER rules, model selection
├── input_guardrails.py     # 5-layer input validation
├── output_guardrails.py    # 6-layer output validation
├── fuzzy_friend.db         # SQLite database
├── core/                   # AI Agent module
│   ├── agent.py            # LangGraph ReAct Agent (PetHealthAgent)
│   ├── tools.py            # Agent tools (7 tools)
│   ├── rag_chain.py        # RAG chain for Pinecone knowledge base
│   └── image_analyzer.py   # GPT-4V image analysis
├── shared/                 # Shared constants and utilities
│   ├── constants.py        # Single source of truth for constants
│   ├── prompts.py          # System prompts and templates
│   ├── schemas.py          # Pydantic response schemas
│   ├── red_flags.py        # Emergency detection rules
│   └── errors.py           # Error handling
└── tests/                  # Unit tests
    ├── run_all_tests.py    # Test runner
    └── test_*.py           # Individual test files
```

---

## 🔄 Architecture Flow

```
User Input (symptom description + category + optional image)
    │
    ▼
┌─────────────────────────────────────────┐
│  INPUT GUARDRAILS (5 layers)            │
│  • Scope check (dogs/cats only)         │
│  • Field completeness validation        │
│  • ER pre-check (hard-route emergencies)│
│  • Input sanitization                   │
│  • Prompt injection detection           │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  LANGGRAPH REACT AGENT                  │
│  LLM autonomously selects tools:        │
│  ├─ check_red_flags: Emergency detect   │
│  ├─ vector_search: RAG knowledge base   │
│  ├─ analyze_image: GPT-4V analysis      │
│  ├─ find_nearby_vets: Vet finder (OSM)  │
│  ├─ web_search: Tavily web search       │
│  ├─ get_er_template: ER response        │
│  └─ generate_triage_response: Output    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  OUTPUT GUARDRAILS (6 layers)           │
│  • JSON schema validation               │
│  • Content safety (no diagnosis)        │
│  • Risk calibration                     │
│  • Mandatory disclaimer                 │
│  • UI constraints (length limits)       │
│  • Safe fallback                        │
└─────────────────────────────────────────┘
    │
    ▼
Final Response (TriageResponse JSON)
```

---

## 🛠️ Agent Tools

| Tool | Type | Description |
|------|------|-------------|
| `check_red_flags` | Rule-based | Detect emergency conditions via keyword matching |
| `vector_search` | RAG | Search 18,909 pet health records in Pinecone |
| `analyze_image` | Vision | Analyze pet photos with GPT-4V |
| `find_nearby_vets` | API | Find nearby vet clinics via OpenStreetMap |
| `web_search` | API | Search web for current info via Tavily |
| `get_er_template` | Template | Get pre-built emergency response |
| `generate_triage_response` | Generator | Format final structured triage output |

---

## 🔒 Input Guardrails (5 Layers)

| Layer | Name | Purpose |
|-------|------|---------|
| A | Scope Guardrails | MVP boundaries (dogs/cats only) |
| B | Field Completeness | Check required structured fields |
| C | ER Pre-check | Hard-route emergencies (skip LLM) |
| D | Input Quality | Sanitization, length limits |
| E | Safety Detection | Prompt injection detection |

---

## ✅ Output Guardrails (6 Layers)

| Layer | Name | Purpose |
|-------|------|---------|
| A | JSON Schema Validation | Ensure valid JSON structure |
| B | Content Safety | No diagnosis, no medication dosing |
| C | Risk Calibration | Prevent under-triage |
| D | Mandatory Disclaimer | Always include medical disclaimer |
| E | UI Constraints | List limits, character limits |
| F | Safe Fallback | Never break the app |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=sk-your-openai-key
PINECONE_API_KEY=your-pinecone-key
TAVILY_API_KEY=your-tavily-key  # Optional, for web search
```

### 3. Run the API Server

```bash
uvicorn api:app --reload --port 8000
```

API docs available at: http://localhost:8000/api/docs

### 4. Run Tests

```bash
python tests/run_all_tests.py
```

---

## 📋 Symptom Categories

| # | Category | Icon |
|---|----------|------|
| 1 | Toxic Ingestion & Poisoning | ☠️ |
| 2 | Stomach Upset | 🤢 |
| 3 | Itching & Skin Issues | 🔴 |
| 4 | Injury & Bleeding | 🩹 |
| 5 | Concerning Behaviour Changes | 😰 |
| 6 | Ears, Eyes, and Mouth | 👁️ |
| 7 | Breathing Issues | 😮‍💨 |
| 8 | Urinary & Genital | 💧 |
| 9 | Something Else | ❓ |

---

## 🚨 Risk Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **ER** | Emergency | Go to emergency vet NOW |
| **TODAY** | Urgent | Vet visit today |
| **SOON** | Non-urgent | Vet visit within 24-48 hours |
| **MONITOR** | Low-risk | Safe to monitor at home |

---

## ⚡ Emergency Hard-Routing

The following conditions trigger immediate ER response **without calling the LLM**:

- 🐱 Cat open-mouth breathing
- 💜 Blue/purple gums (cyanosis)
- 🐱 Male cat urinary straining (12+ hours)
- ⚡ Seizure > 5 minutes or 3+ in 24 hours
- 🫁 Bloat symptoms (distended abdomen + unproductive retching)
- 🩸 Heavy uncontrolled bleeding
- 👁️ Eye proptosis (eye popped out)

---

## 📤 Output JSON Schema

```json
{
  "risk_level": "ER | TODAY | SOON | MONITOR",
  "category": "one of 9 symptom categories",
  "red_flags": ["list of detected emergency indicators"],
  "reasoning_summary": ["1-3 brief reasons for the risk level"],
  "recommended_actions": ["3-6 actionable steps"],
  "what_to_monitor": ["2-5 signs to watch for"],
  "follow_up_questions": ["0-2 questions if info incomplete"],
  "nearby_vets": [{"name": "...", "distance_km": 1.2, ...}],
  "disclaimer": "This is not a veterinary diagnosis..."
}
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/categories` | GET | Get symptom categories |
| `/api/triage` | POST | Main triage assessment |
| `/api/chat` | POST | General pet health chat |
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/pet-profile` | POST/GET | Save/retrieve pet profile |
| `/api/nearby-vets` | POST | Find nearby vet clinics |
| `/api/triage-history` | GET | Get triage session history |

---

## 🛡️ Safety Principles

1. **No Diagnosis**: Only triage guidance, never definitive diagnosis
2. **No Medication Dosing**: Never provide drug dosages
3. **Conservative Escalation**: When uncertain, escalate to higher urgency
4. **Always Disclaimer**: Every response includes medical disclaimer
5. **Never Break**: Fallback responses ensure the app always works

---

## 🧪 Model Configuration

| Stage | Model | Purpose |
|-------|-------|---------|
| Agent | gpt-4-turbo | Autonomous tool selection & reasoning |
| Vision | gpt-4-vision-preview | Image analysis |
| Fallback | gpt-4.1 | Complex/uncertain cases |
