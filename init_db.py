from app import app, db
from models import User, Operator, Audit, Finding
from extensions import bcrypt

with app.app_context():
    db.create_all()
    print("✅ Tables created successfully!")

    if not User.query.filter_by(username="admin").first():
        hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin = User(username="admin", password=hashed_pw, role="admin")
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created!")

    print("Done!")