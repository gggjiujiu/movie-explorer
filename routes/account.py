from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from db import (
    get_user,
    email_exists,
    update_user_email,
    update_user_password
)

# Define Blueprint
account_bp = Blueprint('account_bp', __name__)

def get_current_user_id():
    return session.get("user_id")


@account_bp.route("/account", methods=["GET", "POST"])
def account_page():
    user_id = get_current_user_id()

    # Access Control: Redirect to home if user is not logged in
    if not user_id:
        flash("Please login first.", "warning")
        return redirect(url_for("home"))

    user_info = None

    try:
        user = get_user(user_id)
        
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("home"))

        if request.method == "POST":
            action = request.form.get("action")

            #  Case A: Update Profile (Email)
            if action == "update_profile":
                new_email = request.form.get("email")

                if not new_email:
                    flash("Email cannot be empty.", "danger")
                elif email_exists(new_email, user_id):
                    flash("This email is already registered by another user.", "danger")

                else:
                    update_user_email(user, new_email)
                    flash("Profile updated successfully!", "success")
            

            #  Case B: Change Password
            elif action == "change_password":
                current_password = request.form.get("current_password")
                new_password = request.form.get("new_password")
                confirm_password = request.form.get("confirm_password")

                # 1. Check if the two new passwords match
                if new_password != confirm_password:
                    flash("New passwords do not match!", "danger")
                else:
                    if check_password_hash(user.password, current_password):

                        hashed_pw = generate_password_hash(new_password)
                        update_user_password(user, hashed_pw)

                        flash("Password updated successfully!", "success")
                    else:
                        flash("Incorrect current password.", "danger")

        user_info = {
            "account": user.account,
            "fullname": f"{user.firstname} {user.lastname}",
            "email": user.email
        }

    except Exception as e:
        # Print error if DB connection fails and flash a message
        print("Error:", e)
        flash("Database error occurred.", "danger")

    # Pass user_info to HTML for rendering
    return render_template("account.html", user=user_info)