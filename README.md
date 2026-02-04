# ⚖️ AI Legal Document Analysis System

![Status](https://img.shields.io/badge/Status-Active-success) ![Language](https://img.shields.io/badge/Language-Python_3-blue) ![AI Model](https://img.shields.io/badge/Model-BERT_%2F_Transformers-orange) ![Architecture](https://img.shields.io/badge/Architecture-Three--Tier-purple)

**A specialized Artificial Intelligence platform designed to automate the review, summarization, and bias detection of complex legal texts.**

---

## 1. Problem Statement & Business Case

Legal professionals face an overwhelming volume of complex documentation—contracts, case law, and judgments. The traditional manual review process is fraught with inefficiencies:

* **Labor-Intensive:** High human effort required for routine document parsing.
* **Time-Consuming:** Bottlenecks in processing large volumes of case files.
* **Error-Prone:** Subjective interpretation can lead to critical legal oversights.
* **Bias-Blind:** Systemic gender or social biases in historical data are often invisible to human reviewers.

### 🎯 The Solution
We have engineered an AI-powered system that automates these critical tasks to enhance equity and efficiency:
1.  **Automated Summarization:** Rapid distillation of lengthy contracts into actionable insights.
2.  **Bias Detection:** Algorithmic identification of systemic or gender-based patterns in judicial outcomes.
3.  **Entity Extraction:** Structured retrieval of key entities (names, dates, case numbers) for rapid indexing.

---

## 2. Core Logic & Workflow

The system implements a rigorous **Document Ingestion & Preprocessing** workflow to ensure data integrity before AI analysis:

* **Validation:** Automatically checks uploaded files to ensure they meet format (PDF/TXT) and size constraints.
* **Preprocessing:**
    * **OCR:** Extracts text from scanned documents.
    * **Text Cleaning:** Removes noise and formatting errors.
    * **PII Masking:** Redacts Personally Identifiable Information to ensure privacy compliance.
* **Analysis:** Triggers the backend AI models to generate summaries and detect systemic bias.

---

## 3. System Architecture & Design

The system follows a robust **Three-Tier Architecture** to ensure modularity, security, and scalability.

### A. Architectural Tiers
1.  **Presentation Tier (Frontend):** A web-based interface built with HTML5 and Flask templates for seamless document ingestion.
2.  **Application Tier (Backend):** The core logic engine orchestrating specialized AI modules (Summarization, Bias Detection).
3.  **Data Tier (Database):** A relational storage layer (SQLite/PostgreSQL) for structured results and document archives.

### B. Visual Modeling (UML)
The design is validated through rigorous technical modeling:

* **Class Diagram:** Defines the schema for `LegalDocument`, `SummarizationModel`, and `BiasReport` entities.
* **Sequence Diagram:** Visualizes the synchronous communication between the UI, the AI Engine, and the Database during a "Summarize" request.

---

## 4. Technical Implementation

This section details the source code structure and the technologies powering the AI engine.

### 🛠️ Technology Stack
* **Core Backend:** Python 3.x / Flask Framework.
* **AI & NLP Engine:**
    * **BERT:** For context-aware entity extraction.
    * **Transformers:** For abstractive text summarization.
    * **Torch:** Deep learning framework support.
* **Data Layer:** SQLite3 for relational data management.

### 📂 Repository Structure
| File/Directory | Description |
| :--- | :--- |
| `app.py` | Central orchestrator handling API routes and the Summarization Pipeline. |
| `database.py` | Initialization script for the `legal_ai.db` schema. |
| `/templates` | Contains the Frontend views (`index.html`, `upload.html`). |

---

## 5. Installation & Setup

Follow these steps to deploy the system locally.

### Step 1: Clone and Configure
```bash
git clone [https://github.com/your-repo/legal-ai-system.git](https://github.com/your-repo/legal-ai-system.git)

** System Access & Interface**
Once the server is running, you can access the application interfaces using the specific URLs below:

🖥️ Dashboard View
Status: Active System Monitor

URL: http://127.0.0.1:5000/

Function: Main landing page for system status and recent reports.

📤 Document Ingestion & Upload
Status: Ingestion Interface

URL: http://127.0.0.1:5500/templates/upload.html

Function: Specialized interface for uploading legal PDF/Text documents for processing.

**upload html referance image**
<img width="1911" height="1001" alt="Screenshot 2026-02-04 204356" src="https://github.com/user-attachments/assets/5209d8a6-1dd5-4df1-8a99-ff4756fe9d9c" />

**index html referance image**
<img width="1919" height="1001" alt="Screenshot 2026-02-04 204348" src="https://github.com/user-attachments/assets/d4e98be9-d548-4bdd-a810-633db3269801" />

cd legal-ai-system
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
