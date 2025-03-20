from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from datetime import datetime 

# Define Blueprint
auth = Blueprint('auth', __name__)

# ---------------- Register User ----------------
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        qualification = request.form.get('qualification')
        dob_str = request.form.get('dob')  # Gets dob as string
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('auth.register'))

        # Convert `dob` string to `datetime.date`
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Please enter a valid date.", "danger")
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            full_name=full_name,
            email=email,
            password=hashed_password,
            qualification=qualification,
            dob=dob,  # Now correctly formatted as a `date` object
            is_admin=False
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# ---------------- Login User ----------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_role'] = 'admin' if user.is_admin else 'user'  # Fix here

            flash("Login successful!", "success")
            return redirect(url_for('main.home'))  # Update with your dashboard route

        flash("Invalid email or password", "danger")

    return render_template('login.html')

# ---------------- Logout ----------------
@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('main.home'))  # Use 'main.home' now
