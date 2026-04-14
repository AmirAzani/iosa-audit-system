from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Operator
from models import Finding

operator_bp = Blueprint('operator', __name__)

# ================================
# LIST OPERATORS (READ)
# ================================
@operator_bp.route("/operators")
@login_required
def list_operators():
    operators = Operator.query.all()
    return render_template("operators.html", operators=operators)

# ================================
# OPERATOR DETAIL PAGE
# ================================
@operator_bp.route("/operator/<int:id>")
@login_required
def operator_detail(id):

    operator = Operator.query.get_or_404(id)

    # import Audit here to avoid circular import
    from models import Audit

    audits = Audit.query.filter_by(operator_id=id).all()

    return render_template(
        "operator_details.html",
        operator=operator,
        audits=audits
    )


# ===============================
# DASHBOARD ROUTE
# ===============================
@operator_bp.route("/dashboard")
@login_required
def dashboard():
    from models import Operator, Finding, Audit
    
    # Get all operators
    operators = Operator.query.all()
    
    operator_stats = []
    total_findings = 0
    total_observations = 0
    
    for operator in operators:
        findings_count = 0
        observations_count = 0
        
        # Loop through all audits for this operator
        for audit in operator.audits:
            for finding in audit.findings:
                if finding.type == 'Finding':
                    findings_count += 1
                elif finding.type == 'Observation':
                    observations_count += 1
        
        total_findings += findings_count
        total_observations += observations_count
        
        operator_stats.append({
            'id': operator.id,
            'airline_name': operator.airline_name,
            'iata_code': operator.iata_code,
            'alliance': operator.alliance,
            'findings_count': findings_count,
            'observations_count': observations_count
        })
    
    # Sort by total findings + observations (highest first)
    operator_stats.sort(key=lambda x: x['findings_count'] + x['observations_count'], reverse=True)
    
    return render_template('dashboard.html',
                         operators=operators,
                         operator_stats=operator_stats,
                         total_findings=total_findings,
                         total_observations=total_observations)
# ================================
# ADD OPERATOR (CREATE)
# ================================
@operator_bp.route("/add_operator", methods=["POST"])
@login_required
def add_operator():

    airline_name = request.form.get("airline_name")
    iata_code = request.form.get("iata_code")
    alliance = request.form.get("alliance")

    new_operator = Operator(
        airline_name=airline_name,
        iata_code=iata_code,
        alliance=alliance
    )

    db.session.add(new_operator)
    db.session.commit()

    flash("Operator added successfully!")

    return redirect(url_for("operator.list_operators"))


# ================================
# EDIT OPERATOR PAGE
# ================================
@operator_bp.route("/edit_operator/<int:id>")
@login_required
def edit_operator(id):

    operator = Operator.query.get_or_404(id)

    return render_template(
        "edit_operator.html",
        operator=operator
    )


# ================================
# UPDATE OPERATOR (UPDATE)
# ================================
@operator_bp.route("/update_operator/<int:id>", methods=["POST"])
@login_required
def update_operator(id):

    operator = Operator.query.get_or_404(id)

    operator.airline_name = request.form.get("airline_name")
    operator.iata_code = request.form.get("iata_code")
    operator.alliance = request.form.get("alliance")

    db.session.commit()

    flash("Operator updated successfully!")

    return redirect(url_for("operator.list_operators"))


# ================================
# DELETE OPERATOR (DELETE)
# ================================
@operator_bp.route("/delete_operator/<int:id>")
@login_required
def delete_operator(id):

    operator = Operator.query.get_or_404(id)

    db.session.delete(operator)
    db.session.commit()

    flash("Operator deleted successfully!")

    return redirect(url_for("operator.list_operators"))