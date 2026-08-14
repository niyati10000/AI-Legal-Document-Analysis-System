import threading
import queue
import traceback
import os
from database import db, LegalDocument, DocumentVersion, Summary, BiasReport, Entity, AuditLog
from services.file_service import extract_text_from_file
from services.ai_service import analyze_document_pipeline

# Global queue for thread-safe background jobs
task_queue = queue.Queue()
worker_thread = None

def worker_loop(app):
    """Worker thread loop to process document analysis tasks in background"""
    while True:
        try:
            # Block until a task is available
            task = task_queue.get()
            
            # None is a sentinel signal to stop the thread
            if task is None:
                task_queue.task_done()
                break
                
            doc_id = task['doc_id']
            file_path = task.get('file_path')
            analysis_type = task.get('analysis_type', 'both')
            summary_length = task.get('summary_length', 'medium')
            pii_masking = task.get('pii_masking', True)
            ip_address = task.get('ip_address', '127.0.0.1')
            
            # Execute within Flask application context to access database and services
            with app.app_context():
                process_document(doc_id, file_path, analysis_type, summary_length, pii_masking, ip_address)
                
            task_queue.task_done()
            
        except Exception as e:
            print(f"Background worker loop critical error: {e}")
            traceback.print_exc()

def process_document(doc_id, file_path, analysis_type, summary_length, pii_masking, ip_address):
    """Processes extraction and AI pipelines for a single document"""
    doc = LegalDocument.query.get(doc_id)
    if not doc:
        print(f"Error: Document with ID {doc_id} not found in database.")
        return

    try:
        # Step 1: Extract Text Content
        doc.current_status = 'extracting'
        db.session.commit()
        
        content = ""
        filename = doc.title  # Fallback

        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path)
            content = extract_text_from_file(file_path)
        else:
            # If no file was uploaded, the content was pasted in Tab B.
            # We assume a base version has already been created or content was passed.
            # Let's retrieve content from the latest version.
            latest_ver = DocumentVersion.query.filter_by(doc_id=doc_id).order_by(DocumentVersion.version_number.desc()).first()
            if latest_ver:
                content = latest_ver.content
                filename = latest_ver.filename
            else:
                raise ValueError("No text content or file path provided for analysis.")

        # Create version 1 record if it doesn't exist yet (for uploaded files)
        version_count = DocumentVersion.query.filter_by(doc_id=doc_id).count()
        if version_count == 0:
            version = DocumentVersion(
                doc_id=doc_id,
                version_number=1,
                content=content,
                filename=filename
            )
            db.session.add(version)
            db.session.flush()

        # Step 2: Run AI pipelines (Summarization, Bias Detection, Entity Extraction, PII Masking)
        doc.current_status = 'analyzing'
        db.session.commit()

        # Run unified pipeline service
        analysis_results = analyze_document_pipeline(
            content=content, 
            analysis_type=analysis_type, 
            summary_length=summary_length,
            pii_masking=pii_masking,
            user_id=doc.user_id
        )

        # Step 3: Write results to database
        # 3a. Summarization
        if analysis_type in ['summarize', 'both']:
            summary = Summary(
                doc_id=doc_id,
                summary_text=analysis_results['summary'],
                length_setting=summary_length
            )
            db.session.add(summary)

        # 3b. Bias Analysis
        if analysis_type in ['bias', 'both']:
            bias_report = BiasReport(
                doc_id=doc_id,
                bias_score=analysis_results['bias']['score'],
                bias_type=analysis_results['bias']['type'],
                explanation=analysis_results['bias']['explanation']
            )
            cats = dict(analysis_results['bias'].get('categories', {}))
            if 'flags' in analysis_results['bias']:
                cats['flags'] = analysis_results['bias']['flags']
            if 'compliance_status' in analysis_results['bias']:
                cats['compliance_status'] = analysis_results['bias']['compliance_status']
            bias_report.categories = cats
            db.session.add(bias_report)

        # 3c. Named Entity Extraction
        entities = Entity(
            doc_id=doc_id
        )
        entities.data = analysis_results['entities']
        db.session.add(entities)

        # Complete status
        doc.current_status = 'completed'
        
        # Log successful audit
        log = AuditLog(
            user_id=doc.user_id,
            action='ANALYZE_SUCCESS',
            details=f"Successfully analyzed document ID: {doc_id} ('{doc.title}')",
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        print(f"[OK] Background processing completed for document {doc_id} ('{doc.title}')")

    except Exception as e:
        db.session.rollback()
        # Mark document as failed
        doc.current_status = 'failed'
        db.session.commit()
        
        error_details = traceback.format_exc()
        print(f"[ERROR] Background processing failed for document {doc_id}: {e}\n{error_details}")
        
        # Log failed audit trail
        log = AuditLog(
            user_id=doc.user_id,
            action='ANALYZE_FAILED',
            details=f"Failed analysis on document ID {doc_id}. Error: {str(e)}",
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()

def enqueue_document(doc_id, file_path=None, analysis_type='both', summary_length='medium', pii_masking=True, ip_address='127.0.0.1'):
    """Helper function to enqueue document for analysis"""
    task = {
        'doc_id': doc_id,
        'file_path': file_path,
        'analysis_type': analysis_type,
        'summary_length': summary_length,
        'pii_masking': pii_masking,
        'ip_address': ip_address
    }
    task_queue.put(task)
    print(f"Task enqueued for document ID: {doc_id}")

def start_worker(app):
    """Spawns background worker thread if not already running"""
    global worker_thread
    if worker_thread is None or not worker_thread.is_alive():
        worker_thread = threading.Thread(target=worker_loop, args=(app,), daemon=True)
        worker_thread.start()
        print("Background worker thread started successfully.")
