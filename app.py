from flask import Flask, redirect, url_for
from extensions import db, login_manager, bcrypt
from flask_migrate import Migrate


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