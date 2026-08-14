# ⚖️ LexAI - Legal Document Intelligence & Bias Analysis Platform

> **AI-Powered Contract Review, Bias Auditing, and Legal Risk Intelligence**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red.svg)](https://streamlit.io)
[![AI Engine](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://aistudio.google.com/)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed-brightgreen.svg)](#)

**LexAI** is an artificial intelligence platform designed to automate the analysis, summarization, and bias auditing of complex legal agreements, contracts, court judgments, and policy documents. Built with a **hybrid AI pipeline** (Google Gemini + deterministic rule fallback) and wrapped in an **Apple Frosted Acrylic UI**, LexAI delivers clause-by-clause legal risk assessments, protected-class discrimination checks (EEOC / Civil Rights), interactive document chatting, and full-spectrum analytics.

---

## 🚀 Quick Start (Streamlit)

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

### 2. Configure Gemini API Key
Create a `.env` file in the root directory (or `.streamlit/secrets.toml`):
```ini
GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Run Streamlit App
```bash
streamlit run streamlit_app.py
```
Open your browser to the URL displayed in your terminal (typically `http://localhost:8501`).

---

## ☁️ Deploying to Streamlit Community Cloud

1. **Push your code to GitHub** (Ensure `streamlit_app.py`, `requirements.txt`, and `.streamlit/config.toml` are present).
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with your GitHub account.
3. Click **New App**, select your repository, branch (`main`), and set Main file path to:
   ```text
   streamlit_app.py
   ```
4. Under **Advanced settings... -> Secrets**, add your Gemini API key:
   ```toml
   GEMINI_API_KEY = "your-google-gemini-api-key-here"
   ```
5. Click **Deploy!**

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
| **App Framework** | Streamlit (Python 3.10+) |
| **Backend / Web Server** | Python 3.13, Flask (Optional local API server) |
| **AI / NLP** | Google Gemini (`google-genai`), Regex-NER, Keyword Frequency Fallback |
| **Document Parsers** | `pypdf` (PDF Parsing), `python-docx` (Word Documents), `txt` |
| **Frontend Styling** | Apple Frosted Acrylic & Clean Light CSS Design System |

---

## 📂 Project Architecture

```
Legal_bais/
├── streamlit_app.py            # Streamlit Application Entrypoint
├── requirements.txt            # Python Dependencies
├── .env                        # Local Environment Secrets
├── .streamlit/
│   ├── config.toml             # Streamlit Theme & Server Settings
│   └── secrets.toml.example    # Streamlit Secrets Template
│
├── services/                   # Business Logic & AI Pipeline
│   ├── ai_service.py           # Gemini Analyzer & Fallback Engine
│   ├── file_service.py         # PDF, DOCX, and TXT Extraction
│   └── worker.py               # Background Task Queue
│
├── test_documents/             # Test Files for Verification
│   └── full_test_contract.txt  # Multi-category Bias & PII Contract
└── tests/                      # Automated Pytest Suite
```

---

## 📄 License
This project is developed for educational and professional legal technology analysis.
