import sqlite3

def init_legal_db():
    conn = sqlite3.connect('legal_ai.db')
    cursor = conn.cursor()

    # Document Table (Ref: LegalDocument Class)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS legal_documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            doc_type TEXT, -- Contract or Judgment
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Summarization Table (Ref: Summary Class)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            summary_text TEXT NOT NULL,
            length_setting TEXT,
            FOREIGN KEY (doc_id) REFERENCES legal_documents (doc_id)
        )
    ''')

    # Bias Analysis Table (Ref: BiasReport Class)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bias_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            bias_score FLOAT,
            bias_type TEXT,
            explanation TEXT,
            FOREIGN KEY (doc_id) REFERENCES legal_documents (doc_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Legal AI Database initialized successfully.")

if __name__ == "__main__":
    init_legal_db()