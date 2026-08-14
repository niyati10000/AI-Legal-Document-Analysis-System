from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from database import db, User, UserSetting, AuditLog
from functools import wraps
import re

auth_bp = Blueprint('auth', __name__)

def get_client_ip():
    """Helper to retrieve client IP address"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr

def login_required(f):
    """Decorator to protect routes requiring authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect routes requiring admin permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'Admin':
            flash('Unauthorized access. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Input validation
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Establish session
            session['user_id'] = user.id
            session['username'] = user.full_name or user.email.split('@')[0]
            session['role'] = user.role
            session.permanent = True

            # Log audit trail
            log = AuditLog(
                user_id=user.id,
                action='LOGIN',
                details=f"User {user.email} logged in successfully.",
                ip_address=get_client_ip()
            )
            db.session.add(log)
            db.session.commit()

            flash('Welcome back to LexAI!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            
            # Log failed login attempt
            log = AuditLog(
                user_id=None,
                action='LOGIN_FAILED',
                details=f"Failed login attempt for email: {email}",
                ip_address=get_client_ip()
            )
            db.session.add(log)
            db.session.commit()

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not full_name or not email or not password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')

        # Basic email format check
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email format.', 'error')
            return render_template('register.html')

        # Check existing user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address is already registered.', 'error')
            return render_template('register.html')

        try:
            # Create user (First user registered defaults to Admin role, subsequent users default to Analyst)
            user_count = User.query.count()
            role = 'Admin' if user_count == 0 else 'Analyst'

            new_user = User(
                email=email,
                full_name=full_name,
                role=role
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush()  # Generate user ID for foreign keys

            # Initialize user settings
            settings = UserSetting(
                user_id=new_user.id,
                default_summary_length='medium',
                bias_threshold=0.3,
                pii_masking_enabled=True
            )
            db.session.add(settings)

            # Log audit trail
            log = AuditLog(
                user_id=new_user.id,
                action='REGISTER',
                details=f"New user registered: {email} with role: {role}",
                ip_address=get_client_ip()
            )
            db.session.add(log)
            db.session.commit()

            # Automatically log in the user after registering
            session['user_id'] = new_user.id
            session['username'] = new_user.full_name
            session['role'] = new_user.role
            session.permanent = True

            flash('Registration successful! Welcome to LexAI.', 'success')
            return redirect(url_for('dashboard.dashboard'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    user_id = session.get('user_id')
    if user_id:
        # Log logout event
        log = AuditLog(
            user_id=user_id,
            action='LOGOUT',
            details="User logged out.",
            ip_address=get_client_ip()
        )
        db.session.add(log)
        db.session.commit()

    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
