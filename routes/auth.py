from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required
from models import User
from extensions import db, bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        print(f"🔐 Login attempt for username: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"✅ User found in database. Role: {user.role}")
            print(f"Stored hash: {user.password[:20]}...")
            
            if bcrypt.check_password_hash(user.password, password):
                print("✅ Password verified!")
                login_user(user)
                return redirect(url_for("operator.list_operators"))
            else:
                print("❌ Password verification FAILED")
        else:
            print(f"❌ User '{username}' not found in database")
        
        return "Invalid username or password", 200

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))