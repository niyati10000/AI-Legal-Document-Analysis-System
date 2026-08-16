import os
import sys
from dotenv import load_dotenv; load_dotenv()

from flask import Flask, render_template, redirect, url_for, session, make_response
from database import db, LegalDocument
from config import config_by_name
from services.worker import start_worker
from blueprints.auth import auth_bp
from blueprints.settings import settings_bp
from blueprints.dashboard import dashboard_bp
from blueprints.api import api_bp

# Set the active config environment ('dev', 'prod', or 'test')
config_name = os.environ.get('FLASK_ENV', 'dev')

app = Flask(__name__)
app.config.from_object(config_by_name[config_name])

# Initialize SQLAlchemy Database extension
db.init_app(app)

# Register Blueprint Route Controllers
app.register_blueprint(auth_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)

# ===== GLOBAL ROUTING =====

@app.route('/')
def index():
    """Landing Page showing public/recent uploads"""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    
    # Query last 5 uploaded documents globally
    try:
        documents = LegalDocument.query.order_by(LegalDocument.uploaded_at.desc()).limit(5).all()
    except Exception as e:
        app.logger.warning(f"Failed to query index documents: {e}")
        documents = []
        
    return render_template('index.html', documents=documents)

@app.route('/help')
def help():
    """Render static help documentation"""
    return render_template('help.html')

@app.route('/profile')
def profile():
    """Redirect deprecated profile path to settings"""
    return redirect(url_for('settings.settings'))

# ===== GLOBAL ERROR HANDLERS =====

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # Rollback failed DB transaction
    return render_template('500.html'), 500

# ===== DATABASE INITIALIZATION & SEEDING =====

def initialize_database():
    """Ensure database schema is created and default demo account is seeded"""
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()

        # Migrate new columns gracefully in SQLite
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                for col, defn in [('bio', 'VARCHAR(255)'), ('organization', 'VARCHAR(100)')]:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {defn}"))
                        conn.commit()
                    except Exception:
                        pass
                for col, defn in [('ai_model', 'VARCHAR(50) DEFAULT \'gemini-3.5-flash\''), ('legal_domain', 'VARCHAR(100) DEFAULT \'General Corporate\'')]:
                    try:
                        conn.execute(text(f"ALTER TABLE user_settings ADD COLUMN {col} {defn}"))
                        conn.commit()
                    except Exception:
                        pass
        except Exception as e:
            app.logger.warning(f"Column migration notice: {e}")
        
        # Check and seed standard demo account
        from database import User, UserSetting
        demo_email = 'demo@lexai.com'
        demo_user = User.query.filter_by(email=demo_email).first()
        
        if not demo_user:
            app.logger.info("Initializing database: seeding demo account...")
            demo_user = User(
                email=demo_email,
                full_name='Demo User',
                role='Admin',
                bio='AI-driven legal document intelligence, contract bias auditing, and compliance verification workspace.',
                organization='LexAI Legal Solutions'
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.flush()  # Generate primary user ID
            
            # Create user settings
            demo_settings = UserSetting(
                user_id=demo_user.id,
                default_summary_length='medium',
                bias_threshold=0.3,
                pii_masking_enabled=True,
                ai_model='gemini-3.5-flash',
                legal_domain='General Corporate'
            )
            db.session.add(demo_settings)
            db.session.commit()
            app.logger.info("Demo user 'demo@lexai.com' seeded successfully!")

# ===== APPLICATION START =====

if __name__ == '__main__':
    # Initialize schema and seed user
    initialize_database()
    
    # Spawn background analysis worker thread
    start_worker(app)
    
    port = int(os.environ.get('PORT', 5000))
    # Run development server
    # Set use_reloader=False when starting background threads to prevent running worker twice
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)