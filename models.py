from extensions import db
from flask_login import UserMixin
from datetime import datetime

# ===============================
# User Model
# ===============================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # email = db.Column(db.String(120), unique=True, nullable=False) #
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'


# ===============================
# Operator Model
# ===============================
class Operator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    airline_name = db.Column(db.String(100), nullable=False)
    iata_code = db.Column(db.String(2), nullable=False)
    alliance = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    audits = db.relationship('Audit', backref='operator', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Operator {self.airline_name}>'


# ===============================
# Audit Model
# ===============================
class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    audit_type = db.Column(db.String(50), nullable=False)
    audit_date = db.Column(db.Date, nullable=False)
    auditor_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='Planned')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    findings = db.relationship('Finding', backref='audit', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Audit {self.audit_type} - {self.audit_date}>'


# ===============================
# Finding Model
# ===============================
class Finding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'finding' or 'observation'
    isarp_code = db.Column(db.String(50), nullable=False)
    isarp_requirement = db.Column(db.Text, nullable=False)
    finding_details = db.Column(db.Text, nullable=True)
    root_cause = db.Column(db.Text, nullable=True)
    corrective_action = db.Column(db.Text, nullable=True)
    final_review = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Finding {self.isarp_code} - {self.type}>'