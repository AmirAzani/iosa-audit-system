from flask import Flask, redirect, url_for, render_template, request
from extensions import db, login_manager, bcrypt
from flask_migrate import Migrate
import os
import pandas as pd
from models import Finding, User, Operator, Audit

# ======================
# App Initialization
# ======================
app = Flask(__name__)

# ======================
# App Configuration
# ======================
app.config['SECRET_KEY'] = 'supersecretkey'

# MySQL Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/iosa_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Temporary storage for Excel data during import
temp_data = None
temp_audit_id = None

# ======================
# Helper Functions
# ======================

def clean_excel(df):
    """Clean Excel dataframe by finding the header row and normalizing columns"""
    start_row = None

    # Find the row that contains "ISARP"
    for i, row in df.iterrows():
        if "ISARP" in str(row.values):
            start_row = i
            break

    if start_row is not None:
        df = df.iloc[start_row:]
        df.columns = df.iloc[0]
        df = df[1:]

    # Normalize column names (strip spaces and convert to uppercase)
    df.columns = df.columns.str.strip().str.upper()

    return df


def validate_data(df):
    """Validate the dataframe for required fields"""
    errors = []

    for index, row in df.iterrows():
        # Check for ISARP NUMBER
        if pd.isna(row.get('ISARP NUMBER')) and pd.isna(row.get('ISARP')):
            errors.append(f"Row {index + 2}: Missing ISARP Number/Code")

        # Check for ROOT CAUSE
        if pd.isna(row.get('ROOT CAUSE')):
            errors.append(f"Row {index + 2}: Missing Root Cause")

    return errors


# ======================
# Initialize Extensions
# ======================
db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
bcrypt.init_app(app)

# ======================
# Login Manager Setup
# ======================
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# ======================
# Import Models
# ======================
from models import User, Operator, Audit

# ======================
# User Loader
# ======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ======================
# Home Route
# ======================
@app.route("/")
def home():
    return redirect(url_for("operator.list_operators"))


# ======================
# Upload Routes
# ======================
@app.route('/upload-page')
def upload_page():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and display available sheets"""
    file = request.files['file']
    audit_id = request.form.get('audit_id')

    if file and file.filename.endswith('.xlsx'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Read Excel file
        excel = pd.ExcelFile(filepath)
        sheets = excel.sheet_names

        return render_template(
            'preview.html',
            sheets=sheets,
            filename=file.filename,
            audit_id=audit_id
        )

    return "Invalid file. Please upload an Excel file (.xlsx)"


@app.route('/process', methods=['POST'])
def process_sheet():
    """Process selected sheet, clean data, and show preview"""
    filename = request.form['filename']
    sheet = request.form['sheet']
    audit_id = request.form.get('audit_id')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Read Excel
    df = pd.read_excel(filepath, sheet_name=sheet)

    # Clean Excel
    df = clean_excel(df)

    # Validate
    errors = validate_data(df)

    # Save temporarily for import
    global temp_data, temp_audit_id
    temp_data = df
    temp_audit_id = audit_id

    # Convert dataframe to HTML for preview
    table_html = df.head(10).to_html(index=False)

    return render_template(
        "preview.html",
        tables=[table_html],  # Pass as list to match template expectation
        errors=errors,
        filename=filename,
        sheets=[sheet],  # Keep as list for consistency
        audit_id=audit_id,
        total_rows=len(df)
    )


@app.route('/import', methods=['POST'])
def import_data():
    """Import validated data into database with duplicate prevention"""
    global temp_data, temp_audit_id

    if temp_data is None:
        return "No data to import. Please upload and process a file first."

    audit_id = temp_audit_id

    # Verify audit exists
    audit = Audit.query.get(audit_id)
    if not audit:
        return f"""
        <html>
        <head>
            <style>
                body {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .container {{
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    text-align: center;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 500px;
                }}
                .error {{ color: #dc3545; font-size: 3em; margin-bottom: 20px; }}
                h2 {{ color: #495057; margin-bottom: 20px; }}
                .btn {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">✗</div>
                <h2>Import Failed</h2>
                <p>Audit ID {audit_id} not found!</p>
                <a href="/upload-page" class="btn">Try Again</a>
            </div>
        </body>
        </html>
        """

    imported_count = 0
    skipped_count = 0
    error_count = 0

    for _, row in temp_data.iterrows():
        try:
            # Extract data with fallbacks
            isarp = str(row.get('ISARP NUMBER') or row.get('ISARP') or "").strip()
            
            if not isarp:
                skipped_count += 1
                continue

            # Check for duplicate to prevent re-importing
            existing = Finding.query.filter_by(
                audit_id=audit_id,
                isarp_code=isarp
            ).first()

            if existing:
                skipped_count += 1
                continue

            # Extract other fields
            root_cause = str(row.get('ROOT CAUSE') or row.get('ROOT_CAUSE') or "")
            corrective_action = str(row.get('CORRECTION ACTION') or row.get('CORRECTIVE_ACTION') or "")
            requirement = str(row.get('REQUIREMENT') or row.get('ISARP REQUIREMENT') or "")
            finding_type = str(row.get('TYPE') or row.get('Type') or "Finding")
            
            # Determine type (Finding or Observation)
            if finding_type.lower() == 'observation':
                finding_type = 'Observation'
            else:
                finding_type = 'Finding'

            # Create finding object
            finding = Finding(
                audit_id=audit_id,
                type=finding_type,
                isarp_code=isarp,
                isarp_requirement=requirement if requirement else 'Not specified',
                root_cause=root_cause if root_cause else '',
                corrective_action=corrective_action if corrective_action else '',
                status='Open'
            )
            
            db.session.add(finding)
            imported_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"Error importing row: {e}")

    db.session.commit()

    # Clear temp data after import
    temp_data = None
    temp_audit_id = None

    # Redirect back to the audit page after successful import
    return redirect(url_for('audit.audit_detail', audit_id=audit_id))


# ======================
# Register Blueprints
# ======================
from routes.auth import auth_bp
from routes.operator import operator_bp
from routes.audit import audit_bp
from routes.finding import finding_bp

app.register_blueprint(auth_bp)
app.register_blueprint(operator_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(finding_bp)

# ======================
# Create Tables (Dev Only)
# ======================
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")

# ======================
# Run Application
# ======================
if __name__ == "__main__":
    app.run(debug=True)