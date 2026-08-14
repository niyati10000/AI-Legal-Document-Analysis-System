from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app, abort
from database import db, User, UserSetting, LegalDocument, DocumentVersion, Summary, BiasReport, Entity, AuditLog
from blueprints.auth import login_required, get_client_ip
from services.worker import enqueue_document
from werkzeug.utils import secure_filename
import os

dashboard_bp = Blueprint('dashboard', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Render main user dashboard with analytics and recent documents list"""
    user_id = session['user_id']
    
    # KPIs isolated to user
    total_docs = LegalDocument.query.filter_by(user_id=user_id).count()
    
    total_summaries = db.session.query(db.func.count(Summary.id)).join(LegalDocument).\
        filter(LegalDocument.user_id == user_id).scalar() or 0
        
    total_bias_reports = db.session.query(db.func.count(BiasReport.id)).join(LegalDocument).\
        filter(LegalDocument.user_id == user_id).scalar() or 0

    # Fetch 10 most recent documents
    recent_docs = LegalDocument.query.filter_by(user_id=user_id).\
        order_by(LegalDocument.uploaded_at.desc()).limit(10).all()

    # Calculate user specific bias distribution statistics
    bias_stats_query = db.session.query(
        BiasReport.bias_type, 
        db.func.count(BiasReport.id).label('count'),
        db.func.avg(BiasReport.bias_score).label('avg_score')
    ).join(LegalDocument).filter(LegalDocument.user_id == user_id).group_by(BiasReport.bias_type).all()
    
    bias_stats = [{'bias_type': row[0], 'count': row[1], 'avg_score': row[2]} for row in bias_stats_query]

    return render_template('dashboard.html',
                           total_docs=total_docs,
                           total_summaries=total_summaries,
                           total_bias_reports=total_bias_reports,
                           recent_docs=recent_docs,
                           bias_stats=bias_stats)

@dashboard_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle document uploads and text pasting"""
    user_id = session['user_id']
    user_settings = UserSetting.query.filter_by(user_id=user_id).first()
    
    # Ensure settings exist
    if not user_settings:
        user_settings = UserSetting(user_id=user_id)
        db.session.add(user_settings)
        db.session.commit()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        doc_type = request.form.get('doc_type', 'Contract')
        analysis_type = request.form.get('analysis_type', 'both')
        summary_length = request.form.get('summary_length', user_settings.default_summary_length)
        pii_masking = 'pii_masking' in request.form
        
        input_method = request.form.get('input_method', 'file') # 'file' or 'text'
        pasted_content = request.form.get('content', '').strip()
        
        file = request.files.get('file')
        file_saved_path = None

        # Input validations
        if not title:
            flash('Document title is required.', 'error')
            return render_template('upload.html')

        try:
            if input_method == 'file':
                # Handle File Upload Tab
                if not file or file.filename == '':
                    flash('Please select a file to upload.', 'error')
                    return render_template('upload.html')
                    
                if not allowed_file(file.filename):
                    flash('Invalid file format. Only PDF, DOCX, and TXT are supported.', 'error')
                    return render_template('upload.html')

                # Secure and save file
                filename = secure_filename(file.filename)
                upload_dir = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)
                
                # Append timestamp to filename to prevent collisions
                name_parts = filename.rsplit('.', 1)
                unique_filename = f"{name_parts[0]}_{int(db.func.sys_time() if hasattr(db.func, 'sys_time') else os.getpid())}.{name_parts[1]}"
                file_saved_path = os.path.join(upload_dir, unique_filename)
                file.save(file_saved_path)
                
            elif input_method == 'text':
                # Handle Pasted Text Tab
                if not pasted_content:
                    flash('Please paste some text content to analyze.', 'error')
                    return render_template('upload.html')
            else:
                flash('Invalid document input method.', 'error')
                return render_template('upload.html')

            # Create base document record
            new_doc = LegalDocument(
                user_id=user_id,
                title=title,
                doc_type=doc_type,
                current_status='queued'
            )
            db.session.add(new_doc)
            db.session.flush()  # Generate primary key ID

            # If user pasted text, save initial version 1 immediately
            if input_method == 'text':
                version = DocumentVersion(
                    doc_id=new_doc.id,
                    version_number=1,
                    content=pasted_content,
                    filename=None
                )
                db.session.add(version)

            db.session.commit()

            # Enqueue task for background worker
            enqueue_document(
                doc_id=new_doc.id,
                file_path=file_saved_path,
                analysis_type=analysis_type,
                summary_length=summary_length,
                pii_masking=pii_masking,
                ip_address=get_client_ip()
            )

            # Log audit trail
            log = AuditLog(
                user_id=user_id,
                action='UPLOAD_DOCUMENT',
                details=f"Document '{title}' ({doc_type}) enqueued for analysis. Method: {input_method}",
                ip_address=get_client_ip()
            )
            db.session.add(log)
            db.session.commit()

            flash('Document uploaded successfully. Analyzing with Hybrid AI...', 'success')
            return redirect(url_for('dashboard.analysis', doc_id=new_doc.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Document upload error: {e}")
            flash('An error occurred during document upload. Please try again.', 'error')

    return render_template('upload.html')

@dashboard_bp.route('/documents')
@login_required
def documents():
    """Render documents list library with search, filtering, and pagination"""
    user_id = session['user_id']
    
    doc_type = request.args.get('type', 'all')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 12
    
    # Query setup
    query = LegalDocument.query.filter_by(user_id=user_id)
    
    if doc_type != 'all':
        query = query.filter_by(doc_type=doc_type)
        
    if search:
        # Search title or contents of the latest version of the documents
        query = query.join(DocumentVersion).filter(
            (LegalDocument.title.like(f"%{search}%")) | 
            (DocumentVersion.content.like(f"%{search}%"))
        ).group_by(LegalDocument.id)
        
    # Paginate results
    pagination = query.order_by(LegalDocument.uploaded_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('documents.html',
                           documents=pagination.items,
                           pagination=pagination,
                           current_type=doc_type,
                           search=search,
                           current_page=page,
                           total_pages=pagination.pages)

@dashboard_bp.route('/analysis/<int:doc_id>')
@login_required
def analysis(doc_id):
    """Render AI analysis details view. Shows progress loaders if processing"""
    user_id = session['user_id']
    
    # Isolate queries to current user
    document = LegalDocument.query.filter_by(id=doc_id, user_id=user_id).first_or_404()
    summary = Summary.query.filter_by(doc_id=doc_id).first()
    bias_report = BiasReport.query.filter_by(doc_id=doc_id).first()
    entities_record = Entity.query.filter_by(doc_id=doc_id).first()

    entities_data = entities_record.data if entities_record else {}

    # Log view action (limit logs spamming on page refreshes using short interval check)
    last_log = AuditLog.query.filter_by(user_id=user_id, action='VIEW_ANALYSIS').\
        order_by(AuditLog.timestamp.desc()).first()
    
    import time as _time
    should_log = True
    if last_log and last_log.timestamp:
        elapsed = _time.time() - last_log.timestamp.timestamp()
        should_log = elapsed > 60
    
    if should_log:
        log = AuditLog(
            user_id=user_id,
            action='VIEW_ANALYSIS',
            details=f"Viewed analysis for document ID {doc_id} ('{document.title}')",
            ip_address=get_client_ip()
        )
        db.session.add(log)
        db.session.commit()

    return render_template('analysis.html',
                           document=document,
                           summary=summary,
                           bias_report=bias_report,
                           entities=entities_data)

@dashboard_bp.route('/document/<int:doc_id>')
@login_required
def document_details(doc_id):
    """Render full document details, versions list, and side-by-side diff tool"""
    user_id = session['user_id']
    
    document = LegalDocument.query.filter_by(id=doc_id, user_id=user_id).first_or_404()
    
    # Get all versions
    versions = DocumentVersion.query.filter_by(doc_id=doc_id).order_by(DocumentVersion.version_number.desc()).all()
    latest_version = versions[0] if versions else None
    
    summary = Summary.query.filter_by(doc_id=doc_id).first()
    bias_report = BiasReport.query.filter_by(doc_id=doc_id).first()
    entities_record = Entity.query.filter_by(doc_id=doc_id).first()
    entities_data = entities_record.data if entities_record else {}

    # Get related documents of same type
    related_docs = LegalDocument.query.filter(
        LegalDocument.user_id == user_id,
        LegalDocument.doc_type == document.doc_type,
        LegalDocument.id != doc_id
    ).order_by(LegalDocument.uploaded_at.desc()).limit(3).all()

    return render_template('document-details.html',
                           document=document,
                           versions=versions,
                           latest_version=latest_version,
                           summary=summary,
                           bias_report=bias_report,
                           entities=entities_data,
                           related_docs=related_docs)

@dashboard_bp.route('/document/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    """Delete a document and all related analysis records from database and files"""
    user_id = session['user_id']
    doc = LegalDocument.query.filter_by(id=doc_id, user_id=user_id).first_or_404()

    try:
        title = doc.title
        
        # Remove physical file if saved
        for version in doc.versions:
            if version.filename:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], version.filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        current_app.logger.error(f"Error removing physical file {file_path}: {e}")

        # Delete database model records (Cascade handles summaries, bias, entities, versions)
        db.session.delete(doc)
        
        # Log action
        log = AuditLog(
            user_id=user_id,
            action='DELETE_DOCUMENT',
            details=f"Deleted document ID {doc_id} ('{title}')",
            ip_address=get_client_ip()
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Document '{title}' deleted successfully.", 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting document {doc_id}: {e}")
        flash('Failed to delete document.', 'error')

    return redirect(url_for('dashboard.documents'))

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Render analytics dashboard"""
    return render_template('analytics.html')
