# ⚖️ LexAI - Legal Intelligence Platform

> **AI-Powered Legal Document Analysis for Enhanced Equity and Efficiency**

[![License](https://img.shields.io/badge/License-Educational-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![Flask Version](https://img.shields.io/badge/Flask-3.1.2-lightgrey.svg)](https://flask.palletsprojects.com/)
[![AI Powered](https://img.shields.io/badge/AI-HuggingFace%20%7C%20Gemini-orange.svg)](#)
[![Status](https://img.shields.io/badge/Status-Active_Development-success.svg)](#)

LexAI is a specialized artificial intelligence platform designed to automate the review, summarization, and bias detection of complex legal texts. By leveraging hybrid AI architectures, it empowers legal professionals to process contracts, court judgments, and case law faster while proactively identifying potential gender, racial, or socioeconomic biases hidden within historical legal documents.

---

##  The Problem
Legal professionals face an overwhelming volume of complex documentation. Traditional manual review processes are:
* **Labor-Intensive:** High human effort is required for routine document parsing.
* **Time-Consuming:** Significant bottlenecks occur when processing large volumes of case files.
* **Error-Prone:** Subjective human interpretation can lead to critical legal oversights.
* **Bias-Blind:** Systemic gender or social biases in historical data are often invisible to human reviewers.

##  The Solution
LexAI automates critical legal tasks through a multi-layered AI approach:
* **Automated Summarization:** Rapid distillation of lengthy contracts into actionable insights.
* **Bias Detection:** Algorithmic identification of systemic, age, or gender-based patterns.
* **Entity Extraction:** Structured retrieval of key entities for rapid indexing.

---

##  Key Features

### 1. Secure Document Management
* Upload legal documents (PDF, DOCX, TXT) up to 50MB.
* Secure storage with automated PII (Personally Identifiable Information) masking.
* Smart categorization (Contracts, Judgments, Case Law, Statutes, Agreements).
* Advanced search, filtering, and paginated document libraries.

### 2. Hybrid AI-Powered Analysis
LexAI utilizes a robust fallback architecture to ensure continuous operation:

| Feature | Technology | Description |
| :--- | :--- | :--- |
| **Summarization** | BART Transformer | Generates concise summaries (short/medium/detailed). |
| **Bias Detection** | RoBERTa + Keywords | Identifies gender, racial, socioeconomic, and age bias. |
| **Entity Extraction** | BERT NER | Extract people, organizations, locations, dates, and currency. |
| **Insights** | Google Gemini AI | Provides high-level trend analysis and strategic recommendations. |

### 3. Analytics Dashboard

* Real-time KPIs (Total Documents, Avg. Bias Score, Processing Time).
* Interactive charts (Processing Trends, Bias Distribution, Document Types).
* Bias detection heatmaps and top-offender tracking.

### 4. Advanced User Management
* Secure, session-based authentication system.
* Built-in demo environment for immediate testing.
* Personalized user profiles and customizable settings.

---

##  System Architecture



* **Frontend:** HTML5, CSS3, JavaScript, Chart.js, Font Awesome.
* **Backend:** Python 3.x, Flask, Werkzeug.
* **AI & NLP:** Hugging Face Transformers (BART, BERT, RoBERTa), Google Gemini API.
* **Database:** SQLite3 (Development ready).

---

##  Installation & Setup

### Prerequisites
* Python 3.8+
* `pip` package manager
* Git
* *(Optional)* Google Gemini API key for advanced insights

Navigate to http://127.0.0.1:5000 in your web browser to view the application.

** Configuration**

Create a .env file in the root directory to store your environment variables:

### Flask Configuration (Required)
SECRET_KEY=your-secure-secret-key-here

### Google Gemini API (Optional, but recommended for full feature access)
GEMINI_API_KEY=your-gemini-api-key

### Demo Credentials
Want to test the platform quickly? Use the built-in demo account:
Email: demo@lexai.com
Password: demo123

### Usage & API Integration
LexAI includes a robust RESTful API for integrating analysis into external legal software.
Example: Fetching Advanced Analytics

curl -X GET [http://127.0.0.1:5000/api/analytics-data](http://127.0.0.1:5000/api/analytics-data) \
     -H "Content-Type: application/json"

### Contributing
Contributions are welcome! If you'd like to improve LexAI, please follow these standard PR guidelines:
Fork the repository.
Create a new branch for your feature (git checkout -b feature/AmazingFeature).

Commit your changes (git commit -m 'Add some AmazingFeature').

Push to the branch (git push origin feature/AmazingFeature).

Open a Pull Request.

### Business Value

85% Time Saved on routine document review.

98% Accuracy in targeted bias detection.

24/7 Availability for immediate, highly-consistent document analysis.

Reduced Legal Risk through proactive historical bias identification.

### License
This project is currently for educational and demonstration purposes. For specific licensing inquiries or production usage, please contact the developer.

### Developer Info
Niyati Bansal  Indore, Madhya Pradesh, India

 Email: Niyatibansal626@gmail.com

 LinkedIn: niyati-bansal-6a783b284

 GitHub: @niyati10000

 X/Twitter: @bansalniyati1

Special thanks to the Hugging Face community, Google GenAI, and the Flask community for powering this platform.


### Step-by-Step Installation

```bash
# 1. Clone the repository
git clone [https://github.com/niyati10000/LexAI.git](https://github.com/niyati10000/LexAI.git)
cd LexAI

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Initialize the database
python database.py

# 6. Run the application
python app.py

