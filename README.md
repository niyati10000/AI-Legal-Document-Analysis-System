# ⚖️ LexAI - Legal Document Intelligence & Bias Analysis Platform

> **AI-Powered Contract Review, Bias Auditing, and Legal Risk Intelligence**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-green.svg)](https://flask.palletsprojects.com)
[![AI Engine](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://aistudio.google.com/)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed-brightgreen.svg)](#)

**LexAI** is an artificial intelligence platform designed to automate the analysis, summarization, and bias auditing of complex legal agreements, contracts, court judgments, and policy documents. Built with a **hybrid AI pipeline** (Google Gemini + deterministic rule fallback) and an interactive web interface, LexAI delivers clause-by-clause legal risk assessments, protected-class discrimination checks (EEOC / Civil Rights), interactive document chatting, and full-spectrum analytics.

---
**Hostedlink**
https://niyati1.pythonanywhere.com/

**Last Updated**: August 18, 2026  
**Status**: ✅ Production Stable

## 🚀 Quick Start (Flask)

### 1. Installation
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

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```ini
GEMINI_API_KEY=your-gemini-api-key-here
FLASK_SECRET_KEY=your-secret-key
```

### 3. Run Application
```bash
python app.py
```
Open your browser to `http://localhost:5000`.

---

## 📸 Key Features & Capabilities

### 1. 🤖 Document Intelligence & Legal Chatbot
* **Structured Clause Synthesis**: Generates explanatory, clause-by-clause summaries categorizing parties, indemnification thresholds, termination conditions, and payment schedules.
* **Interactive Document Chat**: In-session legal assistant that answers ad-hoc questions against uploaded documents, cites specific clauses, and proposes neutral amendments.

### 2. 🛡️ Comprehensive Bias & Compliance Auditing
* **5 Protected-Class Audits**: Scans documents for subtle, overt, or systemic bias across **Gender**, **Racial/Ethnic**, **Age**, **Disability**, and **Socioeconomic** dimensions.
* **EEOC / Civil Rights Verification**: Gauges compliance against standard anti-discrimination statutes.
* **Neutral Remediation Engine**: Pinpoints biased contract language, assigns risk severity (Low / Medium / High), and outputs legally sound remediation recommendations.

### 3. 🔒 Privacy & Automated PII Masking
* **Confidentiality Pre-Processing**: Automatically detects and masks sensitive Personally Identifiable Information (SSNs, credit card numbers, personal emails, phone numbers) before transmitting data.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **App Framework** | Flask 3.1, Jinja2 Templates |
| **Database** | Flask-SQLAlchemy (SQLite / PostgreSQL) |
| **WSGI Server** | Gunicorn (Production), Werkzeug (Development) |
| **AI / NLP** | Google Gemini (`google-genai`), Regex-NER, Keyword Frequency Fallback |
| **Document Parsers** | `pypdf` (PDF Parsing), `python-docx` (Word Documents), `txt` |

---

## 📂 Project Architecture

```
Legal_bais/
├── app.py                      # Flask Application Entrypoint
├── config.py                   # Application Configurations
├── database.py                 # SQLAlchemy Database Models
├── requirements.txt            # Python Dependencies
├── .env                        # Local Environment Secrets
│
├── blueprints/                 # Flask Blueprints & Controllers
│   ├── api.py                  # API Endpoints
│   ├── auth.py                 # Authentication Routes
│   ├── dashboard.py            # Main Dashboard & Document Views
│   └── settings.py             # User Settings & API Configuration
│
├── services/                   # Business Logic & AI Pipeline
│   ├── ai_service.py           # Gemini Analyzer & Fallback Engine
│   ├── file_service.py         # PDF, DOCX, and TXT Extraction
│   └── worker.py               # Background Task Queue
│
├── static/                     # CSS, JS, and Asset Files
├── templates/                  # HTML Templates (Jinja2)
├── test_documents/             # Test Files for Verification
└── tests/                      # Automated Pytest Suite
```

---

## 📄 License
This project is developed for educational and professional legal technology analysis.
