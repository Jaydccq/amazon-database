# app/models/user.py

from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):
    def __init__(self, user_id, email, first_name, last_name, address, current_balance, is_seller):
        self.id = user_id  # Flask-Login 需要的属性
        self.user_id = user_id
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
            return None
        if not check_password_hash(rows[0][0], password):
            return None
        return User(*rows[0][1:])  

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
        SELECT 1 FROM Accounts WHERE email = :email
        """, email=email)
        return len(rows) > 0

    @staticmethod
    def register(email, password, first_name, last_name, address):
        try:
            rows = app.db.execute("""
            INSERT INTO Accounts(email, password, first_name, last_name, address, current_balance, is_seller)
            VALUES (:email, :password, :first_name, :last_name, :address, 0.0, FALSE)
            RETURNING user_id
            """,
                email=email,
                password=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                address=address
            )
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            print(f"Registration failed: {e}")
            return None

    @staticmethod
    def get(user_id):
        rows = app.db.execute("""
        SELECT user_id, email, first_name, last_name, address, current_balance, is_seller
        FROM Accounts
        WHERE user_id = :user_id
        """, user_id=user_id)

        return User(*rows[0]) if rows else None
    
    def top_up(self, amount):
        self.current_balance += amount
        app.db.execute("""
        UPDATE Accounts
        SET current_balance = :balance
        WHERE user_id = :uid
        """, balance=self.current_balance, uid=self.user_id)


