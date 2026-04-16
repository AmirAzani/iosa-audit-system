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
    from collections import defaultdict
    from datetime import datetime
    
    # Get all operators
    operators = Operator.query.all()
    
    operator_stats = []
    total_findings = 0
    total_observations = 0
    
    # Yearly stats
    year_stats_dict = defaultdict(lambda: {'findings': 0, 'observations': 0, 'operators': set()})
    
    # ISARP stats (extract prefix from ISARP code)
    isarp_stats_dict = defaultdict(int)
    
    # ISARP category mapping
    isarp_categories = {
        'ORG': 'Organization',
        'MNT': 'Maintenance',
        'FLT': 'Flight Operations',
        'CAB': 'Cabin',
        'GRH': 'Ground Handling',
        'SEC': 'Security',
        'DGR': 'Dangerous Goods',
        'CGO': 'Cargo',
        'DSP': 'Dispatch',
        'OTHER': 'Other'
    }
    
    for operator in operators:
        findings_count = 0
        observations_count = 0
        
        for audit in operator.audits:
            # Extract year from audit_date
            if audit.audit_date:
                year = audit.audit_date.year
                year_stats_dict[year]['operators'].add(operator.id)
            else:
                year = None
            
            for finding in audit.findings:
                if finding.type == 'Finding':
                    findings_count += 1
                    total_findings += 1
                    year_stats_dict[year]['findings'] += 1
                elif finding.type == 'Observation':
                    observations_count += 1
                    total_observations += 1
                    year_stats_dict[year]['observations'] += 1
                
                # ISARP analysis - extract prefix (first 3 characters)
                isarp_code = finding.isarp_code or ''
                if len(isarp_code) >= 3:
                    prefix = isarp_code[:3].upper()
                    if prefix in isarp_categories:
                        isarp_stats_dict[prefix] += 1
                    else:
                        isarp_stats_dict['OTHER'] += 1
                else:
                    isarp_stats_dict['OTHER'] += 1
        
        operator_stats.append({
            'id': operator.id,
            'airline_name': operator.airline_name,
            'iata_code': operator.iata_code,
            'alliance': operator.alliance,
            'findings_count': findings_count,
            'observations_count': observations_count
        })
    
    # Sort operator_stats by total
    operator_stats.sort(key=lambda x: x['findings_count'] + x['observations_count'], reverse=True)
    
    # Prepare year_stats list sorted by year
    year_stats = []
    for year in sorted(year_stats_dict.keys()):
        if year:  # Skip None
            year_stats.append({
                'year': year,
                'findings': year_stats_dict[year]['findings'],
                'observations': year_stats_dict[year]['observations'],
                'operator_count': len(year_stats_dict[year]['operators'])
            })
    
    # Prepare ISARP stats list
    isarp_stats = []
    total_isarp = sum(isarp_stats_dict.values())
    for prefix, count in sorted(isarp_stats_dict.items(), key=lambda x: x[1], reverse=True):
        isarp_stats.append({
            'category': f"{prefix} - {isarp_categories.get(prefix, 'Other')}",
            'description': isarp_categories.get(prefix, 'Other ISARP categories'),
            'count': count,
            'percentage': (count / total_isarp * 100) if total_isarp > 0 else 0
        })
    
    # Get top ISARP category
    top_isarp_category = isarp_stats[0]['category'] if isarp_stats else 'N/A'
    
    return render_template('dashboard.html',
                         operators=operators,
                         operator_stats=operator_stats,
                         total_findings=total_findings,
                         total_observations=total_observations,
                         year_stats=year_stats,
                         isarp_stats=isarp_stats,
                         top_isarp_category=top_isarp_category)


# ===============================
# JSON data to the dashboard
# ===============================

@operator_bp.route("/api/dashboard-data")
@login_required
def api_dashboard_data():
    from models import Operator, Finding, Audit
    from collections import defaultdict
    
    operators = Operator.query.all()
    
    operator_stats = []
    operator_names = []
    findings_data = []
    observations_data = []
    total_findings = 0
    total_observations = 0
    
    # Yearly stats
    year_stats_dict = defaultdict(lambda: {'findings': 0, 'observations': 0, 'operators': set()})
    
    # ISARP stats - COMPLETE LIST OF 8 DISCIPLINES
    isarp_stats_dict = defaultdict(int)
    isarp_categories = {
        'ORG': 'Organization (Corporate Organization & Management System)',
        'FLT': 'Flight Operations',
        'DSP': 'Operational Control & Flight Dispatch',
        'MNT': 'Aircraft Engineering & Maintenance',
        'CAB': 'Cabin Operations',
        'GRH': 'Ground Handling Operations',
        'CGO': 'Cargo Operations',
        'SEC': 'Security Management'
    }
    
    for operator in operators:
        f_count = 0
        o_count = 0
        
        for audit in operator.audits:
            year = audit.audit_date.year if audit.audit_date else None
            if year:
                year_stats_dict[year]['operators'].add(operator.id)
            
            for finding in audit.findings:
                if finding.type == 'Finding':
                    f_count += 1
                    total_findings += 1
                    if year:
                        year_stats_dict[year]['findings'] += 1
                else:
                    o_count += 1
                    total_observations += 1
                    if year:
                        year_stats_dict[year]['observations'] += 1
                
                # ISARP analysis - extract first 3 characters of ISARP code
                code = (finding.isarp_code or '')[:3].upper()
                if code in isarp_categories:
                    isarp_stats_dict[f"{code} - {isarp_categories[code]}"] += 1
                else:
                    isarp_stats_dict['Other - Other ISARP Category'] += 1
        
        operator_stats.append({
            'id': operator.id,
            'airline_name': operator.airline_name,
            'iata_code': operator.iata_code,
            'findings_count': f_count,
            'observations_count': o_count
        })
        operator_names.append(operator.airline_name)
        findings_data.append(f_count)
        observations_data.append(o_count)
    
    # Sort operator_stats
    operator_stats.sort(key=lambda x: x['findings_count'] + x['observations_count'], reverse=True)
    
    # Year stats
    year_stats = []
    years = []
    year_findings = []
    year_observations = []
    for year in sorted(year_stats_dict.keys()):
        if year:
            years.append(year)
            year_findings.append(year_stats_dict[year]['findings'])
            year_observations.append(year_stats_dict[year]['observations'])
            year_stats.append({
                'year': year,
                'findings': year_stats_dict[year]['findings'],
                'observations': year_stats_dict[year]['observations'],
                'operator_count': len(year_stats_dict[year]['operators'])
            })
    
    # ISARP stats - sort by count (highest first)
    isarp_stats = []
    for cat, count in sorted(isarp_stats_dict.items(), key=lambda x: x[1], reverse=True):
        isarp_stats.append({
            'category': cat,
            'count': count,
            'percentage': (count / total_findings * 100) if total_findings > 0 else 0
        })
    
    return {
        'operatorStats': operator_stats,
        'operatorNames': operator_names,
        'findingsData': findings_data,
        'observationsData': observations_data,
        'totalFindings': total_findings,
        'totalObservations': total_observations,
        'yearStats': year_stats,
        'years': years,
        'yearFindings': year_findings,
        'yearObservations': year_observations,
        'isarpStats': isarp_stats
    }

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