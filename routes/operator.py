from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Operator

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