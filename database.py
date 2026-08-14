from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# Association table for Document <-> Tag many-to-many relationship
document_tags = db.Table('document_tags',
    db.Column('doc_id', db.Integer, db.ForeignKey('legal_documents.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model):
    """User accounts table"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(50), default='Analyst', nullable=False)
    bio = db.Column(db.String(255), default='AI-driven legal document intelligence and contract bias auditing workspace.', nullable=True)
    organization = db.Column(db.String(100), default='LexAI Legal Tech', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    documents = db.relationship('LegalDocument', backref='owner', lazy=True, cascade='all, delete-orphan')
    settings = db.relationship('UserSetting', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    api_keys = db.relationship('ApiKey', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', backref='creator', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Set user password with secure scrypt hashing"""
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        """Verify user password"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class UserSetting(db.Model):
    """User analysis preferences settings"""
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    default_summary_length = db.Column(db.String(50), default='medium', nullable=False)  # short, medium, detailed
    bias_threshold = db.Column(db.Float, default=0.3, nullable=False)
    pii_masking_enabled = db.Column(db.Boolean, default=True, nullable=False)
    ai_model = db.Column(db.String(50), default='gemini-3.5-flash', nullable=False)  # gemini-3.5-flash, gemini-pro, local-rules
    legal_domain = db.Column(db.String(100), default='General Corporate', nullable=False)  # General Corporate, Employment & HR, IP & Patents, Real Estate

    def __repr__(self):
        return f'<UserSetting user_id={self.user_id}>'


class ApiKey(db.Model):
    """Developer API Keys table"""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    key_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)  # SHA-256 hash of API key
    name = db.Column(db.String(100), nullable=False)  # Label for the key
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<ApiKey id={self.id} name={self.name}>'


class AuditLog(db.Model):
    """Security audit logs ledger"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # LOGIN, UPLOAD, VIEW, DELETE, KEY_GEN, etc.
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<AuditLog user_id={self.user_id} action={self.action}>'


class LegalDocument(db.Model):
    """Core Legal Documents metadata table"""
    __tablename__ = 'legal_documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    doc_type = db.Column(db.String(100), nullable=False)  # Contract, Judgment, Case Law, Statute, Agreement
    current_status = db.Column(db.String(50), default='queued', nullable=False)  # queued, extracting, analyzing, completed, failed
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    versions = db.relationship('DocumentVersion', backref='document', lazy=True, cascade='all, delete-orphan', order_by='DocumentVersion.version_number.desc()')
    summary = db.relationship('Summary', backref='document', uselist=False, lazy=True, cascade='all, delete-orphan')
    bias_report = db.relationship('BiasReport', backref='document', uselist=False, lazy=True, cascade='all, delete-orphan')
    entities = db.relationship('Entity', backref='document', uselist=False, lazy=True, cascade='all, delete-orphan')
    
    # Many-to-many relationship with tags
    tags = db.relationship('Tag', secondary=document_tags, backref=db.backref('documents', lazy=True))

    @property
    def latest_version(self):
        """Helper to get latest version model"""
        return self.versions[0] if self.versions else None

    def __repr__(self):
        return f'<LegalDocument id={self.id} title={self.title}>'


class DocumentVersion(db.Model):
    """Document text revisions history tracking table"""
    __tablename__ = 'document_versions'

    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey('legal_documents.id', ondelete='CASCADE'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    content = db.Column(db.Text, nullable=False)  # Raw extracted text content
    filename = db.Column(db.String(255), nullable=True)  # Name of uploaded file
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<DocumentVersion doc_id={self.doc_id} version={self.version_number}>'


class Summary(db.Model):
    """AI Generated Summaries table"""
    __tablename__ = 'summaries'

    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey('legal_documents.id', ondelete='CASCADE'), unique=True, nullable=False)
    summary_text = db.Column(db.Text, nullable=False)
    length_setting = db.Column(db.String(50), default='medium', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Summary doc_id={self.doc_id}>'


class BiasReport(db.Model):
    """AI Generated Bias Analysis Reports table"""
    __tablename__ = 'bias_reports'

    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey('legal_documents.id', ondelete='CASCADE'), unique=True, nullable=False)
    bias_score = db.Column(db.Float, default=0.0, nullable=False)
    bias_type = db.Column(db.String(100), default='None', nullable=False)  # Primary bias type
    explanation = db.Column(db.Text, nullable=True)
    categories_json = db.Column(db.Text, nullable=False)  # JSON-string of bias categories details
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def categories(self):
        """Deserialized categories JSON dictionary helper"""
        try:
            return json.loads(self.categories_json)
        except:
            return {}

    @categories.setter
    def categories(self, value):
        self.categories_json = json.dumps(value)

    def __repr__(self):
        return f'<BiasReport doc_id={self.doc_id} score={self.bias_score}>'


class Entity(db.Model):
    """AI Extracted Entities (NER) table"""
    __tablename__ = 'entities'

    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey('legal_documents.id', ondelete='CASCADE'), unique=True, nullable=False)
    entities_json = db.Column(db.Text, nullable=False)  # JSON-string of extracted entities categorized
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def data(self):
        """Deserialized entities dictionary helper"""
        try:
            return json.loads(self.entities_json)
        except:
            return {}

    @data.setter
    def data(self, value):
        self.entities_json = json.dumps(value)

    def __repr__(self):
        return f'<Entity doc_id={self.doc_id}>'


class Tag(db.Model):
    """Custom categorization tags table"""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tag_name = db.Column(db.String(100), nullable=False)

    # Enforce uniqueness of tag per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'tag_name', name='_user_tag_uc'),
    )

    def __repr__(self):
        return f'<Tag {self.tag_name}>'
