from flask import Blueprint, request, jsonify, session, current_app, abort
from database import db, User, UserSetting, LegalDocument, DocumentVersion, Summary, BiasReport, Entity, ApiKey, AuditLog
from blueprints.auth import login_required, get_client_ip
from services.ai_service import analyze_document_pipeline, GEMINI_AVAILABLE, gemini_client, run_gemini_analysis, get_fallback_insights
from services.file_service import extract_text_from_file
from werkzeug.utils import secure_filename
import hashlib
from datetime import datetime, timedelta
import time
import os
import difflib
import json
import threading

api_bp = Blueprint('api', __name__)

# ===== IN-MEMORY RATE LIMITER (TOKEN BUCKET ALGORITHM) =====
class TokenBucketRateLimiter:
    """Thread-safe in-memory Token Bucket rate limiter for Developer APIs"""
    def __init__(self, max_tokens=60, fill_rate_per_sec=1.0):
        self.max_tokens = max_tokens
        self.fill_rate = fill_rate_per_sec
        self.buckets = {}
        self.lock = threading.Lock() if 'threading' in globals() else None
        
    def _get_lock(self):
        # Dynamically import threading lock if needed
        import threading
        if not hasattr(self, 'lock') or self.lock is None:
            self.lock = threading.Lock()
        return self.lock

    def is_allowed(self, client_key):
        lock = self._get_lock()
        with lock:
            now = time.time()
            if client_key not in self.buckets:
                self.buckets[client_key] = {
                    'tokens': self.max_tokens,
                    'last_update': now
                }
                return True

            bucket = self.buckets[client_key]
            elapsed = now - bucket['last_update']
            
            # Replenish tokens
            new_tokens = bucket['tokens'] + (elapsed * self.fill_rate)
            bucket['tokens'] = min(self.max_tokens, new_tokens)
            bucket['last_update'] = now

            if bucket['tokens'] >= 1.0:
                bucket['tokens'] -= 1.0
                return True
            else:
                return False

# Instantiate rate limiter (60 requests per minute capacity, refills 1 token every second)
rate_limiter = TokenBucketRateLimiter(max_tokens=60, fill_rate_per_sec=1.0)

# ===== SECURITY MIDDLEWARE FOR API KEY AUTH =====
def api_key_required(f):
    """Decorator to authorize developer requests using Bearer API keys with rate-limiting"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized. Missing or invalid Bearer token.'}), 401
            
        raw_key = auth_header.split('Bearer ')[1].strip()
        
        # Interactive API Playground session authentication fallback
        if raw_key == 'TEST_PLAYGROUND_SESSION_AUTH' and 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                request.api_user = user
                return f(*args, **kwargs)

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Verify key in database
        key = ApiKey.query.filter_by(key_hash=key_hash, is_active=True).first()
        if not key:
            return jsonify({'error': 'Unauthorized. Invalid API key.'}), 401

        # Check rate limits
        if not rate_limiter.is_allowed(key.key_hash):
            return jsonify({'error': 'Too Many Requests. Rate limit exceeded (60 req/min).'}), 429

        # Update last used timestamp
        key.last_used_at = datetime.utcnow()
        db.session.commit()
        
        # Attach validated user to request context for route handler usage
        request.api_user = key.user
        return f(*args, **kwargs)
    return decorated

# ===== DEVELOPER REST ENDPOINTS (V1 API) =====

@api_bp.route('/api/v1/analyze', methods=['POST'])
@api_key_required
def api_analyze_document():
    """
    Developer API to analyze document contents.
    Accepts raw text or file uploads. Runs synchronously returning results immediately.
    """
    user = request.api_user
    
    title = request.form.get('title', '').strip()
    doc_type = request.form.get('doc_type', 'Contract')
    analysis_type = request.form.get('analysis_type', 'both')
    summary_length = request.form.get('summary_length', 'medium')
    pii_masking = request.form.get('pii_masking', 'true').lower() == 'true'
    
    pasted_text = request.form.get('content', '').strip()
    file = request.files.get('file')
    
    if not title:
        return jsonify({'error': 'Missing title parameter.'}), 400

    try:
        content = ""
        filename = None
        
        # Determine input method
        if file:
            if not allowed_file(file.filename):
                return jsonify({'error': 'Unsupported file format. Use PDF, DOCX, or TXT.'}), 400
                
            filename = secure_filename(file.filename)
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"api_{int(time.time())}_{filename}")
            file.save(file_path)
            
            content = extract_text_from_file(file_path)
            # Remove file immediately after reading to save disk storage on API runs
            try:
                os.remove(file_path)
            except:
                pass
        elif pasted_text:
            content = pasted_text
        else:
            return jsonify({'error': 'Missing document content. Send text in "content" or upload a "file".'}), 400

        # Execute analysis synchronously
        results = analyze_document_pipeline(
            content=content,
            analysis_type=analysis_type,
            summary_length=summary_length,
            pii_masking=pii_masking,
            user_id=user.id
        )

        # Log audit trail
        log = AuditLog(
            user_id=user.id,
            action='API_ANALYZE_REQUEST',
            details=f"API request analyzed document '{title}' ({doc_type}). PII Masking: {pii_masking}",
            ip_address=get_client_ip()
        )
        db.session.add(log)
        db.session.commit()

        # Build clean developer JSON response
        response = {
            'title': title,
            'doc_type': doc_type,
            'pii_masked': pii_masking,
            'summary': results.get('summary') if analysis_type in ['summarize', 'both'] else None,
            'bias_analysis': results.get('bias') if analysis_type in ['bias', 'both'] else None,
            'entities': results.get('entities')
        }
        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f"API document analysis failure: {e}")
        return jsonify({'error': f"Processing error: {str(e)}"}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'txt'}

@api_bp.route('/api/v1/documents', methods=['GET'])
@api_key_required
def api_list_documents():
    """List all documents owned by developer"""
    user = request.api_user
    docs = LegalDocument.query.filter_by(user_id=user.id).order_by(LegalDocument.uploaded_at.desc()).all()
    
    result = []
    for doc in docs:
        result.append({
            'doc_id': doc.id,
            'title': doc.title,
            'doc_type': doc.doc_type,
            'status': doc.current_status,
            'uploaded_at': doc.uploaded_at.isoformat()
        })
    return jsonify(result)

# ===== SYSTEM POLLING & INTERACTIVE UI SERVICES =====

@api_bp.route('/api/v1/documents/<int:doc_id>/status', methods=['GET'])
@login_required
def api_document_status(doc_id):
    """Retrieve document background processing status for frontend polling loaders"""
    user_id = session['user_id']
    doc = LegalDocument.query.filter_by(id=doc_id, user_id=user_id).first_or_404()
    
    return jsonify({
        'doc_id': doc.id,
        'status': doc.current_status,
        'title': doc.title
    })

@api_bp.route('/api/v1/document/diff', methods=['POST'])
@login_required
def api_compare_versions():
    """Calculate side-by-side text diff highlight comparisons using python's difflib"""
    user_id = session['user_id']
    doc_id = request.json.get('doc_id')
    ver_a_num = request.json.get('version_a')
    ver_b_num = request.json.get('version_b')
    
    if not doc_id or not ver_a_num or not ver_b_num:
        return jsonify({'error': 'Missing comparison identifiers.'}), 400

    # Ensure document ownership
    doc = LegalDocument.query.filter_by(id=doc_id, user_id=user_id).first_or_404()
    
    ver_a = DocumentVersion.query.filter_by(doc_id=doc_id, version_number=ver_a_num).first_or_404()
    ver_b = DocumentVersion.query.filter_by(doc_id=doc_id, version_number=ver_b_num).first_or_404()

    text_a = ver_a.content.splitlines()
    text_b = ver_b.content.splitlines()

    # Generate html side-by-side diff table
    differ = difflib.HtmlDiff()
    diff_table = differ.make_table(text_a, text_b, context=True, numlines=3)

    return jsonify({
        'diff_html': diff_table,
        'version_a': ver_a_num,
        'version_b': ver_b_num
    })

# ===== ANALYTICS VISUALIZATION APIS =====

@api_bp.route('/api/v1/charts/trends', methods=['GET'])
@login_required
def api_chart_trends():
    """Retrieve uploads trend stats grouped by period for Chart.js"""
    user_id = session['user_id']
    period = request.args.get('period', 'weekly')
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # SQLite raw/ORM extraction grouping
    if period == 'daily':
        data = db.session.query(
            db.func.date(LegalDocument.uploaded_at).label('date'),
            db.func.count(LegalDocument.id).label('count')
        ).filter(
            LegalDocument.user_id == user_id,
            LegalDocument.uploaded_at >= thirty_days_ago
        ).group_by('date').order_by('date').all()
        
        labels = [row.date for row in data]
        values = [row.count for row in data]
        
    elif period == 'weekly':
        # Group by week number
        data = db.session.query(
            db.func.strftime('%W', LegalDocument.uploaded_at).label('week'),
            db.func.count(LegalDocument.id).label('count')
        ).filter(LegalDocument.user_id == user_id).group_by('week').order_by('week').all()
        
        labels = [f"Week {row.week}" for row in data]
        values = [row.count for row in data]
        
    else: # monthly
        data = db.session.query(
            db.func.strftime('%Y-%m', LegalDocument.uploaded_at).label('month'),
            db.func.count(LegalDocument.id).label('count')
        ).filter(LegalDocument.user_id == user_id).group_by('month').order_by('month').all()
        
        labels = [row.month for row in data]
        values = [row.count for row in data]

    return jsonify({'labels': labels, 'values': values})

@api_bp.route('/api/v1/charts/bias', methods=['GET'])
@login_required
def api_chart_bias():
    """Retrieve user bias breakdown score averages for Radar/Doughnut Chart.js"""
    user_id = session['user_id']
    
    reports = BiasReport.query.join(LegalDocument).filter(LegalDocument.user_id == user_id).all()
    
    totals = {'Gender': 0.0, 'Racial': 0.0, 'Socioeconomic': 0.0, 'Age': 0.0}
    counts = {'Gender': 0, 'Racial': 0, 'Socioeconomic': 0, 'Age': 0}
    
    for r in reports:
        cats = r.categories
        for cat, score in cats.items():
            if cat in totals:
                totals[cat] += score
                counts[cat] += 1
                
    averages = {cat: round(totals[cat] / counts[cat], 2) if counts[cat] > 0 else 0.0 for cat in totals}
    
    return jsonify({
        'labels': list(averages.keys()),
        'values': list(averages.values())
    })

@api_bp.route('/api/v1/gemini-insights', methods=['POST'])
@login_required
def gemini_insights():
    """Generate strategic trends insights dynamically using Gemini"""
    if not GEMINI_AVAILABLE or not gemini_client:
        return jsonify(get_fallback_insights())
        
    user_id = session['user_id']
    data = request.json or {}
    analytics = data.get('analytics', {})
    
    try:
        # Pull document type breakdown to enrich prompt context
        type_breakdown = db.session.query(
            LegalDocument.doc_type, db.func.count(LegalDocument.id)
        ).filter(LegalDocument.user_id == user_id).group_by(LegalDocument.doc_type).all()
        type_str = ", ".join([f"{row[0]}: {row[1]}" for row in type_breakdown])
        
        prompt = f"""
        You are a highly advanced Legal Tech compliance auditor. Review the following metric details of a lawyer's account uploads:
        - Total Documents Audited: {analytics.get('total_documents', 0)}
        - Average Bias Severity Score: {analytics.get('avg_bias_score', 0)}
        - Document Classifications: {type_str}
        
        Generate exactly 6 short, strategic compliance alerts:
        1. Trend warning.
        2. Jurisdiction risk pattern.
        3. Frequency insights on terms.
        4. Operational review bottlenecks.
        5. Red flag compliance warning.
        6. Best practice procedural advice.
        
        Output format: Return ONLY a raw JSON string array containing exactly 6 strings. No quotes, backticks, or markdown format wrappers.
        """
        
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        
        txt = response.text.strip()
        if txt.startswith("```json"):
            txt = txt[7:]
        if txt.endswith("```"):
            txt = txt[:-3]
        txt = txt.strip()
        
        return jsonify(json.loads(txt))
        
    except Exception as e:
        current_app.logger.error(f"Gemini Insights API failed: {e}")
        return jsonify(get_fallback_insights())

@api_bp.route('/api/v1/export-analytics', methods=['GET'])
@login_required
def export_analytics():
    """Export user compliance statistics as a CSV report"""
    user_id = session['user_id']
    
    # Query all user documents outer joined with summaries and bias reports
    data = db.session.query(
        LegalDocument.id,
        LegalDocument.title,
        LegalDocument.doc_type,
        LegalDocument.uploaded_at,
        BiasReport.bias_score,
        BiasReport.bias_type,
        BiasReport.explanation,
        Summary.summary_text
    ).outerjoin(BiasReport, LegalDocument.id == BiasReport.doc_id)\
     .outerjoin(Summary, LegalDocument.id == Summary.doc_id)\
     .filter(LegalDocument.user_id == user_id)\
     .order_by(BiasReport.bias_score.desc()).all()
     
    from io import StringIO
    import csv
    from flask import make_response
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Title', 'Type', 'Date', 'Bias Score', 'Bias Type', 'Explanation', 'Summary Preview'])
    
    for row in data:
        cw.writerow([
            row[0],
            row[1],
            row[2],
            row[3].strftime('%Y-%m-%d') if row[3] else '',
            f"{row[4]:.2f}" if row[4] is not None else 'N/A',
            row[5] or 'None',
            (row[6][:100] + '...') if row[6] else '',
            (row[7][:100] + '...') if row[7] else ''
        ])
        
    output = si.getvalue()
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=lexai-analytics-report.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@api_bp.route('/api/v1/analytics', methods=['GET'])
@login_required
def api_analytics_summary():
    """Retrieve combined user-specific metrics for the dashboard and charts"""
    user_id = session['user_id']
    
    total_docs = LegalDocument.query.filter_by(user_id=user_id).count()
    
    avg_bias = db.session.query(db.func.avg(BiasReport.bias_score)).join(LegalDocument)\
        .filter(LegalDocument.user_id == user_id).scalar() or 0.0
        
    total_entities = db.session.query(db.func.count(Entity.id)).join(LegalDocument)\
        .filter(LegalDocument.user_id == user_id).scalar() or 0
        
    bias_dist_query = db.session.query(
        BiasReport.bias_type, db.func.count(BiasReport.id)
    ).join(LegalDocument).filter(LegalDocument.user_id == user_id).group_by(BiasReport.bias_type).all()
    
    type_dist_query = db.session.query(
        LegalDocument.doc_type, db.func.count(LegalDocument.id)
    ).filter(LegalDocument.user_id == user_id).group_by(LegalDocument.doc_type).all()
    
    # Format trend values
    trend_data = api_chart_trends().json
    bias_distribution = [{'type': row[0] or 'None', 'count': row[1]} for row in bias_dist_query]
    type_distribution = [{'type': row[0], 'count': row[1]} for row in type_dist_query]
    
    # Calculate fake but nicely formatted heatmap data (average bias per day of week)
    heatmap_scores = [0.0] * 7
    heatmap_query = db.session.query(
        db.func.strftime('%w', LegalDocument.uploaded_at).label('day'),
        db.func.avg(BiasReport.bias_score).label('avg')
    ).join(BiasReport).filter(LegalDocument.user_id == user_id).group_by('day').all()
    for row in heatmap_query:
        try:
            day_idx = int(row.day)
            heatmap_scores[day_idx] = float(row.avg)
        except:
            pass
            
    # Top documents listing
    top_docs_query = db.session.query(
        LegalDocument.id, LegalDocument.title, LegalDocument.doc_type, LegalDocument.uploaded_at, BiasReport.bias_score
    ).join(BiasReport).filter(LegalDocument.user_id == user_id).order_by(BiasReport.bias_score.desc()).limit(5).all()
    
    top_docs = []
    for row in top_docs_query:
        # Word counts approximation based on content length
        latest_ver = DocumentVersion.query.filter_by(doc_id=row.id).order_by(DocumentVersion.version_number.desc()).first()
        words = len(latest_ver.content.split()) if latest_ver else 0
        
        top_docs.append({
            'id': row.id,
            'title': row.title,
            'type': row.doc_type,
            'date': row.uploaded_at.strftime('%Y-%m-%d'),
            'words': words,
            'score': float(row.bias_score)
        })

    return jsonify({
        'total_documents': total_docs,
        'avg_bias_score': float(avg_bias),
        'total_entities': total_entities,
        'trend_data': trend_data,
        'bias_distribution': bias_distribution,
        'type_distribution': type_distribution,
        'heatmap_data': heatmap_scores,
        'top_docs': top_docs
    })

@api_bp.route('/api/v1/time-data', methods=['GET'])
@login_required
def api_time_data():
    """Retrieve average document lengths as a proxy for processing times"""
    user_id = session['user_id']
    
    data = db.session.query(
        LegalDocument.doc_type,
        db.func.avg(db.func.length(DocumentVersion.content)).label('avg_len')
    ).join(DocumentVersion).filter(LegalDocument.user_id == user_id).group_by(LegalDocument.doc_type).all()
    
    labels = [row[0] for row in data]
    # Estimate seconds based on content length (e.g., 1s per 2000 chars)
    values = [max(1.0, round(float(row[1]) / 2000.0, 1)) if row[1] else 1.0 for row in data]
    
    return jsonify({
        'labels': labels,
        'values': values
    })

@api_bp.route('/api/v1/top-docs', methods=['GET'])
@login_required
def api_top_documents():
    """Retrieve top documents sorted by bias or upload date"""
    user_id = session['user_id']
    sort_by = request.args.get('sort', 'bias')
    
    query = db.session.query(
        LegalDocument.id, LegalDocument.title, LegalDocument.doc_type, LegalDocument.uploaded_at, BiasReport.bias_score
    ).join(BiasReport).filter(LegalDocument.user_id == user_id)
    
    if sort_by == 'recent':
        query = query.order_by(LegalDocument.uploaded_at.desc())
    else:
        query = query.order_by(BiasReport.bias_score.desc())
        
    data = query.limit(5).all()
    
    result = []
    for row in data:
        latest_ver = DocumentVersion.query.filter_by(doc_id=row.id).order_by(DocumentVersion.version_number.desc()).first()
        words = len(latest_ver.content.split()) if latest_ver else 0
        
        result.append({
            'id': row.id,
            'title': row.title,
            'type': row.doc_type,
            'date': row.uploaded_at.strftime('%Y-%m-%d'),
            'words': words,
            'score': float(row.bias_score)
        })
    return jsonify(result)

@api_bp.route('/api/v1/chat', methods=['POST'])
def api_chat():
    """Chatbot endpoint for document Q&A"""
    user_id = session.get('user_id')
    
    # Fallback to API Key auth
    if not user_id:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            raw_key = auth_header.split('Bearer ')[1].strip()
            if raw_key == 'TEST_PLAYGROUND_SESSION_AUTH' and 'user_id' in session:
                user_id = session['user_id']
            else:
                key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
                key = ApiKey.query.filter_by(key_hash=key_hash, is_active=True).first()
                if key:
                    if not rate_limiter.is_allowed(key.key_hash):
                        return jsonify({'error': 'Too Many Requests. Rate limit exceeded (60 req/min).', 'success': False}), 429
                    user_id = key.user_id
                    key.last_used_at = datetime.utcnow()
                    db.session.commit()

    if not user_id:
        return jsonify({'error': 'Unauthorized', 'success': False}), 401
        
    data = request.json or {}
    doc_id = data.get('doc_id')
    message = data.get('message')
    history = data.get('history', [])
    
    if not doc_id or not message:
        return jsonify({'error': 'Missing doc_id or message', 'success': False}), 400
        
    if not GEMINI_AVAILABLE or not gemini_client:
        return jsonify({'error': 'AI service is currently unavailable.', 'success': False}), 503
        
    # Verify document ownership
    doc = LegalDocument.query.filter_by(id=doc_id, user_id=user_id).first()
    if not doc:
        return jsonify({'error': 'Document not found or unauthorized', 'success': False}), 404
        
    # Load document context
    latest_ver = DocumentVersion.query.filter_by(doc_id=doc_id).order_by(DocumentVersion.version_number.desc()).first()
    content = latest_ver.content if latest_ver else ""
    
    summary_obj = Summary.query.filter_by(doc_id=doc_id).first()
    summary_context = f"SUMMARY: {summary_obj.summary_text}" if summary_obj and summary_obj.summary_text else ""
    
    bias_obj = BiasReport.query.filter_by(doc_id=doc_id).first()
    bias_context = f"BIAS ANALYSIS: {bias_obj.explanation}" if bias_obj and bias_obj.explanation else ""
    
    prompt = f"""You are LexAI, an intelligent legal document assistant. You have been given a legal document to analyze. Answer the user's question about this document accurately and helpfully.

DOCUMENT TITLE: {doc.title}
DOCUMENT TYPE: {doc.doc_type}

DOCUMENT CONTENT:
{content[:12000]}

{summary_context}
{bias_context}

IMPORTANT: Answer based ONLY on the document content provided. If the answer is not in the document, say so clearly. Be precise and cite specific sections when possible."""

    if history:
        history_text = "\n\nPREVIOUS CONVERSATION:\n"
        for msg in history[-6:]:  # Last 6 messages for context window
            role = "User" if msg.get('role') == 'user' else "Assistant"
            history_text += f"{role}: {msg.get('content', '')}\n"
        prompt += history_text

    prompt += f"\nUser's current question: {message}\n\nProvide a helpful, accurate response:"
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        return jsonify({'response': response.text, 'success': True})
    except Exception as e:
        current_app.logger.error(f"Chat API error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

