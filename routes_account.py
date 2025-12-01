# routes_account.py

import os

from dotenv import load_dotenv
import psycopg2
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv(override=True)

# Define Blueprint
account_bp = Blueprint('account_bp', __name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('PGHOST', 'localhost'),
        database=os.environ.get('PGDATABASE', 'your_local_db_name'),
        user=os.environ.get('PGUSER', 'your_local_db_user'),
        password=os.environ.get('PGPASSWORD', 'your_local_db_password'),
        port=os.environ.get('PGPORT', '5432')
    )
    return conn

# --- Mock User ---
def get_current_user_id():
    return 1 # Since login functionality isn't ready, we mock the logged-in user as ID = 1
    # TODO: When merging code, change this to: return session.get("user_id")


@account_bp.route("/account", methods=["GET", "POST"])
def account_page():
    user_id = get_current_user_id()

    # Access Control: Redirect to home if user is not logged in
    if not user_id:
        flash("Please login first.", "warning")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cur = conn.cursor()

    user_info = None

    try:
        if request.method == "POST":
            action = request.form.get("action")

            #  Case A: Update Profile (Email)
            if action == "update_profile":
                new_email = request.form.get("email")

                if not new_email:
                    flash("Email cannot be empty.", "danger")
                else:
                    cur.execute(
                        "SELECT id FROM public.users WHERE email = %s AND id != %s", 
                        (new_email, user_id)
                    )
                    existing_user = cur.fetchone()

                    if existing_user:
                        flash("This email is already registered by another user.", "danger")
                    else:
                        cur.execute(
                            "UPDATE public.users SET email = %s, updated_at = NOW() WHERE id = %s",
                            (new_email, user_id)
                        )
                        conn.commit()
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
                    # 2. Retrieve the current password from the database
                    cur.execute("SELECT password FROM public.users WHERE id = %s", (user_id,))
                    user_record = cur.fetchone()

                    if user_record:
                        stored_password = user_record[0]

                        # 3. Verify current password
                        if check_password_hash(stored_password, current_password):
                            
                            # 4. Update password
                            new_hashed_password = generate_password_hash(new_password)
                            
                            cur.execute(
                                "UPDATE public.users SET password = %s, updated_at = NOW() WHERE id = %s",
                                (new_hashed_password, user_id)
                            )
                            conn.commit()
                            flash("Password updated successfully!", "success")
                        else:
                            flash("Incorrect current password.", "danger")
                    else:
                        flash("User not found.", "danger")

        # Fetch user details from DB to display on Tab 1
        cur.execute("SELECT account, firstname, lastname, email FROM public.users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        
        if row:
            # Organize data into a dictionary for HTML rendering
            user_info = {
                "account": row[0],
                "fullname": f"{row[1]} {row[2]}",
                "email": row[3]
            }

    except Exception as e:
        # Print error if DB connection fails and flash a message
        print("Error:", e)
        flash("Database error occurred.", "danger")
    finally:
        cur.close()
        conn.close()

    # Pass user_info to HTML for rendering
    return render_template("account.html", user=user_info)