from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Audit, Operator
from datetime import datetime

audit_bp = Blueprint('audit', __name__)

# ================================
# LIST AUDITS
# ================================
@audit_bp.route("/audits")
@login_required
def list_audits():

    audits = Audit.query.all()

    return render_template(
        "audits.html",
        audits=audits
    )

# ================================
# AUDIT DETAIL PAGE
# ================================
@audit_bp.route("/audit/<int:audit_id>")
@login_required
def audit_detail(audit_id):

    audit = Audit.query.get_or_404(audit_id)

    # import here to avoid circular import
    from models import Finding

    findings = Finding.query.filter_by(audit_id=audit_id).all()

    total_findings = Finding.query.filter_by(
        audit_id=audit_id,
        type="Finding"
    ).count()

    total_observations = Finding.query.filter_by(
        audit_id=audit_id,
        type="Observation"
    ).count()

    return render_template(
        "audit_detail.html",
        audit=audit,
        findings=findings,
        total_findings=total_findings,
        total_observations=total_observations
    )

# ================================
# ADD AUDIT PAGE
# ================================
@audit_bp.route("/add_audit")
@login_required
def add_audit_page():

    # get operator id from URL
    operator_id = request.args.get("operator_id")

    operators = Operator.query.all()

    return render_template(
        "add_audit.html",
        operators=operators,
        selected_operator=operator_id
    )


# ================================
# SAVE AUDIT
# ================================
@audit_bp.route("/save_audit", methods=["POST"])
@login_required
def save_audit():

    operator_id = request.form.get("operator_id")
    audit_type = request.form.get("audit_type")
    audit_year = request.form.get("audit_year")  # Keep as audit_year from form
    auditor_name = request.form.get("auditor_name")
    status = request.form.get("status")

    # Convert year to date (use January 1st of that year)
    if audit_year:
        audit_date = datetime(int(audit_year), 1, 1).date()
    else:
        audit_date = None

    new_audit = Audit(
        operator_id=operator_id,
        audit_type=audit_type,
        audit_date=audit_date,  # Model uses audit_date
        auditor_name=auditor_name,
        status=status
    )

    db.session.add(new_audit)
    db.session.commit()

    flash("Audit added successfully!")

    # redirect back to operator page
    return redirect(url_for("operator.operator_detail", id=operator_id))


# ================================
# EDIT AUDIT PAGE
# ================================
@audit_bp.route("/edit_audit/<int:audit_id>", methods=["GET", "POST"])
@login_required
def edit_audit(audit_id):

    audit = Audit.query.get_or_404(audit_id)

    if request.method == "POST":
        # Update audit details
        audit.audit_type = request.form.get("audit_type")
        audit_year = request.form.get("audit_year")
        if audit_year:
            audit.audit_date = datetime(int(audit_year), 1, 1).date()
        audit.auditor_name = request.form.get("auditor_name")
        audit.status = request.form.get("status")

        db.session.commit()
        flash("Audit updated successfully!", "success")
        return redirect(url_for("audit.audit_detail", audit_id=audit.id))

    # Extract year from audit_date for display
    audit_year = audit.audit_date.year if audit.audit_date else None

    return render_template(
        "edit_audit.html",
        audit=audit,
        audit_year=audit_year
    )


# ================================
# DELETE AUDIT
# ================================
@audit_bp.route("/delete_audit/<int:audit_id>", methods=["POST"])
@login_required
def delete_audit(audit_id):

    audit = Audit.query.get_or_404(audit_id)
    operator_id = audit.operator_id

    # Delete all findings related to this audit first
    from models import Finding
    Finding.query.filter_by(audit_id=audit_id).delete()

    db.session.delete(audit)
    db.session.commit()

    flash("Audit deleted successfully!", "success")
    return redirect(url_for("operator.operator_detail", id=operator_id))