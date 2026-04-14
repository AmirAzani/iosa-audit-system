from flask import Flask, redirect, url_for, render_template, request, session
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
# Configuration
# ======================
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')

# Database URL - Use environment variable for production, local for development
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Aiven MySQL URL format (mysql:// -> mysql+pymysql://)
    if database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', 'mysql+pymysql://')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/iosa_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folder configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ======================
# Init Extensions
# ======================
db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
bcrypt.init_app(app)

# ======================
# Login Setup
# ======================
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ======================
# Helper Functions
# ======================
def clean_excel(df):
    start_row = None

    for i, row in df.iterrows():
        if "ISARP" in str(row.values):
            start_row = i
            break

    if start_row is not None:
        df = df.iloc[start_row:]
        df.columns = df.iloc[0]
        df = df[1:]

    df.columns = df.columns.str.strip().str.upper()
    return df


def validate_data(df):
    errors = []

    for index, row in df.iterrows():
        if pd.isna(row.get('ISARP NUMBER')) and pd.isna(row.get('ISARP')):
            errors.append(f"Row {index + 2}: Missing ISARP")

    return errors

# ======================
# Home
# ======================
@app.route("/")
def home():
    return redirect(url_for("operator.list_operators"))

# ======================
# STEP 1 — Upload
# ======================
@app.route('/upload', methods=['POST'])
def upload_file():
    print("🔥 UPLOAD ROUTE HIT")

    if 'file' not in request.files:
        print("❌ No file in request")
        return "No file uploaded"

    file = request.files['file']
    audit_id = request.form.get('audit_id')

    print("Audit ID:", audit_id)
    print("Filename:", file.filename)

    if file.filename == '':
        print("❌ Empty filename")
        return "No selected file"

    if file and file.filename.endswith('.xlsx'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        print("✅ File saved at:", filepath)

        excel = pd.ExcelFile(filepath)
        sheets = excel.sheet_names

        print("Sheets:", sheets)

        return render_template(
            'preview.html',
            sheets=sheets,
            filename=file.filename,
            audit_id=audit_id
        )

    print("❌ Invalid file type")
    return "Invalid file"

# ======================
# STEP 2 — Process
# ======================
@app.route('/process', methods=['POST'])
def process_sheet():
    filename = request.form['filename']
    sheet = request.form['sheet']
    audit_id = request.form['audit_id']

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    df = pd.read_excel(filepath, sheet_name=sheet)
    df = clean_excel(df)

    errors = validate_data(df)

    table_html = df.head(10).to_html(index=False)

    excel = pd.ExcelFile(filepath)

    return render_template(
        'preview.html',
        tables=[table_html],
        errors=errors,
        filename=filename,
        sheets=excel.sheet_names,
        audit_id=audit_id,
        selected_sheet=sheet
    )

# ======================
# STEP 3 — Import
# ======================
@app.route('/import', methods=['POST'])
def import_data():
    audit_id = request.form.get('audit_id')
    filename = request.form.get('filename')
    sheet = request.form.get('sheet')

    if not filename or not sheet:
        return "Missing filename or sheet"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return "File not found"

    df = pd.read_excel(filepath, sheet_name=sheet)
    df = clean_excel(df)

    imported = 0
    for _, row in df.iterrows():
        isarp = str(row.get('ISARP NUMBER') or row.get('ISARP') or "").strip()
        
        if not isarp:
            continue

        # Check for duplicate
        existing = Finding.query.filter_by(audit_id=audit_id, isarp_code=isarp).first()
        if existing:
            continue

        finding = Finding(
            audit_id=audit_id,
            type='Finding',
            isarp_code=isarp,
            isarp_requirement=str(row.get('REQUIREMENT') or ''),
            root_cause=str(row.get('ROOT CAUSE') or ''),
            corrective_action=str(row.get('CORRECTION ACTION') or ''),
            status='Open'
        )
        db.session.add(finding)
        imported += 1

    db.session.commit()
    print(f"✅ Imported {imported} findings")

    return redirect(f"/audit/{audit_id}")

# ======================
# TEMPORARY: Create admin user on startup (REMOVE AFTER FIRST RUN)
# ======================
with app.app_context():
    from models import User
    from extensions import bcrypt
    
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
        new_admin = User(username="admin", password=hashed_pw, role="admin")
        db.session.add(new_admin)
        db.session.commit()
        print("✅ Admin user created on startup!")
    else:
        print(f"Admin user already exists: {admin.username}")
        
    # List all users for debugging
    all_users = User.query.all()
    print(f"Total users in database: {len(all_users)}")
    for u in all_users:
        print(f"  - {u.username} (role: {u.role})")

# ======================
# Blueprints
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
# DB Init
# ======================
with app.app_context():
    db.create_all()

# ======================
# Run
# ======================
if __name__ == "__main__":
    app.run(debug=True)