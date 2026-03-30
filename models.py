from extensions import db
from flask_login import UserMixin


# ===============================
# USER TABLE
# ===============================
class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="viewer")


# ===============================
# OPERATOR TABLE
# ===============================
class Operator(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    airline_name = db.Column(db.String(100), nullable=False)
    iata_code = db.Column(db.String(10))
    alliance = db.Column(db.String(50))


# ===============================
# AUDIT TABLE
# ===============================
class Audit(db.Model):

    __tablename__ = "audits"

    id = db.Column(db.Integer, primary_key=True)

    operator_id = db.Column(
        db.Integer,
        db.ForeignKey("operator.id"),
        nullable=False
    )

    audit_type = db.Column(db.String(50))

    audit_year = db.Column(db.Integer)   # ✅ CHANGED

    auditor_name = db.Column(db.String(100))
    status = db.Column(db.String(50))

    operator = db.relationship("Operator", backref="audits")
    
# ===============================
# FINDINGS / OBSERVATIONS TABLE
# ===============================
class Finding(db.Model):

    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)

    audit_id = db.Column(
        db.Integer,
        db.ForeignKey("audits.id"),   # ✅ FIXED HERE
        nullable=False
    )

    type = db.Column(db.String(20))  # Finding / Observation

    isarp_code = db.Column(db.String(20))
    isarp_requirement = db.Column(db.Text)

    finding_details = db.Column(db.Text)

    root_cause = db.Column(db.String(100))

    corrective_action = db.Column(db.Text)
    final_review = db.Column(db.Text)

    status = db.Column(db.String(20))  # Open / Closed

    audit = db.relationship("Audit", backref="findings")