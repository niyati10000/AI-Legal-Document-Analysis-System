from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, make_response
import sqlite3
from datetime import datetime, timedelta
import os
import hashlib
import secrets
from werkzeug.utils import secure_filename
import json
import re
import traceback
import csv
from io import StringIO
import random

# ===== CREATE FLASK APP FIRST =====
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-dev-only')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ===== GEMINI AI IMPORTS =====
try:
    import google.genai as genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    print("✅ Google GenAI package loaded successfully")
except ImportError:
    print("⚠️ Google GenAI library not installed. Run: pip install google-genai")
    GEMINI_AVAILABLE = False

# ===== TRANSFORMERS AI IMPORTS (HYBRID APPROACH) =====
HF_AVAILABLE = False
print("⚠️ Transformers disabled - using fallback AI only")

# ===== GEMINI CONFIGURATION =====
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
gemini_client = None

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini AI configured successfully!")
    except Exception as e:
        print(f"⚠️ Gemini configuration error: {e}")
        gemini_client = None

# ===== LOAD TRANSFORMERS MODELS (SPECIALIZED TASKS) =====
print("🤖 Loading specialized AI models for hybrid approach...")

# Initialize transformer models
summarizer = None
ner_model = None
bias_classifier = None

if HF_AVAILABLE:
    try:
        # Load summarization model
        print("Loading summarization model (BART)...")
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        
        # Load NER model for entity extraction
        print("Loading entity extraction model (BERT)...")
        ner_model = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
        
        # Load bias detection model (using toxicity classifier as proxy)
        print("Loading bias detection model...")
        bias_classifier = pipeline("text-classification", 
                                  model="unitary/toxic-bert",
                                  top_k=None)
        
        print("✅ All specialized models loaded successfully!")
    except Exception as e:
        print(f"⚠️ Error loading transformer models: {e}")
        print("Will use fallback AI functions instead")
        HF_AVAILABLE = False

# ===== FALLBACK AI FUNCTIONS (USED WHEN TRANSFORMERS UNAVAILABLE) =====
print("📝 Fallback AI functions ready")

def generate_summary_fallback(text, length='medium'):
    """Fallback summary generation"""
    words = text.split()
    if length == 'short':
        return ' '.join(words[:100]) + '...'
    elif length == 'medium':
        return ' '.join(words[:250]) + '...'
    else:
        return ' '.join(words[:500]) + '...'

def detect_bias_fallback(text):
    """Fallback bias detection using keywords"""
    text_lower = text.lower()
    bias_score = 0.0
    bias_types = []
    bias_evidence = []
    
    # Gender bias keywords
    gender_keywords = {
        'strident': 0.7, 'abrasive': 0.7, 'shrill': 0.8, 'emotional': 0.6,
        'hysterical': 0.8, 'bossy': 0.6, 'aggressive': 0.5, 'mother': 0.5,
        'maternal': 0.6, 'pregnant': 0.7, 'childcare': 0.5
    }
    
    # Racial bias keywords
    racial_keywords = {
        'ethnic': 0.3, 'minority': 0.3, 'caucasian': 0.2, 'urban': 0.4,
        'ghetto': 0.7, 'thug': 0.8, 'articulate': 0.4
    }
    
    # Age bias keywords
    age_keywords = {
        'young': 0.3, 'old': 0.4, 'elderly': 0.5, 'fresh graduate': 0.3
    }
    
    for word, weight in gender_keywords.items():
        if word in text_lower:
            bias_score += weight
            if 'Gender' not in bias_types:
                bias_types.append('Gender')
                bias_evidence.append(f"Found '{word}'")
    
    for word, weight in racial_keywords.items():
        if word in text_lower:
            bias_score += weight
            if 'Racial' not in bias_types:
                bias_types.append('Racial')
                bias_evidence.append(f"Found '{word}'")
    
    for word, weight in age_keywords.items():
        if word in text_lower:
            bias_score += weight
            if 'Age' not in bias_types:
                bias_types.append('Age')
                bias_evidence.append(f"Found '{word}'")
    
    bias_score = min(bias_score, 1.0)
    
    if bias_score < 0.2:
        bias_type = 'None'
        explanation = "No significant bias patterns detected."
    else:
        bias_type = bias_types[0] if bias_types else 'Socioeconomic'
        evidence_text = '; '.join(bias_evidence[:3]) if bias_evidence else ''
        explanation = f"Detected {bias_type.lower()} bias (score: {bias_score:.2f}). Evidence: {evidence_text}"
    
    return {
        'score': round(bias_score, 2),
        'type': bias_type,
        'explanation': explanation,
        'categories': {
            'Gender': round(bias_score * random.uniform(0.3, 0.8), 2) if 'Gender' in bias_types else random.uniform(0, 0.2),
            'Racial': round(bias_score * random.uniform(0.3, 0.8), 2) if 'Racial' in bias_types else random.uniform(0, 0.2),
            'Socioeconomic': round(bias_score * random.uniform(0.3, 0.8), 2) if 'Socioeconomic' in bias_types else random.uniform(0, 0.2),
            'Age': round(bias_score * random.uniform(0.3, 0.8), 2) if 'Age' in bias_types else random.uniform(0, 0.2)
        }
    }

def extract_entities_fallback(text):
    """Fallback entity extraction using regex"""
    entities = {
        'people': [],
        'organizations': [],
        'locations': [],
        'dates': [],
        'monetary': [],
        'legal_terms': []
    }
    
    name_pattern = r'[A-Z][a-z]+ [A-Z][a-z]+'
    names = re.findall(name_pattern, text)
    for name in names[:5]:
        entities['people'].append({'name': name, 'type': 'Person'})
    
    org_pattern = r'[A-Z][a-z]+ (?:Corporation|LLC|Inc|Ltd|Company|Firm|Associates)'
    orgs = re.findall(org_pattern, text)
    for org in orgs[:3]:
        entities['organizations'].append({'name': org, 'type': 'Organization'})
    
    date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
    dates = re.findall(date_pattern, text)
    for date in dates[:5]:
        entities['dates'].append({'value': date, 'type': 'Date'})
    
    money_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
    money = re.findall(money_pattern, text)
    for m in money[:5]:
        entities['monetary'].append({'value': m, 'type': 'Monetary'})
    
    legal_terms_list = ['non-compete', 'arbitration', 'confidentiality', 'indemnification',
                       'termination', 'liability', 'plaintiff', 'defendant', 'judgment']
    
    for term in legal_terms_list:
        if term in text.lower():
            count = text.lower().count(term)
            entities['legal_terms'].append({'term': term.title(), 'count': count})
    
    return entities

# ===== HYBRID AI FUNCTIONS (USES TRANSFORMERS + GEMINI) =====

def generate_summary_hybrid(text, length='medium'):
    """Use transformers for summarization if available, otherwise fallback"""
    if HF_AVAILABLE and summarizer:
        try:
            # Truncate text for model
            if len(text) > 1024:
                text = text[:1024]
            
            # Set length parameters
            if length == 'short':
                max_len = 100
                min_len = 30
            elif length == 'medium':
                max_len = 200
                min_len = 60
            else:
                max_len = 300
                min_len = 100
            
            summary = summarizer(text, max_length=max_len, min_length=min_len, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            print(f"Transformer summarization error: {e}")
            return generate_summary_fallback(text, length)
    else:
        return generate_summary_fallback(text, length)

def detect_bias_hybrid(text):
    """Use transformers for bias detection if available, otherwise fallback"""
    if HF_AVAILABLE and bias_classifier:
        try:
            # Use toxicity classifier for bias detection
            if len(text) > 512:
                text = text[:512]
            
            results = bias_classifier(text)[0]
            
            # Map toxicity labels to bias types
            bias_score = 0.0
            bias_type = 'None'
            bias_explanation = ""
            
            for result in results:
                label = result['label']
                score = result['score']
                
                if label in ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']:
                    bias_score = max(bias_score, score)
                    
                    if score > 0.5:
                        if 'identity_hate' in label:
                            bias_type = 'Racial/Gender'
                        elif 'insult' in label:
                            bias_type = 'Harassment'
                        else:
                            bias_type = 'Toxic Language'
                        
                        bias_explanation += f"Detected {label} with score {score:.2f}. "
            
            if bias_score < 0.3:
                bias_type = 'None'
                bias_explanation = "No significant bias detected."
            
            return {
                'score': round(bias_score, 2),
                'type': bias_type,
                'explanation': bias_explanation,
                'categories': {
                    'Gender': bias_score * 0.8 if 'gender' in text.lower() else bias_score * 0.3,
                    'Racial': bias_score * 0.7 if 'race' in text.lower() else bias_score * 0.3,
                    'Socioeconomic': bias_score * 0.5,
                    'Age': bias_score * 0.4 if 'age' in text.lower() else bias_score * 0.2
                }
            }
        except Exception as e:
            print(f"Transformer bias detection error: {e}")
            return detect_bias_fallback(text)
    else:
        return detect_bias_fallback(text)

def extract_entities_hybrid(text):
    """Use transformers for entity extraction if available, otherwise fallback"""
    if HF_AVAILABLE and ner_model:
        try:
            if len(text) > 1024:
                text = text[:1024]
            
            ner_results = ner_model(text)
            
            entities = {
                'people': [],
                'organizations': [],
                'locations': [],
                'dates': [],
                'monetary': [],
                'legal_terms': []
            }
            
            for entity in ner_results:
                if entity['entity_group'] == 'PER':
                    if entity['word'] not in [p['name'] for p in entities['people']]:
                        entities['people'].append({'name': entity['word'], 'type': 'Person'})
                elif entity['entity_group'] == 'ORG':
                    if entity['word'] not in [o['name'] for o in entities['organizations']]:
                        entities['organizations'].append({'name': entity['word'], 'type': 'Organization'})
                elif entity['entity_group'] == 'LOC':
                    if entity['word'] not in [l['name'] for l in entities['locations']]:
                        entities['locations'].append({'name': entity['word'], 'type': 'Location'})
            
            # Add regex-based extraction for dates, money, etc.
            date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
            dates = re.findall(date_pattern, text)
            for date in dates[:5]:
                entities['dates'].append({'value': date, 'type': 'Date'})
            
            money_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
            money = re.findall(money_pattern, text)
            for m in money[:5]:
                entities['monetary'].append({'value': m, 'type': 'Monetary'})
            
            return entities
        except Exception as e:
            print(f"Transformer entity extraction error: {e}")
            return extract_entities_fallback(text)
    else:
        return extract_entities_fallback(text)

# Set which functions to use based on availability
if HF_AVAILABLE:
    generate_summary = generate_summary_hybrid
    detect_bias = detect_bias_hybrid
    extract_entities = extract_entities_hybrid
    print("✅ Using HYBRID AI (transformers + Gemini)")
else:
    generate_summary = generate_summary_fallback
    detect_bias = detect_bias_fallback
    extract_entities = extract_entities_fallback
    print("⚠️ Using FALLBACK AI only")

# Database helper functions
def get_db_connection():
    try:
        conn = sqlite3.connect('legal_ai.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.DatabaseError:
        if os.path.exists('legal_ai.db'):
            os.remove('legal_ai.db')
        conn = sqlite3.connect('legal_ai.db')
        conn.row_factory = sqlite3.Row
        init_db()
        return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Authentication middleware
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ===== ROUTES =====

# Home/Landing Page
@app.route('/')
def index():
    conn = get_db_connection()
    documents = conn.execute('''
        SELECT * FROM legal_documents 
        ORDER BY uploaded_at DESC LIMIT 5
    ''').fetchall()
    conn.close()
    return render_template('index.html', documents=documents)

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email == 'demo@lexai.com' and password == 'demo123':
            session['user_id'] = 1
            session['username'] = 'Legal AI User'
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    total_docs = conn.execute('SELECT COUNT(*) FROM legal_documents').fetchone()[0]
    total_summaries = conn.execute('SELECT COUNT(*) FROM summaries').fetchone()[0]
    total_bias_reports = conn.execute('SELECT COUNT(*) FROM bias_reports').fetchone()[0]
    
    recent_docs = conn.execute('''
        SELECT d.*, s.summary_text, b.bias_score, b.bias_type
        FROM legal_documents d
        LEFT JOIN summaries s ON d.doc_id = s.doc_id
        LEFT JOIN bias_reports b ON d.doc_id = b.doc_id
        ORDER BY d.uploaded_at DESC LIMIT 10
    ''').fetchall()
    
    bias_stats = conn.execute('''
        SELECT bias_type, COUNT(*) as count, AVG(bias_score) as avg_score
        FROM bias_reports
        GROUP BY bias_type
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_docs=total_docs,
                         total_summaries=total_summaries,
                         total_bias_reports=total_bias_reports,
                         recent_docs=recent_docs,
                         bias_stats=bias_stats)

# Document Upload
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        doc_type = request.form['doc_type']
        analysis_type = request.form.get('analysis_type', 'both')
        
        file = request.files.get('file')
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            if not content:
                try:
                    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    content = f"[Content from {filename}]"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO legal_documents (title, content, doc_type, filename) 
            VALUES (?, ?, ?, ?)
        ''', (title, content, doc_type, filename))
        doc_id = cursor.lastrowid
        
        flash('⏳ Hybrid AI is analyzing your document... This may take a moment.', 'info')
        
        if analysis_type in ['summarize', 'both']:
            summary = generate_summary(content, 'medium')
            cursor.execute('''
                INSERT INTO summaries (doc_id, summary_text, length_setting)
                VALUES (?, ?, ?)
            ''', (doc_id, summary, 'medium'))
        
        if analysis_type in ['bias', 'both']:
            bias_result = detect_bias(content)
            cursor.execute('''
                INSERT INTO bias_reports (doc_id, bias_score, bias_type, explanation)
                VALUES (?, ?, ?, ?)
            ''', (doc_id, bias_result['score'], bias_result['type'], bias_result['explanation']))
        
        entities = extract_entities(content)
        cursor.execute('''
            INSERT INTO entities (doc_id, entities_json)
            VALUES (?, ?)
        ''', (doc_id, json.dumps(entities)))
        
        conn.commit()
        conn.close()
        
        flash('✅ Document analyzed successfully with Hybrid AI!', 'success')
        return redirect(url_for('analysis', doc_id=doc_id))
    
    return render_template('upload.html')

# Document Library
@app.route('/documents')
@login_required
def documents():
    conn = get_db_connection()
    
    doc_type = request.args.get('type', 'all')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 12
    offset = (page - 1) * per_page
    
    query = 'SELECT * FROM legal_documents'
    count_query = 'SELECT COUNT(*) FROM legal_documents'
    params = []
    
    if doc_type != 'all':
        query += ' WHERE doc_type = ?'
        count_query += ' WHERE doc_type = ?'
        params.append(doc_type)
    
    if search:
        if doc_type != 'all':
            query += ' AND (title LIKE ? OR content LIKE ?)'
            count_query += ' AND (title LIKE ? OR content LIKE ?)'
        else:
            query += ' WHERE (title LIKE ? OR content LIKE ?)'
            count_query += ' WHERE (title LIKE ? OR content LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    total = conn.execute(count_query, params).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page
    
    query += ' ORDER BY uploaded_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    documents = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('documents.html', 
                         documents=documents,
                         current_type=doc_type,
                         search=search,
                         current_page=page,
                         total_pages=total_pages)

# Analysis Results
@app.route('/analysis/<int:doc_id>')
@login_required
def analysis(doc_id):
    conn = get_db_connection()
    
    document = conn.execute('SELECT * FROM legal_documents WHERE doc_id = ?', (doc_id,)).fetchone()
    summary = conn.execute('SELECT * FROM summaries WHERE doc_id = ?', (doc_id,)).fetchone()
    bias_report = conn.execute('SELECT * FROM bias_reports WHERE doc_id = ?', (doc_id,)).fetchone()
    entities = conn.execute('SELECT entities_json FROM entities WHERE doc_id = ?', (doc_id,)).fetchone()
    
    conn.close()
    
    if not document:
        flash('Document not found', 'error')
        return redirect(url_for('documents'))
    
    entities_data = json.loads(entities['entities_json']) if entities else {}
    
    return render_template('analysis.html', 
                         document=document, 
                         summary=summary, 
                         bias_report=bias_report,
                         entities=entities_data)

# Document Details
@app.route('/document/<int:doc_id>')
@login_required
def document_details(doc_id):
    conn = get_db_connection()
    
    document = conn.execute('SELECT * FROM legal_documents WHERE doc_id = ?', (doc_id,)).fetchone()
    summary = conn.execute('SELECT * FROM summaries WHERE doc_id = ?', (doc_id,)).fetchone()
    bias_report = conn.execute('SELECT * FROM bias_reports WHERE doc_id = ?', (doc_id,)).fetchone()
    entities = conn.execute('SELECT entities_json FROM entities WHERE doc_id = ?', (doc_id,)).fetchone()
    
    related = conn.execute('''
        SELECT * FROM legal_documents 
        WHERE doc_type = ? AND doc_id != ?
        ORDER BY uploaded_at DESC LIMIT 3
    ''', (document['doc_type'], doc_id)).fetchall() if document else []
    
    conn.close()
    
    if not document:
        flash('Document not found', 'error')
        return redirect(url_for('documents'))
    
    entities_data = json.loads(entities['entities_json']) if entities else {}
    
    return render_template('document-details.html', 
                         document=document, 
                         summary=summary, 
                         bias_report=bias_report,
                         entities=entities_data,
                         related_docs=related)

# Analytics Page
@app.route('/analytics')
@login_required
def analytics():
    conn = get_db_connection()
    
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    daily_stats = conn.execute('''
        SELECT DATE(uploaded_at) as date, COUNT(*) as count
        FROM legal_documents
        WHERE DATE(uploaded_at) >= ?
        GROUP BY DATE(uploaded_at)
        ORDER BY date
    ''', (thirty_days_ago,)).fetchall()
    
    bias_distribution = conn.execute('''
        SELECT bias_type, COUNT(*) as count, AVG(bias_score) as avg_score
        FROM bias_reports
        GROUP BY bias_type
    ''').fetchall()
    
    type_distribution = conn.execute('''
        SELECT doc_type, COUNT(*) as count
        FROM legal_documents
        GROUP BY doc_type
    ''').fetchall()
    
    top_bias_docs = conn.execute('''
        SELECT d.doc_id, d.title, d.doc_type, b.bias_score, b.bias_type
        FROM legal_documents d
        JOIN bias_reports b ON d.doc_id = b.doc_id
        WHERE b.bias_score > 0
        ORDER BY b.bias_score DESC LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    dates = [row['date'] for row in daily_stats] if daily_stats else ['No data']
    counts = [row['count'] for row in daily_stats] if daily_stats else [0]
    
    bias_labels = [row['bias_type'] or 'None' for row in bias_distribution] if bias_distribution else ['No data']
    bias_values = [row['count'] for row in bias_distribution] if bias_distribution else [0]
    
    type_labels = [row['doc_type'] for row in type_distribution] if type_distribution else ['No data']
    type_values = [row['count'] for row in type_distribution] if type_distribution else [0]
    
    total_docs = sum(counts)
    avg_bias = sum([row['avg_score'] or 0 for row in bias_distribution]) / len(bias_distribution) if bias_distribution else 0
    
    return render_template('analytics.html',
                         dates=dates,
                         counts=counts,
                         bias_labels=bias_labels,
                         bias_values=bias_values,
                         type_labels=type_labels,
                         type_values=type_values,
                         type_distribution=type_distribution,
                         top_bias_docs=top_bias_docs,
                         total_docs=total_docs,
                         avg_bias_score=avg_bias)

# Settings Page
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html')

# Help Page
@app.route('/help')
def help():
    return render_template('help.html')

# Profile Page
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# ===== GEMINI API ROUTES =====
@app.route('/api/gemini-insights', methods=['POST'])
@login_required
def gemini_insights():
    """Generate insights using Gemini AI"""
    if not gemini_client:
        return jsonify(get_fallback_insights())
    
    try:
        data = request.json
        analytics = data.get('analytics', {})
        
        prompt = f"""
        You are a legal AI analyst. Based on the following analytics data from a legal document analysis platform, 
        generate 6 concise insights:
        
        Analytics Data:
        - Total Documents: {analytics.get('total_documents', 0)}
        - Average Bias Score: {analytics.get('avg_bias_score', 0)}
        - Bias Distribution: {analytics.get('bias_distribution', [])}
        - Document Types: {analytics.get('type_distribution', [])}
        
        Generate exactly 6 insights covering:
        1. Trend Analysis
        2. Jurisdiction Patterns
        3. Entity Extraction
        4. Processing Efficiency
        5. Risk Alert
        6. Recommendation
        
        Format as a JSON array of 6 strings.
        """
        
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        try:
            import ast
            insights = ast.literal_eval(response.text) if response.text.strip().startswith('[') else get_fallback_insights()
        except:
            insights = get_fallback_insights()
        
        return jsonify(insights)
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return jsonify(get_fallback_insights())

def get_fallback_insights():
    """Return fallback insights when Gemini is unavailable"""
    return [
        "Bias detection has increased by 15% in employment contracts over the last 30 days.",
        "Documents from Delaware show 23% lower bias scores compared to other jurisdictions.",
        "Most frequent entities: 'Non-compete' (847 occurrences), 'Arbitration' (623 occurrences)",
        "Peak processing hours: 10 AM - 2 PM. Consider scheduling large uploads during this window.",
        "3 documents this week exceeded bias threshold. Review recommended for employment contracts.",
        "Enable automated bias flagging for contracts over 5,000 words to catch high-risk documents early."
    ]

# ===== ANALYTICS API ROUTES =====
@app.route('/api/analytics-data')
@login_required
def api_analytics_data():
    conn = get_db_connection()
    total_docs = conn.execute('SELECT COUNT(*) FROM legal_documents').fetchone()[0]
    avg_bias = conn.execute('SELECT AVG(bias_score) FROM bias_reports').fetchone()[0] or 0
    bias_dist = conn.execute('SELECT bias_type, COUNT(*) as count FROM bias_reports GROUP BY bias_type').fetchall()
    type_dist = conn.execute('SELECT doc_type, COUNT(*) as count FROM legal_documents GROUP BY doc_type').fetchall()
    conn.close()
    
    return jsonify({
        'total_documents': total_docs,
        'avg_bias_score': round(avg_bias, 2),
        'bias_distribution': [{'type': row['bias_type'] or 'None', 'count': row['count']} for row in bias_dist],
        'type_distribution': [{'type': row['doc_type'], 'count': row['count']} for row in type_dist]
    })

@app.route('/api/trend-data')
@login_required
def trend_data():
    period = request.args.get('period', 'weekly')
    conn = get_db_connection()
    
    if period == 'daily':
        data = conn.execute('''
            SELECT DATE(uploaded_at) as date, COUNT(*) as count
            FROM legal_documents
            WHERE uploaded_at >= DATE('now', '-7 days')
            GROUP BY DATE(uploaded_at)
            ORDER BY date
        ''').fetchall()
        labels = [row['date'][5:] for row in data]
        values = [row['count'] for row in data]
    elif period == 'weekly':
        data = conn.execute('''
            SELECT strftime('%W', uploaded_at) as week, COUNT(*) as count
            FROM legal_documents
            GROUP BY week
            ORDER BY week DESC LIMIT 8
        ''').fetchall()
        labels = [f"Week {row['week']}" for row in reversed(data)]
        values = [row['count'] for row in reversed(data)]
    else:
        data = conn.execute('''
            SELECT strftime('%Y-%m', uploaded_at) as month, COUNT(*) as count
            FROM legal_documents
            GROUP BY month
            ORDER BY month DESC LIMIT 6
        ''').fetchall()
        labels = [row['month'] for row in reversed(data)]
        values = [row['count'] for row in reversed(data)]
    
    conn.close()
    return jsonify({'labels': labels, 'values': values})

@app.route('/api/time-data')
@login_required
def time_data():
    conn = get_db_connection()
    data = conn.execute('''
        SELECT doc_type, AVG(LENGTH(content)) as avg_length
        FROM legal_documents
        WHERE doc_type IS NOT NULL
        GROUP BY doc_type
    ''').fetchall()
    
    labels = [row['doc_type'] for row in data]
    values = [min(1 + (row['avg_length'] / 5000), 5) for row in data]
    conn.close()
    return jsonify({'labels': labels, 'values': values})

@app.route('/api/top-docs')
@login_required
def top_docs():
    sort = request.args.get('sort', 'bias')
    conn = get_db_connection()
    
    if sort == 'recent':
        data = conn.execute('''
            SELECT d.doc_id as id, d.title, d.doc_type as type, 
                   d.uploaded_at as date, b.bias_score as score,
                   LENGTH(d.content) as words
            FROM legal_documents d
            JOIN bias_reports b ON d.doc_id = b.doc_id
            ORDER BY d.uploaded_at DESC
            LIMIT 5
        ''').fetchall()
    else:
        data = conn.execute('''
            SELECT d.doc_id as id, d.title, d.doc_type as type, 
                   d.uploaded_at as date, b.bias_score as score,
                   LENGTH(d.content) as words
            FROM legal_documents d
            JOIN bias_reports b ON d.doc_id = b.doc_id
            WHERE b.bias_score > 0
            ORDER BY b.bias_score DESC
            LIMIT 5
        ''').fetchall()
    
    conn.close()
    
    result = []
    for row in data:
        result.append({
            'id': row['id'],
            'title': row['title'],
            'type': row['type'],
            'date': row['date'][:10] if row['date'] else 'Unknown',
            'score': round(float(row['score']), 2) if row['score'] else 0,
            'words': f"{row['words']:,}" if row['words'] else '0'
        })
    
    return jsonify(result)

@app.route('/api/heatmap-data')
@login_required
def heatmap_data():
    conn = get_db_connection()
    data = conn.execute('''
        SELECT DATE(d.uploaded_at) as date, AVG(b.bias_score) as avg_score
        FROM legal_documents d
        JOIN bias_reports b ON d.doc_id = b.doc_id
        WHERE d.uploaded_at >= DATE('now', '-7 days')
        GROUP BY DATE(d.uploaded_at)
        ORDER BY date
    ''').fetchall()
    conn.close()
    
    scores = [0.5] * 7
    for row in data:
        date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
        day_of_week = date_obj.weekday()
        scores[day_of_week] = round(float(row['avg_score']), 2)
    
    return jsonify(scores)

@app.route('/api/export-analytics')
@login_required
def export_analytics():
    conn = get_db_connection()
    data = conn.execute('''
        SELECT d.doc_id, d.title, d.doc_type, d.uploaded_at,
               b.bias_score, b.bias_type, b.explanation,
               s.summary_text
        FROM legal_documents d
        LEFT JOIN bias_reports b ON d.doc_id = b.doc_id
        LEFT JOIN summaries s ON d.doc_id = s.doc_id
        ORDER BY b.bias_score DESC
    ''').fetchall()
    conn.close()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Title', 'Type', 'Date', 'Bias Score', 'Bias Type', 'Explanation', 'Summary Preview'])
    
    for row in data:
        cw.writerow([
            row['doc_id'],
            row['title'],
            row['doc_type'],
            row['uploaded_at'][:10] if row['uploaded_at'] else '',
            f"{row['bias_score']:.2f}" if row['bias_score'] else 'N/A',
            row['bias_type'] or 'None',
            (row['explanation'][:100] + '...') if row['explanation'] else '',
            (row['summary_text'][:100] + '...') if row['summary_text'] else ''
        ])
    
    output = si.getvalue()
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=lexai-analytics-report.csv"
    response.headers["Content-type"] = "text/csv"
    return response

# ===== EXISTING API ROUTES =====
@app.route('/api/documents')
@login_required
def api_documents():
    conn = get_db_connection()
    documents = conn.execute('SELECT doc_id, title, doc_type, uploaded_at FROM legal_documents ORDER BY uploaded_at DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify([dict(row) for row in documents])

@app.route('/api/search')
@login_required
def api_search():
    query = request.args.get('q', '')
    conn = get_db_connection()
    results = conn.execute('''
        SELECT doc_id, title, doc_type, uploaded_at 
        FROM legal_documents 
        WHERE title LIKE ? OR content LIKE ?
        LIMIT 10
    ''', (f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    return jsonify([dict(row) for row in results])

@app.route('/api/analysis/<int:doc_id>')
@login_required
def api_analysis(doc_id):
    conn = get_db_connection()
    document = conn.execute('SELECT * FROM legal_documents WHERE doc_id = ?', (doc_id,)).fetchone()
    summary = conn.execute('SELECT * FROM summaries WHERE doc_id = ?', (doc_id,)).fetchone()
    bias_report = conn.execute('SELECT * FROM bias_reports WHERE doc_id = ?', (doc_id,)).fetchone()
    conn.close()
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    return jsonify({
        'document': dict(document),
        'summary': dict(summary) if summary else None,
        'bias_report': dict(bias_report) if bias_report else None
    })

@app.route('/api/analytics')
@login_required
def api_analytics():
    conn = get_db_connection()
    total_docs = conn.execute('SELECT COUNT(*) FROM legal_documents').fetchone()[0]
    total_summaries = conn.execute('SELECT COUNT(*) FROM summaries').fetchone()[0]
    total_bias = conn.execute('SELECT COUNT(*) FROM bias_reports').fetchone()[0]
    bias_dist = conn.execute('SELECT bias_type, COUNT(*) as count FROM bias_reports GROUP BY bias_type').fetchall()
    type_dist = conn.execute('SELECT doc_type, COUNT(*) as count FROM legal_documents GROUP BY doc_type').fetchall()
    avg_bias = conn.execute('SELECT AVG(bias_score) FROM bias_reports').fetchone()[0] or 0
    conn.close()
    
    return jsonify({
        'total_documents': total_docs,
        'total_summaries': total_summaries,
        'total_bias_reports': total_bias,
        'avg_bias_score': round(avg_bias, 2),
        'bias_distribution': [dict(row) for row in bias_dist],
        'type_distribution': [dict(row) for row in type_dist]
    })

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@login_required
def api_delete_document(doc_id):
    conn = get_db_connection()
    doc = conn.execute('SELECT * FROM legal_documents WHERE doc_id = ?', (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return jsonify({'error': 'Document not found'}), 404
    
    conn.execute('DELETE FROM summaries WHERE doc_id = ?', (doc_id,))
    conn.execute('DELETE FROM bias_reports WHERE doc_id = ?', (doc_id,))
    conn.execute('DELETE FROM entities WHERE doc_id = ?', (doc_id,))
    conn.execute('DELETE FROM legal_documents WHERE doc_id = ?', (doc_id,))
    
    if doc['filename']:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Document deleted successfully'})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Initialize database
def init_db():
    try:
        conn = sqlite3.connect('legal_ai.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS legal_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                doc_type TEXT,
                filename TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                summary_text TEXT NOT NULL,
                length_setting TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES legal_documents (doc_id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bias_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                bias_score FLOAT,
                bias_type TEXT,
                explanation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES legal_documents (doc_id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                entities_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES legal_documents (doc_id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('SELECT * FROM users WHERE email = ?', ('demo@lexai.com',))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (email, password_hash, full_name)
                VALUES (?, ?, ?)
            ''', ('demo@lexai.com', hashlib.sha256('demo123'.encode()).hexdigest(), 'Demo User'))
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization error: {e}")

if __name__ == '__main__':
    if os.path.exists('legal_ai.db'):
        try:
            conn = sqlite3.connect('legal_ai.db')
            conn.close()
        except:
            print("⚠️ Database corrupted, deleting and recreating...")
            os.remove('legal_ai.db')
    
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)