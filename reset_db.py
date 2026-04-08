from app import app, db
from sqlalchemy import text

with app.app_context():
    # Disable foreign key checks
    print("Disabling foreign key checks...")
    db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    db.session.commit()
    
    # Drop all tables
    print("Dropping all tables...")
    db.drop_all()
    
    # Recreate all tables
    print("Creating all tables...")
    db.create_all()
    
    # Re-enable foreign key checks
    print("Re-enabling foreign key checks...")
    db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    db.session.commit()
    
    print("✅ Database reset successfully!")