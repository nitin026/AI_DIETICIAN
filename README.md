# AI Dietitian

Personalized Indian nutrition planning assistant powered by FastAPI, Streamlit, hosted or local LLMs, and RAG over ICMR-NIN dietary guidelines.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-ff4b4b)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![RAG](https://img.shields.io/badge/RAG-FAISS%20%2B%20ICMR--NIN-orange)](https://www.nin.res.in/)

> **Medical disclaimer:** AI Dietitian is an informational assistant only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider before making dietary or medication-related changes.

## Overview

AI Dietitian helps users build a personalized nutrition plan from their health profile, food preferences, pantry ingredients, budget, cooking skill, and regional Indian cuisine preference. The app computes daily nutrition targets, retrieves relevant dietary guideline context, generates a 7-day meal plan, validates pantry coverage, creates a grocery list, and provides a contextual AI nutrition coach.

The project is designed as a local-first prototype with clear API boundaries:

- **Frontend:** Streamlit multi-step user interface
- **Backend:** FastAPI service with Pydantic request and response contracts
- **LLM layer:** Groq, Gemini, HuggingFace, Ollama, or BioMistral through a unified service
- **RAG layer:** FAISS vector store built from the ICMR-NIN dietary guidelines PDF
- **Persistence:** SQLite database via SQLAlchemy for chat history, feedback, adherence logs, reminders, and profile context

## Key Features

- Personalized calorie, macro, hydration, and micronutrient targets
- Disease-aware nutrition adjustments for conditions such as diabetes, hypertension, anemia, thyroid issues, CKD, obesity, and osteoporosis
- Medication and food-interaction warning support
- 7-day Indian meal planning with breakfast, snacks, lunch, and dinner
- Regional cuisine, diet type, budget, cooking skill, allergies, likes, dislikes, and pantry-aware planning
- Grocery list generation with category grouping and estimated INR cost
- AI coach chat grounded in profile, meal plan, feedback, adherence history, and guideline context
- Meal feedback memory to improve future recommendations
- Adherence tracking for meals, hydration, sleep, weight, mood, and digestion
- Analytics dashboard with nutrient adequacy, adherence risk, and health score
- Reminder storage API for meal, hydration, supplement, grocery, and adherence reminders
- JSON and PDF export support from the Streamlit app

## Architecture

```text
User
  |
  v
Streamlit Frontend (localhost:8501)
  |
  | REST API
  v
FastAPI Backend (localhost:8000)
  |
  |-- Nutrition services: BMR, TDEE, macro and micronutrient targets
  |-- RAG retriever: FAISS vector store over ICMR-NIN PDF
  |-- Agents: clinical analysis, meal planning, ingredients, grocery list
  |-- Personalization: feedback memory, adherence summary, analytics
  |-- Storage: SQLite via SQLAlchemy
  |
  v
LLM Providers
  |-- Groq
  |-- Gemini
  |-- HuggingFace Router
  |-- Ollama / BioMistral
```

## Project Structure

```text
AI_Nutrient_2/
|-- backend/
|   |-- main.py                    # FastAPI app, middleware, routers, health checks
|   |-- config.py                  # Environment-backed application settings
|   |-- agents/                    # Clinical, meal planning, ingredient, grocery agents
|   |-- models/                    # Pydantic request and response schemas
|   |-- prompts/                   # LLM prompts for chat, nutrients, meals, substitutions
|   |-- rag/                       # PDF ingestion and vector retrieval
|   |-- routers/                   # API route modules
|   |-- services/                  # LLM, nutrition, storage, personalization, safety services
|   |-- utils/                     # Logging, validators, helper calculations
|   `-- requirements.txt
|-- frontend/
|   `-- streamlit_app.py           # Multi-step Streamlit application
|-- data/
|   |-- Dietary_Guidelines_ICMR_NIN.pdf
|   |-- app_state.json             # Local application state
|   `-- example_responses.json
|-- docs/
|   `-- database_migration.sql     # Future database schema reference
|-- rag/
|   `-- vector_store/              # FAISS index files
|-- logs/
|   `-- app.log
|-- requirements.txt
`-- README.md
```

## Quick Start

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

You can also install from the backend-specific file:

```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root. Example:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

HF_API_TOKEN=
HF_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.3

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
BIOMISTRAL_BASE_URL=http://localhost:11434
BIOMISTRAL_MODEL_ID=m/biomistral

VECTOR_STORE_TYPE=faiss
VECTOR_STORE_PATH=./rag/vector_store
PDF_PATH=./data/Dietary_Guidelines_ICMR_NIN.pdf
TOP_K_RETRIEVAL=5

BACKEND_URL=http://localhost:8000
```

Do not commit real API keys. Keep secrets in your local `.env` file or deployment secret manager.

### 4. Add the guideline PDF

Place the ICMR-NIN dietary guidelines PDF at:

```text
data/Dietary_Guidelines_ICMR_NIN.pdf
```

### 5. Build the vector store

Run this once after adding or changing the guideline PDF:

```bash
python -m backend.rag.ingest
```

### 6. Start the backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

API documentation will be available at:

```text
http://localhost:8000/docs
```

### 7. Start the frontend

Open a second terminal and run:

```bash
streamlit run frontend/streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API welcome response and disclaimer |
| `GET` | `/health` | Service health and active model information |
| `POST` | `/predict-nutrients` | Compute personalized nutrient targets |
| `POST` | `/generate-meal-plan` | Generate a 7-day meal plan |
| `POST` | `/validate-ingredients` | Validate pantry ingredients and suggest substitutions |
| `POST` | `/generate-grocery-list` | Generate a weekly grocery list with estimated costs |
| `POST` | `/chat` | Context-aware AI nutrition coach response |
| `POST` | `/chat/stream` | Streaming AI nutrition coach response |
| `GET` | `/chat/history/{user_id}` | Fetch stored chat history |
| `POST` | `/feedback` | Save meal feedback and preference signals |
| `GET` | `/feedback/{user_id}` | Fetch meal feedback history |
| `POST` | `/adherence` | Save adherence, hydration, sleep, mood, digestion, and weight log |
| `GET` | `/adherence/{user_id}` | Fetch adherence logs and summary |
| `POST` | `/analytics` | Generate nutrient adequacy, adherence, and health insights |
| `POST` | `/reminders` | Store reminder or notification configuration |
| `GET` | `/reminders/{user_id}` | Fetch stored reminders |
| `POST` | `/api/chat-image/log-adherence` | Log structured visual meal adherence from food photos |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | Primary provider: `groq`, `gemini`, `huggingface`, `ollama`, or `biomistral` |
| `GROQ_API_KEY` | empty | Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq chat model |
| `GEMINI_API_KEY` | empty | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model |
| `HF_API_TOKEN` | empty | HuggingFace token |
| `HF_MODEL_ID` | `mistralai/Mistral-7B-Instruct-v0.3` | HuggingFace Router model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Local Ollama model |
| `BIOMISTRAL_BASE_URL` | `http://localhost:11434` | BioMistral/Ollama-compatible server URL |
| `BIOMISTRAL_MODEL_ID` | `m/biomistral` | BioMistral model name |
| `VECTOR_STORE_TYPE` | `faiss` | Vector store type |
| `VECTOR_STORE_PATH` | `./rag/vector_store` | Vector index directory |
| `PDF_PATH` | `./data/Dietary_Guidelines_ICMR_NIN.pdf` | Source guideline PDF path |
| `TOP_K_RETRIEVAL` | `5` | Number of retrieved guideline chunks |
| `LLM_TIMEOUT_SECONDS` | `120` | LLM request timeout |
| `LLM_MAX_RETRIES` | `3` | Retry count for transient LLM failures |
| `BACKEND_URL` | `http://localhost:8000` | Backend URL used by Streamlit |

Task-specific provider overrides are also supported through variables such as `MEAL_PLAN_LLM_PROVIDER`, `CHAT_LLM_PROVIDER`, and corresponding fallback variables such as `MEAL_PLAN_FALLBACK_LLM_PROVIDER`.

## Streamlit Workflow

1. **Health Profile:** Age, gender, height, weight, activity, occupation, medical conditions, medications, and addiction frequency.
2. **Preferences and Pantry:** Diet type, regional cuisine, allergies, likes, dislikes, budget, cooking skill, and available pantry items.
3. **Nutrient Analysis:** BMR, TDEE, macro targets, micronutrients, disease notes, interaction warnings, and guideline references.
4. **Meal Plan:** 7-day Indian meal plan with recipes, macro breakdown, estimated cost, and meal feedback capture.
5. **Grocery List:** Weekly shopping list grouped by category with estimated total cost.
6. **AI Coach Chat:** Personalized chat for substitutions, budget changes, sodium reduction, high-protein options, and explanations.
7. **Adherence Calendar:** Meal completion, hydration, sleep, weight, mood, digestion, and notes.
8. **Health Insights:** Nutrient adequacy, adherence risk, health score, and improvement suggestions.

## Data and Persistence

The project currently stores runtime data in a SQLite database (`data/database.sqlite`) using SQLAlchemy. This preserves robust database contracts for:

- profiles
- chat messages
- meal feedback
- adherence logs
- reminders and notifications

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Pydantic v2, Uvicorn |
| Frontend | Streamlit, Plotly, FPDF2 |
| LLM Providers | Groq, Gemini, HuggingFace Router, Ollama, BioMistral |
| RAG | LangChain, SentenceTransformers, FAISS |
| Data Processing | pandas, NumPy, pypdf |
| Storage | SQLite via SQLAlchemy |
| Logging | Loguru |


## Plivo-Aligned Interview Demo

This project has been extended from a nutrition planner into a clinic communication workflow demo: an AI Dietitian Communication Assistant for Indian clinics. It demonstrates how programmable messaging, voice workflows, patient replies, reminders, risk escalation, and observability can support real patient follow-up.

### Demo Story

1. Create an automated meal, hydration, supplement, adherence, or follow-up reminder.
2. Dispatch active reminders through the mock SMS/WhatsApp/voice communication layer.
3. Simulate a patient reply such as `1`, `2`, `3`, `doctor call`, or `severe dizziness`.
4. Let the system classify intent, risk, and recommended action.
5. Use the voice assistant demo to simulate a transcribed phone call.
6. Review the Doctor Dashboard for adherence, high-risk alerts, and suggested next action.
7. Review Observability for reply rate, delivery success, channel usage, risk distribution, and demo readiness.

### Communication Features

- Mock SMS, WhatsApp, voice, and in-app message provider
- Outbound reminders and inbound reply handling
- Intent detection for completed, skipped, alternative requested, callback requested, reminder requested, and medical risk
- Automatic adherence logging from simple patient replies
- Voice assistant endpoint for transcript-based nutrition follow-up demos
- Doctor/dietitian dashboard with risk alerts and suggested actions
- Observability dashboard with communication KPIs, channel breakdowns, intent distribution, and operational alerts


### Communication Provider Adapter

The communication workflow uses a provider adapter boundary:

- `MockCommunicationProvider` keeps the demo local and deterministic.
- `PlivoReadyProvider` preserves the delivery contract for a future real Plivo integration.
- The rest of the application calls `send_message(...)` and does not need to know which provider is active.

Relevant environment variables:

```env
COMMUNICATION_PROVIDER=mock
PLIVO_AUTH_ID=
PLIVO_AUTH_TOKEN=
PLIVO_SOURCE_NUMBER=
```

Provider status is exposed through:

```text
GET /api/communications/provider/status
```

This keeps the project interview-safe because no paid communication API or real patient phone number is required for the demo, while still showing the engineering boundary needed for production provider integration.

### Interview-Relevant API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/communications/send-reminder` | Send and log a mock SMS/WhatsApp/voice/in-app message |
| `POST` | `/api/communications/inbound-reply` | Simulate inbound patient reply and classify intent/risk |
| `GET` | `/api/communications/history/{user_id}` | Fetch patient communication timeline |
| `GET` | `/api/communications/metrics` | Fetch communication metrics |
| `GET` | `/api/communications/provider/status` | Check active communication provider adapter |
| `POST` | `/reminders/dispatch-active` | Dispatch active reminders through the communication layer |
| `POST` | `/api/voice/assistant` | Run transcript-based voice assistant intent/risk workflow |
| `GET` | `/api/clinic/patient/{user_id}` | Doctor/dietitian patient dashboard summary |
| `GET` | `/api/observability/snapshot` | Operational observability snapshot |

### Why This Aligns With Communication Platform Work

The communication layer is intentionally provider-agnostic. The current `mock` provider stores messages locally for demo safety, but the architecture can be adapted to a real programmable communications provider by replacing the send/receive adapter while keeping the API contract, dashboard, observability, and patient workflows intact.

## Production Notes

- Replace permissive CORS settings with explicit frontend origins before production deployment.
- Move API keys out of source code and into environment variables or a secret manager.
- Add authentication and authorization before storing real user health data.
- Review all medical and nutrition guidance with qualified professionals before public use.
- Add automated tests for API contracts, nutrition calculations, and agent output validation.


## Author

Built by *Nitin Tiwari and Akshita Bhansali* as an AI-assisted Indian nutrition planning project.
