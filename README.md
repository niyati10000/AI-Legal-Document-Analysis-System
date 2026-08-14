# ⚖️ LexAI - Legal Document Intelligence & Bias Analysis Platform

> **AI-Powered Contract Review, Bias Auditing, and Legal Risk Intelligence**

[![Python Version](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://python.org)
[![Flask Version](https://img.shields.io/badge/Flask-3.1.2-lightgrey.svg)](https://flask.palletsprojects.com/)
[![AI Engine](https://img.shields.io/badge/AI-Google%20Gemini%203.5%20Flash-orange.svg)](https://aistudio.google.com/)
[![Design System](https://img.shields.io/badge/Design-Apple%20VisionOS%20%26%20Porcelain%20Acrylic-cyan.svg)](#)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed-brightgreen.svg)](#)

**LexAI** is an artificial intelligence platform designed to automate the analysis, summarization, and bias auditing of complex legal agreements, contracts, court judgments, and policy documents. Built with a **hybrid AI pipeline** (Google Gemini 3.5 Flash + deterministic rule fallback) and wrapped in an **Apple Frosted Porcelain Acrylic UI**, LexAI delivers clause-by-clause legal risk assessments, protected-class discrimination checks (EEOC / Civil Rights), interactive document chatting, and full-spectrum analytics.

---

## 📸 Key Features & Capabilities

### 1. 🤖 Document Intelligence & "Ask LexAI" Chatbot
* **Structured Clause Synthesis**: Generates explanatory, clause-by-clause summaries categorizing parties, indemnification thresholds, termination conditions, and payment schedules.
* **Document Chatbot (`Ask LexAI`)**: In-session legal assistant that answers ad-hoc questions against uploaded documents, cites specific clauses, calculates liabilities, and proposes neutral amendments.
* **Interactive Document Annotator**: Real-time monospace text inspector with color-coded entity chips and clause flags.

### 2. 🛡️ Comprehensive Bias & Compliance Auditing
* **5 Protected-Class Audits**: Scans documents for subtle, overt, or systemic bias across **Gender**, **Racial/Ethnic**, **Age**, **Disability**, and **Socioeconomic** dimensions.
* **EEOC / Civil Rights Verification**: Gauges compliance against standard anti-discrimination statutes.
* **Neutral Remediation Engine**: Pinpoints biased contract language, assigns risk severity (Low / Medium / High), and outputs legally sound remediation recommendations.

### 3. 🔒 Privacy & Automated PII Masking
* **Confidentiality Pre-Processing**: Automatically detects and masks sensitive Personally Identifiable Information (SSNs, credit card numbers, personal emails, phone numbers, individual names) before transmitting data.
* **Audit Trail**: Cryptographically logs every document scan, download, and modification with timestamp and IP address.

### 4. 🎨 Apple VisionOS & macOS Porcelain Design System
* **Porcelain Acrylic Glassmorphism**: Clean light-mode aesthetic with soft aurora glows, high-contrast typography, and fluid responsive grids.
* **Interactive Profile & Master-Detail Settings**: Profile management modal, customizable AI models (Gemini 3.5 Flash vs Pro vs Local), legal domain presets, and downloadable CSV audit logs.
* **REST API & In-Browser Playground**: Integrated developer console to test live API payloads directly within the browser.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.13, Flask 3.1.2, Flask-SQLAlchemy (ORM), Werkzeug |
| **AI / NLP** | Google Gemini 3.5 Flash (`google-genai`), Regex-NER, Keyword Frequency Fallback |
| **Document Parsers** | `pypdf` (PDF Parsing), `python-docx` (Word Documents), `txt` |
| **Frontend** | Vanilla HTML5 / ES6 JavaScript, Apple Frosted Porcelain CSS, Chart.js |
| **Security** | `scrypt` password hashing, `SHA-256` hashed API Tokens, PII sanitization |
| **Database** | SQLite (Dev) / PostgreSQL compatible (Production) |

---

## 📂 Project Architecture

```
Legal_bais/
├── app.py                      # Flask Server Bootstrapper & DB Seeding
├── config.py                   # Environment & Database Configuration
├── database.py                 # SQLAlchemy ORM Models (User, Document, AuditLog)
├── requirements.txt            # Python Dependencies
├── .env                        # Gemini API Key & Environment Secrets
│
├── blueprints/                 # Modular Route Controllers
│   ├── auth.py                 # User Login, Registration & Session Handling
│   ├── dashboard.py            # Dashboard, Library & Analytics Pages
│   ├── settings.py             # Settings, Profile Modal, API Key Management & CSV Export
│   └── api.py                  # REST API v1 Endpoints & Chatbot Service
│
├── services/                   # Business Logic & Background Workers
│   ├── ai_service.py           # Gemini 3.5 Flash Analyzer & Fallback Engine
│   ├── file_service.py         # PDF, DOCX, and TXT Extraction
│   └── worker.py               # Asynchronous Multi-threaded Queue Worker
│
├── static/                     # Assets & Styling
│   ├── css/theme.css           # Apple Porcelain Acrylic Design System
│   └── js/                     # Client-side scripts & live polling
│
├── templates/                  # Jinja2 Layout Templates
│   ├── base.html               # Master Acrylic Navigation Layout
│   ├── dashboard.html          # Bento Analytics Dashboard
│   ├── analysis.html           # Full Tabbed Report & "Ask LexAI" Chatbot
│   ├── settings.html           # Master-Detail Settings & REST Playground
│   ├── documents.html          # Document Library & Filtering
│   ├── analytics.html          # System KPIs & Bias Distribution Charts
│   └── upload.html             # Drag-and-Drop / Paste Document Upload
│
├── test_documents/             # Comprehensive Test Files
│   └── full_test_contract.txt  # Multi-category Bias & PII Verification Contract
└── tests/                      # Automated Pytest Suite (11 Tests)
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
* Python 3.10+ (Recommended Python 3.13)
* `git`

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/niyati10000/AI-Legal-Document-Analysis-System.git
cd AI-Legal-Document-Analysis-System

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in the root directory:
```ini
FLASK_ENV=dev
SECRET_KEY=your-secure-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
```

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 5. Default Demo Credentials
| Field | Value |
|---|---|
| **Email** | `demo@lexai.com` |
| **Password** | `demo123` |

---

## 🧪 Running Automated Tests

Run the full pytest test suite:
```bash
pytest -v
```
All 11 unit & integration tests verify authentication, API key validation, version diffing, document parsing, and analysis page rendering.

---

## 🌐 REST API Endpoints

### 1. Analyze Document
`POST /api/v1/analyze` (Multipart Form Data)
* **Headers**: `Authorization: Bearer <API_KEY>`
* **Parameters**: `title`, `content` (or `file`), `analysis_type` (`both|summarize|bias`), `summary_length` (`short|medium|detailed`), `pii_masking` (`true|false`).

### 2. Ask LexAI Chatbot
`POST /api/v1/chat` (JSON)
* **Payload**:
```json
{
  "doc_id": 1,
  "message": "What is the non-compete duration in this contract?",
  "history": []
}
```

### 3. Export Audit Trail
`GET /settings/export-audit-log`
* Downloads a CSV of all user activity and document actions.

---

## 📄 License
This project is developed for educational and professional legal technology analysis.
