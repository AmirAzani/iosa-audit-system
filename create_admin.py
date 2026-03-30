from app import app
from extensions import db, bcrypt
from models import User

with app.app_context():
    hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')

    admin = User(
        username="admin",
        password=hashed_pw
    )

    db.session.add(admin)
    db.session.commit()

    print("Admin user created successfully!")