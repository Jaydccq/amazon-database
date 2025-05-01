from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
class User(UserMixin):
    def __init__(self, user_id, email, first_name, last_name, address, current_balance, is_seller):
        self.id = user_id
        self.user_id = user_id # Redundant, self.id is used by Flask-Login
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.current_balance = current_balance
        self.is_seller = is_seller

    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
        SELECT password, user_id, email, first_name, last_name, address, current_balance, is_seller
        FROM Accounts
        WHERE email = :email
        """, email=email)

        if not rows:
            app.logger.warning(f"Authentication attempt failed: Email '{email}' not found.")
            return None
        # Ensure check_password_hash is used here, matching generate_password_hash usage
        stored_hash = rows[0][0]
        user_data = rows[0][1:] # user_id, email, first_name, ...
        if not check_password_hash(stored_hash, password):
            app.logger.warning(f"Authentication attempt failed: Incorrect password for email '{email}'.")
            return None
        app.logger.info(f"User '{email}' authenticated successfully.")
        return User(*user_data)

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
        SELECT 1 FROM Accounts WHERE email = :email
        """, email=email)
        return len(rows) > 0

    @staticmethod
    def register(email, password, first_name, last_name, address):
        if User.email_exists(email):
             app.logger.warning(f"Registration attempt failed: Email '{email}' already exists.")
             # Optionally raise an exception or return a specific value
             # raise ValueError("Email already exists")
             return None # Indicate failure due to existing email
        try:
            hashed_password = generate_password_hash(password)
            rows = app.db.execute("""
            INSERT INTO Accounts(email, password, first_name, last_name, address, current_balance, is_seller)
            VALUES (:email, :password, :first_name, :last_name, :address, 0.0, FALSE)
            RETURNING user_id
            """,
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                address=address
            )
            user_id = rows[0][0]
            app.logger.info(f"User '{email}' registered successfully with user_id {user_id}.")
            return User.get(user_id) # Use get method to return a User instance
        except Exception as e:
            app.logger.error(f"Registration failed for email '{email}': {e}", exc_info=True)
            # Reraise the exception or handle it depending on desired behavior
            # raise e # Or return None
            return None

    @staticmethod
    def get(user_id):
        rows = app.db.execute("""
        SELECT user_id, email, first_name, last_name, address, current_balance, is_seller
        FROM Accounts
        WHERE user_id = :user_id
        """, user_id=user_id)
        if rows:
            return User(*rows[0])
        else:
            app.logger.warning(f"User.get failed: No user found with user_id {user_id}.")
            return None

    def check_password(self, password):
        #Checks the provided password against the stored hash.
        rows = app.db.execute("""
            SELECT password FROM Accounts WHERE user_id = :user_id
        """, user_id=self.id)
        if not rows:
            app.logger.error(f"check_password failed: User {self.id} not found in DB during check.")
            return False # User not found (shouldn't happen if called on existing user object)
        stored_hash = rows[0][0]
        return check_password_hash(stored_hash, password)

    @staticmethod
    def make_seller(user_id):
        try:
            app.db.execute("""
                UPDATE Accounts
                SET is_seller = TRUE
                WHERE user_id = :user_id
            """, user_id=user_id)
            app.logger.info(f"User {user_id} successfully updated to seller.")
            return True # Indicate success
        except Exception as e:
            app.logger.error(f"Error updating user {user_id} to seller: {e}", exc_info=True)
            return False # Indicate failure

    @staticmethod
    def update_password(user_id, new_password):
        try:
            # Use generate_password_hash for consistency with registration and login check
            hashed_password = generate_password_hash(new_password)
            rows = app.db.execute("""
                UPDATE Accounts
                SET password = :hashed_password
                WHERE user_id = :user_id
            """, hashed_password=hashed_password, user_id=user_id)
            # Check rows affected if your db driver supports it (e.g., rows.rowcount)
            app.logger.info(f"Password updated successfully for user {user_id}.")
            return True # Indicate success
            # else:
            #     app.logger.warning(f"Password update attempt for user {user_id} did not affect any rows.")
            #     return False
        except Exception as e:
            # Log the error
            app.logger.error(f"Error updating password for user {user_id}: {e}", exc_info=True)
            return False # Indicate failure

    @staticmethod
    def update_profile(user_id, email, first_name, last_name, address):
        """
        Updates the profile information for a given user_id.
        Checks if the email already exists and belongs to a different user.
        """
        try:
            # First, check if the email exists for a different user
            rows = app.db.execute("""
                SELECT user_id FROM Accounts WHERE email = :email AND user_id != :user_id
            """, email=email, user_id=user_id)

            # If the email exists for another user, return False
            if rows:
                app.logger.warning(f"Update profile failed for user {user_id}: Email '{email}' already exists.")
                return False

            # Otherwise, proceed with update
            app.db.execute("""
                UPDATE Accounts
                SET email = :email, first_name = :first_name, last_name = :last_name, address = :address
                WHERE user_id = :user_id
            """, email=email, first_name=first_name, last_name=last_name, address=address, user_id=user_id)

            app.logger.info(f"Profile updated successfully for user {user_id}.")
            return True
        except Exception as e:
            app.logger.error(f"Error updating profile for user {user_id}: {e}", exc_info=True)
            return False

    # Static method to get user by email (needed for update_profile route)
    @staticmethod
    def get_by_email(email):
        rows = app.db.execute("""
            SELECT user_id, email, first_name, last_name, address, current_balance, is_seller
            FROM Accounts
            WHERE email = :email
        """, email=email)
        if rows:
            return User(*rows[0])
        else:
            # It's okay for this to return None if no user is found
            app.logger.debug(f"User.get_by_email: No user found with email '{email}'.")
            return None