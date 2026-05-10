# 🥗 AI Dietitian — Personalised Indian Diet Planner

**Powered by BioMistral · FastAPI · Streamlit · RAG (ICMR-NIN 2024)**

> ⚠️ **Medical Disclaimer:** This system is an informational assistant only.
> It is **not** a substitute for professional medical advice, diagnosis, or treatment.

---

## Architecture Overview

```
User → Streamlit UI
         ↓ REST
    FastAPI Backend
    ├── Clinical Analyst Agent  ── Mifflin-St Jeor + RAG (ICMR-NIN) + BioMistral
    ├── Meal Planner Agent      ── RAG + BioMistral → 7-day plan + YouTube links
    ├── Ingredient Validator    ── BioMistral substitution logic
    └── Grocery Agent           ── Deterministic aggregation
              ↓
         BioMistral (Ollama / HuggingFace)
         FAISS / ChromaDB (ICMR-NIN embeddings)
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo>
cd ai_dietitian
cp .env.example .env
pip install -r backend/requirements.txt
```

### 2. Set Up BioMistral (Ollama — Recommended)

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull BioMistral
ollama pull biomistral

# Verify
ollama run biomistral "Hello"
```

### 3. Place the PDF

```bash
# Place the ICMR-NIN 2024 PDF in:
data/Dietary_Guidelines_ICMR_NIN.pdf
```

### 4. Ingest the PDF (one-time)

```bash
cd backend
python -m backend.rag.ingest
# This creates the FAISS index in backend/rag/vector_store/
```

### 5. Start the Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start the Frontend

```bash
streamlit run frontend/streamlit_app.py
```

Open **http://localhost:8501**

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `huggingface` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `biomistral` | Model name in Ollama |
| `HF_API_TOKEN` | — | HuggingFace token (if using HF) |
| `VECTOR_STORE_TYPE` | `faiss` | `faiss` or `chroma` |
| `CHUNK_SIZE` | `512` | PDF chunk size in tokens |
| `TOP_K_RETRIEVAL` | `5` | RAG passages per query |
| `LLM_TIMEOUT_SECONDS` | `120` | Max wait for LLM response |
| `LLM_MAX_RETRIES` | `3` | Retry attempts on failure |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/predict-nutrients` | Analyse health profile → nutrient targets |
| `POST` | `/generate-meal-plan` | Generate 7-day Indian meal plan |
| `POST` | `/validate-ingredients` | Substitute missing pantry items |
| `POST` | `/generate-grocery-list` | Build categorised grocery list |
| `GET` | `/health` | System health check |
| `GET` | `/docs` | Interactive Swagger UI |

---

## Sample API Call

```bash
curl -X POST http://localhost:8000/predict-nutrients \
  -H "Content-Type: application/json" \
  -d '{
    "health_profile": {
      "age": 35,
      "gender": "male",
      "height_cm": 175,
      "weight_kg": 80,
      "occupation": "Engineer",
      "activity_level": "moderately_active",
      "diseases": ["type-2 diabetes"],
      "medications": ["metformin 500mg"],
      "addictions": {"smoking": "never", "alcohol": "weekly", "tobacco": "never"}
    }
  }'
```

---

## Folder Structure

```
ai_dietitian/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Pydantic settings
│   ├── requirements.txt
│   ├── agents/
│   │   ├── clinical_analyst.py     # BMR + RAG + LLM nutrient analysis
│   │   ├── meal_planner.py         # 7-day meal generation
│   │   ├── ingredient_validator.py # Pantry vs meal comparison
│   │   └── grocery_agent.py        # Grocery list builder
│   ├── rag/
│   │   ├── ingest.py               # PDF chunking → vector store
│   │   ├── retriever.py            # Similarity search
│   │   └── vector_store/           # FAISS / ChromaDB index (auto-created)
│   ├── prompts/
│   │   ├── nutrient_prompt.py
│   │   ├── meal_prompt.py
│   │   └── substitution_prompt.py
│   ├── routers/
│   │   ├── nutrients_router.py
│   │   ├── meal_plan_router.py
│   │   ├── ingredient_router.py
│   │   └── grocery_router.py
│   ├── services/
│   │   ├── llm_service.py          # BioMistral interface + retry
│   │   ├── nutrition_service.py    # Mifflin-St Jeor calculations
│   │   └── youtube_service.py      # Recipe video lookup
│   ├── models/
│   │   ├── request_models.py       # Pydantic v2 request schemas
│   │   └── response_models.py      # Pydantic v2 response schemas
│   └── utils/
│       ├── logger.py               # Loguru config
│       ├── validators.py           # JSON extraction / sanitation
│       └── helpers.py              # BMR/TDEE formulae
├── frontend/
│   └── streamlit_app.py            # Multi-step Streamlit UI
├── data/
│   ├── Dietary_Guidelines_ICMR_NIN.pdf  ← place here
│   └── example_responses.json
└── .env.example
```

---

## Docker Deployment (Optional)

```dockerfile
# Dockerfile (backend)
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: "3.9"
services:
  backend:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./backend/rag/vector_store:/app/backend/rag/vector_store
  frontend:
    image: python:3.11-slim
    working_dir: /app
    command: streamlit run frontend/streamlit_app.py --server.port 8501
    ports: ["8501:8501"]
    env_file: .env
    depends_on: [backend]
```

---

## Production Checklist

- [ ] Place ICMR-NIN PDF in `data/`
- [ ] Run `python -m backend.rag.ingest`
- [ ] Set `LLM_PROVIDER` and model credentials in `.env`
- [ ] Set `BACKEND_URL` in `.env` for Streamlit
- [ ] Enable HTTPS via reverse proxy (nginx / caddy)
- [ ] Add authentication layer (OAuth2 / API keys)
- [ ] Configure log rotation (`logs/app.log`)
- [ ] Set up monitoring (Prometheus + Grafana or Sentry)

---

## Supported Diseases

The Clinical Analyst Agent handles dietary adjustments for:
`Type-1 & Type-2 Diabetes` · `Hypertension` · `Hypothyroidism` · `Hyperthyroidism`
`Obesity` · `Underweight` · `Anaemia` · `Osteoporosis` · `Chronic Kidney Disease`

Medication interactions recognised: `Metformin` · `Warfarin` · `Statins` · `Lisinopril` · `Levothyroxine`
