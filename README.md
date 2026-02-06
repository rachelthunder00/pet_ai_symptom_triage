# Fuzzy Friend: AI-Powered Pet Symptom Triage System

A pet health assistant that helps dog and cat owners assess symptoms, determine urgency, and find nearby veterinary care. Built with a Next.js frontend and a Python backend powered by LangChain/LangGraph agents and RAG (Retrieval-Augmented Generation).

This project was developed as a group assignment for ISBA 2421 (AI Enterprise).

**Team Members**: Pooja Shah, Yi Zhang, Rachel He, Srinidhi Jagannathan

---

## Key Features

| Feature | Description |
|---------|-------------|
| AI Triage Assessment | Structured symptom analysis with 4 urgency levels (ER, Today, Soon, Monitor) |
| Symptom Categories | 10 pre-defined categories for faster, more accurate triage |
| Patient Chart Memory | AI remembers past sessions to identify recurring issues |
| Multi-turn Chat | Follow-up questions in General Question mode with full context |
| Visual Analysis | Upload photos for GPT-4o image analysis |
| RAG Knowledge Base | 18,000+ veterinary records via Pinecone vector database |
| Nearby Vet Finder | Auto-locate open clinics using OpenStreetMap |
| Safety Guardrails | 5-layer input + 6-layer output validation |

---

## Architecture

The system uses a dual-agent design:

- **PetTriageAgent** (deterministic pipeline): Handles structured symptom triage. Runs a fixed sequence -- image analysis, red flag check, RAG retrieval, single LLM assessment -- with no autonomous tool selection. This ensures safety-critical steps are never skipped.
- **PetHealthAgent** (ReAct agent): Handles general pet health Q&A via LangGraph's `create_react_agent`, autonomously selecting tools based on the conversation.

```
User Input
    |
    v
[Input Guardrails - 5 layers]
  - Scope check (dogs/cats only)
  - Injection detection and sanitization
  - Off-topic detection
  - Field completeness validation
  - ER pre-check (hard-route emergencies)
    |
    v
[Router: /api/triage or /api/chat]
    |                    |
    v                    v
PetTriageAgent      PetHealthAgent
(Pipeline)          (ReAct Agent)
  1. Image analysis     Autonomous tool
  2. Red flag check     selection from:
  3. RAG retrieval      - vector_search
  4. LLM assessment     - web_search
                        - find_nearby_vets
                        - analyze_image
    |                    |
    v                    v
[Output Guardrails - 6 layers]
  - JSON schema validation
  - Content safety (no diagnosis/dosing)
  - Risk calibration (prevent under-triage)
  - Mandatory disclaimer
  - UI constraints (length limits)
  - Safe fallback
    |
    v
Final Response (TriageResponse JSON)
```

---

## Project Structure

```
pet_ai_symptom_triage/
├── start.sh                # One-click startup script
├── frontend/               # Next.js frontend
│   ├── app/                # App Router pages
│   │   ├── auth/           # Login / Register
│   │   ├── chat/           # Chat interface
│   │   ├── chatbot/        # Symptom checker UI
│   │   ├── onboarding/     # Pet profile setup
│   │   ├── profile/        # User profile
│   │   └── settings/       # App settings
│   ├── components/         # Reusable UI components
│   │   ├── AuthContext.tsx  # Authentication state
│   │   ├── PetContext.tsx   # Pet profile state
│   │   └── chatbot/        # Chat modal components
│   └── lib/                # API client utilities
└── pet_triage/             # Python backend
    ├── api.py              # FastAPI entry point
    ├── auth.py             # JWT authentication
    ├── database.py         # SQLite database operations
    ├── main.py             # Triage orchestration
    ├── core/               # Engine layer
    │   ├── agent.py        # PetTriageAgent (pipeline) + PetHealthAgent (ReAct)
    │   ├── tools.py        # Agent tools (vector search, red flags, vet finder, etc.)
    │   ├── rag_chain.py    # RAG pipeline (Pinecone + OpenAI embeddings)
    │   ├── image_analyzer.py   # GPT-4o image analysis
    │   ├── llm_setup.py    # OpenAI client, ER rules, model selection
    │   └── guardrails/     # Input and output validation
    │       ├── input.py    # 5-layer input guardrails
    │       └── output.py   # 6-layer output guardrails
    ├── shared/             # Data layer (single source of truth)
    │   ├── constants.py    # Enums, config, limits
    │   ├── prompts.py      # System prompts and templates
    │   ├── schemas.py      # Pydantic response schemas
    │   └── red_flags.py    # Emergency detection rules
    └── tests/              # Unit tests (52 tests)
        ├── run_all_tests.py
        └── test_*.py
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- API Keys:
  - `OPENAI_API_KEY` (required)
  - `GOOGLE_API_KEY` (optional, for Gemini web search)

### Quick Start

```bash
# One command to start both servers:
chmod +x start.sh && ./start.sh
```

### Manual Setup

1. Backend:

```bash
cd pet_triage
cp .env.example .env        # Edit .env with your API keys
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

2. Frontend:

```bash
cd frontend
npm install
npm run dev
```

3. Open http://localhost:3000 in your browser.

API docs available at http://localhost:8000/api/docs.

---

## Symptom Categories

Users select a category before describing symptoms for more accurate triage:

| Category | Examples |
|----------|----------|
| Toxic Ingestion and Poisoning | Ate chocolate, toxic plants |
| Stomach Upset | Vomiting, diarrhea |
| Itching and Skin Issues | Rashes, hair loss |
| Injury and Bleeding | Cuts, wounds, trauma |
| Concerning Behaviour Changes | Lethargy, aggression |
| Ears, Eyes, and Mouth | Eye discharge, ear infection |
| Breathing Issues | Coughing, wheezing |
| Urinary and Genital | Straining to urinate |
| Something Else | Other symptoms |
| General Question | Non-symptom pet health questions |

---

## Risk Levels

| Level | Meaning | Action |
|-------|---------|--------|
| ER | Emergency | Go to emergency vet immediately |
| TODAY | Urgent | Vet visit today |
| SOON | Non-urgent | Vet visit within 24-48 hours |
| MONITOR | Low-risk | Safe to monitor at home |

---

## Emergency Hard-Routing

The following conditions trigger an immediate ER response without calling the LLM:

- Cat open-mouth breathing
- Blue/purple gums (cyanosis)
- Male cat urinary straining (12+ hours)
- Seizure lasting more than 5 minutes or 3+ in 24 hours
- Bloat symptoms (distended abdomen + unproductive retching)
- Heavy uncontrolled bleeding
- Eye proptosis

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/categories` | GET | Get symptom categories |
| `/api/triage` | POST | Main triage assessment |
| `/api/chat` | POST | General pet health chat |
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/auth/me` | GET | Get current user |
| `/api/pet-profile` | POST/GET | Save/retrieve pet profile |
| `/api/nearby-vets` | POST | Find nearby vet clinics |
| `/api/triage/history` | GET | Get triage session history |
| `/api/triage/{session_id}` | GET | Get specific triage session |

---

## Output JSON Schema

```json
{
  "risk_level": "ER | TODAY | SOON | MONITOR",
  "category": "symptom category",
  "red_flags": ["detected emergency indicators"],
  "reasoning_summary": ["1-3 reasons for the risk level"],
  "recommended_actions": ["3-6 actionable steps"],
  "what_to_monitor": ["2-5 signs to watch for"],
  "follow_up_questions": ["0-2 clarifying questions"],
  "nearby_vets": [{"name": "...", "distance_km": 1.2}],
  "disclaimer": "This is not a veterinary diagnosis..."
}
```

---

## Safety Principles

1. **No Diagnosis**: Only triage guidance, never definitive diagnosis
2. **No Medication Dosing**: Never provides drug dosages
3. **Conservative Escalation**: When uncertain, escalate to higher urgency
4. **Always Disclaimer**: Every response includes a medical disclaimer
5. **Never Break**: Fallback responses ensure the app always works

---

## Running Tests

```bash
cd pet_triage
python -m pytest tests/ -v
```

---

## License

This project is for educational purposes as part of ISBA 2421.
