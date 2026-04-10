# 🧾 AI-Powered B2B Invoice Tracking & GST Compliance System

A hackathon-ready FastAPI backend for automated B2B invoice management,
GST return generation, fraud detection, and an AI-powered GST chatbot.

---

## 🏗️ Architecture

```
backend/
├── app/
│   ├── main.py                    ← FastAPI app entry point + lifespan
│   ├── api/
│   │   ├── dependencies.py        ← Shared FastAPI dependencies (role guards)
│   │   └── routes/
│   │       ├── auth_routes.py     ← Sign up, sign in, business registration
│   │       ├── invoice_routes.py  ← Upload, share, accept/reject, payments
│   │       └── gst_routes.py      ← Returns, chatbot, risk analysis, dashboard
│   ├── core/
│   │   ├── config.py              ← Pydantic Settings (all env vars)
│   │   └── security.py            ← Supabase JWT verification middleware
│   ├── models/
│   │   ├── invoice.py             ← Domain models: Invoice, LineItem, enums
│   │   ├── user.py                ← User, Business domain models
│   │   └── gst.py                 ← GSTReturn, TaxSummary domain models
│   ├── schemas/
│   │   ├── invoice.py             ← Pydantic v2 request/response schemas
│   │   ├── user.py                ← User/business schemas
│   │   └── gst.py                 ← GST return and chat schemas
│   ├── services/
│   │   ├── gemini_client.py       ← Google Gemini API wrapper
│   │   ├── invoice_analyzer.py    ← OCR text → structured JSON via Gemini
│   │   ├── invoice_service.py     ← Full invoice lifecycle orchestration
│   │   ├── gst_service.py         ← GSTR-1 / GSTR-3B generation
│   │   └── payment_service.py     ← Payment tracking & analytics
│   ├── agents/
│   │   ├── validator_agent.py     ← Invoice Validator Agent (multi-step)
│   │   ├── gst_agent.py           ← GST Assistant Agent (RAG + multi-turn)
│   │   └── risk_agent.py          ← Risk Detection Agent (Neo4j + Gemini)
│   ├── db/
│   │   └── supabase_client.py     ← Supabase client + CRUD helpers
│   ├── graph/
│   │   ├── neo4j_client.py        ← Neo4j async driver + schema init
│   │   └── graph_queries.py       ← Cypher: relationships, fraud detection
│   ├── rag/
│   │   ├── rag_pipeline.py        ← FAISS index build + RAG query pipeline
│   │   └── knowledge/
│   │       └── gst_core_rules.md  ← GST knowledge base for chatbot
│   ├── ocr/
│   │   └── ocr_service.py         ← Tesseract OCR + pdfplumber extraction
│   └── utils/
│       ├── gstin_utils.py         ← GSTIN validation, state lookup, PAN extract
│       └── inventory_utils.py     ← Inventory update from accepted invoices
├── db/
│   └── schema.sql                 ← Supabase PostgreSQL migration
├── .env.example                   ← All required environment variables
├── requirements.txt               ← Python dependencies
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI (Python 3.11+) |
| Database | Supabase (PostgreSQL + Auth) |
| Graph DB | Neo4j 5.x |
| LLM | Google Gemini 1.5 Pro |
| OCR | Tesseract + pdfplumber |
| Vector Search | FAISS + SentenceTransformers |
| Auth | Supabase JWT (HS256) |

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Python 3.11+
python --version

# Tesseract OCR (Ubuntu/Debian)
sudo apt-get install -y tesseract-ocr poppler-utils

# Tesseract OCR (macOS)
brew install tesseract poppler
```

### 2. Clone & Install
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables
```bash
cp .env.example .env
# Edit .env with your actual credentials:
#   - SUPABASE_URL, SUPABASE_KEY, SUPABASE_JWT_SECRET
#   - GEMINI_API_KEY
#   - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
```

### 4. Database Setup
```bash
# Run db/schema.sql in your Supabase SQL Editor
# (Dashboard → SQL Editor → New Query → paste schema.sql → Run)
```

### 5. Start Neo4j (Docker)
```bash
docker run \
  --name neo4j-gst \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:5
```

### 6. Run the API
```bash
uvicorn app.main:app --reload --port 8000
```

API Docs: http://localhost:8000/docs

---

## 🔄 Core Invoice Flow

```
User uploads PDF
      │
      ▼
OCR Service (Tesseract / pdfplumber)
      │  raw text
      ▼
Gemini Invoice Analyzer
      │  structured JSON
      ▼
Validator Agent
  ├── GSTIN regex + state code check
  ├── Tax calculation re-verification (CGST/SGST vs IGST)
  ├── Duplicate detection (DB lookup)
  └── Gemini semantic check
      │  ValidationReport
      ▼
Supabase (store invoice + validation result)
      │
      ▼
Neo4j (create Business nodes + Invoice edges)
      │
      ▼
Seller shares → Buyer accepts/rejects/modifies
      │
      ▼
Inventory updated (on acceptance)
      │
      ▼
GST Return Generation (GSTR-1 / GSTR-3B)
```

---

## 🔐 Authentication Flow

```
POST /auth/signup  →  Supabase creates auth.users entry + returns JWT
POST /auth/signin  →  Returns JWT access token
                         │
                         ▼ (attach as Bearer token)
GET  /invoices/seller/my-invoices
                         │
                         ▼
FastAPI middleware decodes JWT via SUPABASE_JWT_SECRET
Injects user dict → route handler
```

---

## 🤖 AI Agents

### ValidatorAgent (`agents/validator_agent.py`)
Multi-step pipeline: GSTIN check → Tax math → Duplicate DB lookup → Gemini semantic audit  
Returns `ValidationReport` with confidence score and structured issues.

### GSTAgent (`agents/gst_agent.py`)
RAG-powered multi-turn chatbot. Detects intent, routes to specialised handlers or FAISS retrieval.  
Session state maintained in-memory (swap for Redis in production).

### RiskAgent (`agents/risk_agent.py`)
Neo4j graph queries for circular fraud, invoice splitting, high-frequency invoicing.  
Gemini generates plain-English narrative + recommended actions.

---

## 📊 Key API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/signin` | Sign in, get JWT |
| POST | `/auth/register-business` | Register GST business |
| POST | `/invoices/upload` | Upload + OCR + AI validate invoice |
| POST | `/invoices/{id}/share` | Seller shares with buyer |
| PATCH | `/invoices/{id}/status` | Buyer accept/reject/modify |
| POST | `/invoices/payments/record` | Record payment |
| GET | `/invoices/{id}/payments` | Payment history + balance |
| POST | `/gst/returns/gstr1` | Generate GSTR-1 |
| POST | `/gst/returns/gstr3b` | Generate GSTR-3B |
| GET | `/gst/dashboard/{gstin}` | Real-time tax dashboard |
| POST | `/gst/chat` | RAG GST chatbot |
| GET | `/gst/risk/{gstin}` | Fraud risk analysis |

---

## 🧠 RAG Knowledge Base

Add `.txt` or `.md` files to `app/rag/knowledge/` to extend the chatbot's knowledge.  
The FAISS index rebuilds automatically on next startup.

Currently included: `gst_core_rules.md` (comprehensive GST rules, rates, GSTIN format,
return types, ITC, penalties, e-way bills, RCM, composition scheme).

---

## 🔮 Extending for Hackathon

| Feature | Where to add |
|---|---|
| Credit/Debit note processing | `invoice_service.py` + new route |
| WhatsApp invoice sharing | New service in `services/` |
| GSTIN live verification (GST API) | `utils/gstin_utils.py` |
| Scheduled overdue reminders | Background task in `main.py` |
| PDF invoice generation | New utility with `reportlab` |
| E-way bill integration | New agent in `agents/` |
| ML risk scoring | Extend `risk_agent.py` |