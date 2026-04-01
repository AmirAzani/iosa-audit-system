from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from models import Finding, Audit, db

finding_bp = Blueprint("finding", __name__)

# ===============================
# LIST FINDINGS
# ===============================
@finding_bp.route("/findings")
@login_required
def list_findings():

    findings = Finding.query.all()

    return render_template(
        "findings.html",
        findings=findings
    )


# ===============================
# ADD FINDING PAGE
# ===============================
@finding_bp.route("/add_finding")
@login_required
def add_finding():

    audit_id = request.args.get("audit_id")

    audit = Audit.query.get_or_404(audit_id)

    return render_template(
        "add_finding.html",
        audit=audit
    )


# ===============================
# SAVE FINDING
# ===============================
@finding_bp.route("/save_finding", methods=["POST"])
@login_required
def save_finding():

    new_finding = Finding(

        audit_id=request.form["audit_id"],
        type=request.form["type"],

        isarp_code=request.form["isarp_code"],
        isarp_requirement=request.form["isarp_requirement"],

        finding_details=request.form["finding_details"],

        root_cause=request.form["root_cause"],

        corrective_action=request.form["corrective_action"],
        final_review=request.form["final_review"],

        status=request.form["status"]
    )

    db.session.add(new_finding)
    db.session.commit()

    return redirect(url_for("finding.list_findings"))


# ===============================
# VIEW FINDING DETAILS
# ===============================
@finding_bp.route("/finding/<int:finding_id>")
@login_required
def view_finding(finding_id):

    finding = Finding.query.get_or_404(finding_id)

    return render_template(
        "view_finding.html",
        finding=finding
    )