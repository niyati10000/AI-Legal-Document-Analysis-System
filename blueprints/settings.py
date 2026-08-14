from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app, jsonify
from database import db, User, UserSetting, ApiKey, AuditLog
from blueprints.auth import login_required, get_client_ip
import secrets
import hashlib
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Handle user profile, preferences, and api keys settings"""
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    
    # Ensure user has a settings record
    user_settings = UserSetting.query.filter_by(user_id=user_id).first()
    if not user_settings:
        user_settings = UserSetting(user_id=user_id)
        db.session.add(user_settings)
        db.session.commit()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            role = request.form.get('role', user.role).strip()
            bio = request.form.get('bio', '').strip()
            organization = request.form.get('organization', '').strip()

            if not email:
                flash('Email is required.', 'error')
                return redirect(url_for('settings.settings'))

            # Check email availability
            existing_user = User.query.filter(User.email == email, User.id != user_id).first()
            if existing_user:
                flash('Email is already in use by another account.', 'error')
                return redirect(url_for('settings.settings'))

            user.full_name = full_name
            user.email = email
            user.role = role
            user.bio = bio or 'AI-driven legal document intelligence and contract bias auditing workspace.'
            user.organization = organization or 'Legal Tech'
            
            session['username'] = full_name or email.split('@')[0]
            session['role'] = role
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            
            # Log action
            log = AuditLog(
                user_id=user_id,
                action='UPDATE_PROFILE',
                details=f"Updated profile: Name={full_name}, Email={email}, Role={role}, Org={organization}",
                ip_address=get_client_ip()
            )
            db.session.add(log)
            db.session.commit()

        elif action == 'update_preferences':
            default_len = request.form.get('default_summary_length', 'medium')
            bias_thresh = float(request.form.get('bias_threshold', 0.3))
            pii_enabled = 'pii_masking_enabled' in request.form
            ai_model = request.form.get('ai_model', 'gemini-3.5-flash')
            legal_domain = request.form.get('legal_domain', 'General Corporate')

            user_settings.default_summary_length = default_len
            user_settings.bias_threshold = bias_thresh
            user_settings.pii_masking_enabled = pii_enabled
            user_settings.ai_model = ai_model
            user_settings.legal_domain = legal_domain
            
            db.session.commit()
            flash('Analysis & AI preferences saved successfully!', 'success')

            # Log action
            log = AuditLog(
                user_id=user_id,
                action='UPDATE_PREFERENCES',
                details=f"Preferences updated: model={ai_model}, domain={legal_domain}, length={default_len}, threshold={bias_thresh}",
                ip_address=get_client_ip()
            )
            db.session.add(log)
            db.session.commit()

        elif action == 'change_password':
            current_pwd = request.form.get('current_password', '')
            new_pwd = request.form.get('new_password', '')
            confirm_pwd = request.form.get('confirm_password', '')

            if not current_pwd or not new_pwd or not confirm_pwd:
                flash('All password fields are required.', 'error')
                return redirect(url_for('settings.settings'))

            if not user.check_password(current_pwd):
                flash('Incorrect current password.', 'error')
                return redirect(url_for('settings.settings'))

            if new_pwd != confirm_pwd:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('settings.settings'))

            if len(new_pwd) < 6:
                flash('New password must be at least 6 characters long.', 'error')
                return redirect(url_for('settings.settings'))

            user.set_password(new_pwd)
            db.session.commit()
            flash('Password updated successfully!', 'success')

            # Log action
            log = AuditLog(
                user_id=user_id,
                action='CHANGE_PASSWORD',
                details="User changed account password.",
                ip_address=get_client_ip()
            )
            db.session.add(log)
            db.session.commit()

        return redirect(url_for('settings.settings'))

    # Fetch API Keys
    keys = ApiKey.query.filter_by(user_id=user_id).order_by(ApiKey.created_at.desc()).all()
    
    # Fetch user audit logs (limit 20)
    audit_logs = AuditLog.query.filter_by(user_id=user_id).order_by(AuditLog.timestamp.desc()).limit(20).all()

    return render_template('settings.html', 
                           user=user, 
                           settings=user_settings, 
                           api_keys=keys,
                           audit_logs=audit_logs)

@settings_bp.route('/settings/export-audit-log', methods=['GET'])
@login_required
def export_audit_log():
    """Export the user's security & action audit logs as CSV"""
    user_id = session['user_id']
    logs = AuditLog.query.filter_by(user_id=user_id).order_by(AuditLog.timestamp.desc()).all()
    
    import io
    import csv
    from flask import Response
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Log ID', 'Timestamp (UTC)', 'Action', 'IP Address', 'Details'])
    
    for l in logs:
        writer.writerow([l.id, l.timestamp.strftime('%Y-%m-%d %H:%M:%S'), l.action, l.ip_address or 'Localhost', l.details or ''])
    
    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=lexai_audit_trail.csv"}
    )

@settings_bp.route('/settings/api-keys/generate', methods=['POST'])
@login_required
def generate_api_key():
    """Generate a new secure developer API key and store its hash"""
    user_id = session['user_id']
    key_name = request.form.get('key_name', '').strip()

    if not key_name:
        flash('Please provide a name/label for the API key.', 'error')
        return redirect(url_for('settings.settings'))

    # Generate secure random token
    # Prefix with 'lex_live_' for clear identification
    raw_key = f"lex_live_{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    try:
        new_key = ApiKey(
            user_id=user_id,
            key_hash=key_hash,
            name=key_name
        )
        db.session.add(new_key)
        
        # Log action
        log = AuditLog(
            user_id=user_id,
            action='API_KEY_GENERATE',
            details=f"Generated new API Key named: {key_name}",
            ip_address=get_client_ip()
        )
        db.session.add(log)
        db.session.commit()

        # Display raw key once using a special session variable that gets cleared
        session['new_api_key'] = raw_key
        session['new_api_key_name'] = key_name
        flash('API Key generated successfully! Make sure to copy it now. You won\'t be able to see it again.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API Key Generation Error: {e}")
        flash('Failed to generate API Key.', 'error')

    return redirect(url_for('settings.settings'))

@settings_bp.route('/settings/api-keys/revoke/<int:key_id>', methods=['POST'])
@login_required
def revoke_api_key(key_id):
    """Revoke (delete) a developer API key"""
    user_id = session['user_id']
    key = ApiKey.query.filter_by(id=key_id, user_id=user_id).first_or_404()

    try:
        db.session.delete(key)
        
        # Log action
        log = AuditLog(
            user_id=user_id,
            action='API_KEY_REVOKE',
            details=f"Revoked API Key: {key.name}",
            ip_address=get_client_ip()
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f"API Key '{key.name}' revoked successfully.", 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API Key Revocation Error: {e}")
        flash('Failed to revoke API key.', 'error')

    return redirect(url_for('settings.settings'))
