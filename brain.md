# 🧠 LexAI - Master System Context & Architecture Brain

> **Comprehensive Developer & AI Context Manual**  
> *Pass this document to any AI model or developer for instant, complete understanding of the LexAI codebase.*

---

## ⚡ Quick AI Context & Summary
- **App Type:** AI-powered Legal Document Intelligence, Contract Review, and Protected-Class Bias Auditing Platform.
- **Backend Framework:** Python 3.10+ with Flask 3.1, Jinja2 Templates, SQLAlchemy ORM, and Gunicorn (Production WSGI).
- **AI & NLP Pipeline:** 
  1. **Primary Cloud LLM:** Google Gemini (`google-genai` SDK) for structured clause extraction, risk assessment, and interactive document chat.
  2. **Local Hugging Face Pipelines:** Lazy-loaded `facebook/bart-large-cnn` (Summarization), `dslim/bert-base-NER` (Entity Recognition), and `unitary/toxic-bert` (Bias Classification).
  3. **Deterministic Fallback:** Keyword scoring, regex NER, and rule-based protected-class bias matcher (Gender, Race, Age, Disability, Socioeconomic).
  4. **Privacy:** Automated PII masking (SSN, credit card, phone, email) before transmitting text to external AI services.
- **Database:** SQLite (default) / PostgreSQL via `Flask-SQLAlchemy`. Auto-initializes and seeds demo account `demo@lexai.com` / `demo123`.
- **Frontend & Design:** Custom Apple Porcelain Frosted Glass & Bento-Grid UI System (`static/css/theme.css`, `templates/`).

---

## 📂 Codebase File Structure & Responsibilities

```
Legal_bais/
├── app.py                      # Flask App initialization, global routes, error handlers, DB seeding, entry point
├── config.py                   # Environment configurations (DevConfig, ProdConfig, TestConfig)
├── database.py                 # SQLAlchemy ORM Data Models (User, LegalDocument, BiasReport, Summary, etc.)
├── requirements.txt            # Python dependencies (Flask, google-genai, gunicorn, pypdf, python-docx, etc.)
├── brain.md                    # Master AI Architecture & Developer Context Manual (This File)
├── README.md                   # User-facing installation and setup documentation
├── .env                        # Local environment variables (GEMINI_API_KEY, FLASK_SECRET_KEY)
│
├── blueprints/                 # Flask Modular Controllers & Route Handlers
│   ├── auth.py                 # Login, Registration, Logout, Password Hashing (scrypt)
│   ├── dashboard.py            # Upload, Document Details, Library, Analytics, Export, PDF Generation
│   ├── settings.py             # User Profile, AI Engine selection, API Key generation, Audit Logs
│   └── api.py                  # Public REST v1 endpoints & Interactive Document Chat API
│
├── services/                   # Business Logic & NLP Engines
│   ├── ai_service.py           # Gemini API Client, Hugging Face Transformers, Fallback Rule Engine, PII Sanitizer
│   ├── file_service.py         # File extraction (PDF via pypdf, DOCX via python-docx, TXT)
│   └── worker.py               # Background async document processing thread queue
│
├── static/                     # Assets & Custom Stylesheets
│   ├── css/theme.css           # Apple Porcelain Frosted Acrylic Design Tokens & Responsive Bento Grid
│   └── js/main.js              # Client-side interaction & async REST handlers
│
├── templates/                  # Jinja2 HTML View Templates
│   ├── base.html               # Base layout with navbar and sidebar navigation
│   ├── index.html              # Landing page
│   ├── dashboard.html           # Document processing status & analytics summary
│   ├── document_detail.html    # Full clause summary, bias report, entity tags, & live AI chatbot
│   ├── library.html            # Document archive with search & filtering
│   ├── analytics.html          # Global legal bias & risk analytics dashboard
│   ├── settings.html           # API keys, profile management, and audit log exports
│   ├── login.html / register.html # Authentication templates
│   └── 404.html / 500.html     # Custom error pages
│
├── test_documents/             # Test contracts for validation
│   └── full_test_contract.txt  # Multi-category contract sample with bias and PII data
└── tests/                      # Automated Test Suite (Pytest)
    ├── test_api.py             # REST API endpoint tests
    └── test_auth.py            # Authentication & session tests
```

---

## 🏗️ System Architecture & Data Flow

```mermaid
graph TD
    User[User / Web Client] --> Flask[Flask Application]
    Flask --> Auth[auth_bp - Session & Auth]
    Flask --> Dash[dashboard_bp - UI Views & Uploads]
    Flask --> Settings[settings_bp - User Settings & API Keys]
    Flask --> API[api_bp - REST v1 & Chatbot API]
    
    Flask --> DB[(SQLAlchemy ORM - SQLite / Postgres)]
    Dash --> WorkerQueue[Background Worker Queue (worker.py)]
    WorkerQueue --> FileService[file_service.py - Text Extraction]
    WorkerQueue --> AIService[ai_service.py - NLP Engine]
    
    AIService --> PII[PII Sanitizer Engine]
    PII --> Gemini[Google Gemini API]
    PII --> LocalHF[Local Transformers - BART/BERT]
    PII --> RuleFallback[Deterministic Keyword & Regex Fallback]
```

---

## 🗄️ Database Schema Summary (`database.py`)

1. **`User`**: User accounts (`id`, `email`, `password_hash`, `full_name`, `role`, `organization`, `bio`, `created_at`).
2. **`UserSetting`**: Per-user preferences (`default_summary_length`, `bias_threshold`, `pii_masking_enabled`, `ai_model`, `legal_domain`).
3. **`LegalDocument`**: Document metadata (`title`, `doc_type`, `file_path`, `raw_text`, `status`: `queued`/`extracting`/`analyzing`/`completed`/`failed`).
4. **`DocumentVersion`**: Revision tracking for document text diffs.
5. **`Summary`**: Structured summary (`key_provisions`, `parties`, `monetary_terms`, `compliance_status`, `summary_text`).
6. **`BiasReport`**: Bias audit results (`overall_score`, `primary_category`, `gender_bias_score`, `racial_bias_score`, `age_bias_score`, `disability_bias_score`, `socioeconomic_bias_score`, `flags_json`).
7. **`Entity`**: Named entities (`entity_type`, `text`, `confidence_score`).
8. **`ApiKey`**: User API access keys stored via SHA-256 hash.
9. **`AuditLog`**: Security compliance trail (`action`, `details`, `ip_address`, `timestamp`).
10. **`Tag` / `DocumentTag`**: Tagging system for documents.

---

## 🤖 AI & Bias Audit Pipeline Details (`services/ai_service.py`)

- **5 Protected-Class Audits:** Scans for subtle and overt bias across:
  - **Gender** (e.g. gendered roles, maternal penalties, exclusionary language)
  - **Racial/Ethnic** (e.g. accent/origin penalties, discriminatory clauses)
  - **Age** (e.g. `digital native`, compulsory retirement language)
  - **Disability** (e.g. non-essential physical demands, lack of reasonable accommodation)
  - **Socioeconomic** (e.g. zip-code filtering, credit score exclusions)
- **Interactive Document Chat (`POST /api/v1/chat`):** Injects document text + active clause summary into prompt context for accurate, zero-hallucination legal Q&A.
- **Privacy & PII Sanitizer:** Automatically redacts SSNs (`XXX-XX-XXXX`), credit card numbers, phone numbers, and email addresses before external API transmission.

---

## 🛠️ How to Run & Verify

1. **Start Local Development Server:**
   ```bash
   python app.py
   ```
   *(App auto-creates tables and seeds demo account `demo@lexai.com` / `demo123` at `http://localhost:5000`)*

2. **Run Production Server (Gunicorn):**
   ```bash
   gunicorn app:app
   ```

3. **Execute Automated Pytest Suite:**
   ```bash
   pytest -v
   ```

---

## 🎯 Guidance for AI Assistants
When assisting with this codebase:
1. Always preserve the clean modular Flask Blueprint structure (`blueprints/`).
2. Keep business logic and AI prompts in `services/ai_service.py`.
3. Keep database schema definitions in `database.py`.
4. Ensure all database mutations use `db.session.commit()` and wrap in try/except with `db.session.rollback()` on error.
5. Use `gunicorn` as the WSGI web server for cloud deployments (Render, Railway, Koyeb, VPS).
