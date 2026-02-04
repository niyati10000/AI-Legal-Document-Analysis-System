from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('legal_ai.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    documents = conn.execute('SELECT * FROM legal_documents').fetchall()
    conn.close()
    return render_template('index.html', documents=documents)

# Document Ingestion & Preprocessing (Ref: Activity Diagram 1)
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        doc_type = request.form['doc_type']

        # Logic for PII Masking & OCR can be added here (Ref: State Diagram)
        conn = get_db_connection()
        conn.execute('INSERT INTO legal_documents (title, content, doc_type) VALUES (?, ?, ?)',
                     (title, content, doc_type))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)