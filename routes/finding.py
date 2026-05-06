from flask import Blueprint, render_template, request, redirect, url_for, send_file, flash
from flask_login import login_required
from models import Finding, Audit, db
from openpyxl import Workbook
import io

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

    # Get audit_id first
    audit_id = request.form["audit_id"]
    
    new_finding = Finding(
        audit_id=audit_id,
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
    
    # Flash success message
    flash("Finding / Observation saved successfully!", "success")
    
    # ✅ Redirect to AUDIT DETAIL page (since audit_detail route exists!)
    return redirect(url_for("audit.audit_detail", audit_id=audit_id))


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


# ===============================
# DELETE FINDING
# ===============================
@finding_bp.route("/delete_finding/<int:finding_id>", methods=["POST"])
@login_required
def delete_finding(finding_id):

    finding = Finding.query.get_or_404(finding_id)
    audit_id = finding.audit.id

    db.session.delete(finding)
    db.session.commit()
    
    flash("Finding / Observation deleted successfully!", "success")

    return redirect(url_for("audit.audit_detail", audit_id=audit_id))


# ===============================
# EDIT FINDING
# ===============================
@finding_bp.route("/edit_finding/<int:finding_id>", methods=["GET", "POST"])
@login_required
def edit_finding(finding_id):

    finding = Finding.query.get_or_404(finding_id)

    if request.method == "POST":
        finding.type = request.form.get("type")              # ← ADD THIS LINE
        finding.root_cause = request.form.get("root_cause")
        finding.corrective_action = request.form.get("corrective_action")
        finding.final_review = request.form.get("final_review")

        db.session.commit()
        
        flash("Finding / Observation updated successfully!", "success")

        return redirect(url_for("finding.view_finding", finding_id=finding.id))

    return render_template("edit_finding.html", finding=finding)
    
# ===============================
# EXPORT FINDINGS TO EXCEL
# ===============================
@finding_bp.route("/export/<int:audit_id>")
@login_required
def export_excel(audit_id):

    audit = Audit.query.get_or_404(audit_id)
    findings = Finding.query.filter_by(audit_id=audit_id).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Findings"

    # Header
    ws.append([
        "Type",
        "ISARP Code",
        "Requirement",
        "Root Cause",
        "Corrective Action",
        "Final Review",
        "Status"
    ])

    # Data
    for f in findings:
        ws.append([
            f.type,
            f.isarp_code,
            f.isarp_requirement,
            f.root_cause,
            f.corrective_action,
            f.final_review,
            f.status
        ])

    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        download_name=f"audit_{audit_id}_findings.xlsx",
        as_attachment=True
    )