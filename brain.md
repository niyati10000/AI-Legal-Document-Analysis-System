# 🧠 LexAI - Architecture & Developer Context Brain

This document serves as the master developer context ledger for **LexAI**. It captures the system architecture, design decisions, data models, AI pipeline strategies, and API contracts for AI agents and human contributors.

---

## ⚖️ 1. Platform Overview
**LexAI** is an AI-powered Legal Intelligence and Compliance Auditing platform. Its mission is to streamline legal document parsing, detect protected-class discrimination and bias in agreements (Gender, Race, Age, Disability, Socioeconomic), and provide conversational intelligence ("Ask LexAI") over complex legal contracts.

---

## 🏗️ 2. Architectural Blueprint

### Layer Breakdown:
```mermaid
graph TD
    Client[Web Browser / REST Client] --> Flask[Flask Web Application (Blueprints)]
    Flask --> Auth[auth_bp - Scrypt Auth & Sessions]
    Flask --> Dash[dashboard_bp - Dashboard, Library, Analytics]
    Flask --> Settings[settings_bp - Profile, Engine & Keys]
    Flask --> API[api_bp - REST v1 & Chatbot Service]
    
    Flask --> DB[(SQLite / PostgreSQL ORM)]
    Flask --> Worker[Background Worker Thread (Queue)]
    Worker --> AIService[services/ai_service.py]
    AIService --> Gemini[Google Gemini 3.5 Flash]
    AIService --> Fallback[Deterministic Rule Engine / Regex NER]
```

---

## 🗄️ 3. Database Schema (SQLAlchemy ORM)

| Model | Table | Description |
|---|---|---|
| **`User`** | `users` | User accounts with email, scrypt `password_hash`, `full_name`, `role`, `bio`, and `organization`. |
| **`UserSetting`** | `user_settings` | Per-user preferences: `default_summary_length`, `bias_threshold`, `pii_masking_enabled`, `ai_model`, `legal_domain`. |
| **`LegalDocument`** | `legal_documents` | Parent document entity tracking `title`, `doc_type`, and processing lifecycle status (`queued`, `extracting`, `analyzing`, `completed`, `failed`). |
| **`DocumentVersion`** | `document_versions` | Versioned textual revisions allowing revision tracking and diff comparisons. |
| **`Summary`** | `summaries` | AI generated structured legal summary and provisions breakdown. |
| **`BiasReport`** | `bias_reports` | Overall bias score, primary category, per-class breakdown (Gender, Racial, Age, Disability, Socioeconomic), and neutral remediation flags. |
| **`Entity`** | `entities` | Named entities extracted from text (People, Organizations, Locations, Dates, Monetary Amounts, Legal Terms). |
| **`ApiKey`** | `api_keys` | Developer authentication tokens stored as one-way `SHA-256` hashes with usage timestamps. |
| **`AuditLog`** | `audit_logs` | Compliance log tracking all user actions (`LOGIN`, `UPLOAD`, `UPDATE_PROFILE`, `API_KEY_GEN`, etc.) with IP and timestamps. |
| **`Tag` & `DocumentTag`** | `tags` / `document_tags` | Many-to-many relationship supporting customized tags. |

---

## 🤖 4. AI & NLP Pipeline Architecture

### Primary Engine: Google Gemini 3.5 Flash
* **Model Designation**: `gemini-3.5-flash`
* **JSON Schema Extraction**: Enforces structured JSON output containing `key_provisions`, `parties`, `monetary_terms`, `compliance_status`, and `flags` with specific remediation text.
* **Document Chat (`POST /api/v1/chat`)**: Injects the full document context, latest summary, and conversation history buffer (up to 6 turns) into the prompt context for precise clause citation.

### Secondary Engine: Deterministic Fallback Analyzer
* **Summarization**: Extractive sentence ranker scoring sentences by legal keyword density, monetary values, dates, and named entity presence.
* **Bias Detection**: Multi-category weighted phrase-matcher (e.g. `aggressive woman`, `digital native`, `wheelchair-bound`, `inner-city`) with zero false-random inflation.
* **Entity Extraction**: Context-aware regex extraction for parties, dates, monetary values, and US locations.

### Privacy & PII Sanitizer
* Automatically redacts SSNs (`XXX-XX-XXXX`), credit card numbers, phone numbers, and email addresses before invoking external LLM APIs.

---

## 🎨 5. Apple Porcelain Design System (`static/css/theme.css`)

* **Color Tokens**:
  * Canvas: `#f8fafc` with subtle pastel aurora gradients (`#fed7aa`, `#fbcfe8`, `#e9d5ff`, `#bfdbfe`).
  * Surface: Pure White Frosted Porcelain Acrylic (`#ffffff`, `border-radius: 24px - 32px`).
  * Accents: Apple Azure (`#0284c7`), Soft Lilac (`#7e22ce`), Soft Amber (`#b45309`), Emerald (`#10b981`).
* **Layout Structure**: Responsive 12-column Bento grid with `minmax(0, 1fr)` containment to prevent layout overflow.
* **No Harsh Dark Clashes**: Pure white porcelain code consoles with clean syntax styling.

---

## 📡 6. Key REST API Routes

1. `POST /api/v1/analyze`: Upload file or raw text for asynchronous processing. Supports `Bearer <API_KEY>` auth.
2. `POST /api/v1/chat`: Conversational legal assistant query with document context injection.
3. `GET /api/v1/documents/<doc_id>/status`: Real-time processing status polling endpoint.
4. `GET /api/v1/analytics`: Aggregate statistics (total docs, average bias score, document type breakdown).
5. `GET /settings/export-audit-log`: Download user activity trail in CSV format.

---

## 🧪 7. Automated Test Suite
* Pytest test suite located in `tests/test_api.py` and `tests/test_auth.py`.
* Run tests with: `pytest -v`
* Tests verify session auth, duplicate email guards, API key validation, version diffing, document polling, and template rendering.
