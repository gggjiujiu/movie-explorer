from flask import (Blueprint, render_template,
                   request, redirect, url_for, session, flash)
import random

from models.users import User
import db

# Define Blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/", methods=["GET"])
def home():
    # If already logged in, redirect directly to the movie search page
    if 'user_id' in session:
        return redirect(url_for('movies.movie_search'))
    return render_template("home.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    user = db.get_user_by_email(email)

    if user and user.check_password(password):
        session['user_id'] = user.id
        return redirect(url_for('movies.movie_search'))
    else:
        flash("Invalid email or password. Please try again.")
        return redirect(url_for('auth.home'))


@auth_bp.route("/signup", methods=["POST"])
def signup():
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email")
    password = request.form.get("password")

    # Check if the email is already registered
    if User.query.filter_by(email=email).first():
        flash("Email already registered! Please log in instead.")
        return redirect(url_for('auth.home'))

    # Automatically generate account name (email prefix + random suffix)
    base_account = email.split('@')[0]
    random_suffix = str(random.randint(1000, 9999))
    generated_account = f"{base_account}_{random_suffix}"

    temp_user = User()
    temp_user.set_password(password)
    hashed_pw = temp_user.password

    new_user = db.create_user(
        firstname,
        lastname,
        email,
        generated_account,
        hashed_pw
    )

    # Log in directly after successful registration
    session['user_id'] = new_user.id
    flash("Account created successfully! Welcome.")
    return redirect(url_for('movies.movie_search'))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('auth.home'))
