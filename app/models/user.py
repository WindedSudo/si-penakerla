from flask_login import UserMixin
from app.db import get_db_connection
from app.utils.waktu import now_wib
from datetime import datetime

class User(UserMixin):
    def __init__(self, id, nama, email, password, role, created_at):
        self.id = id
        self.nama = nama
        self.email = email
        self.password = password
        self.role = role
        self.created_at = created_at

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return User(row['id'], row['nama'], row['email'], row['password'], row['role'], row['created_at'])
        return None

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return User(row['id'], row['nama'], row['email'], row['password'], row['role'], row['created_at'])
        return None

    @staticmethod
    def create(nama, email, password_hash, role):
        conn = get_db_connection()
        cursor = conn.cursor()
        created_at = now_wib()
        cursor.execute(
            "INSERT INTO users (nama, email, password, role, created_at) VALUES (%s, %s, %s, %s, %s)",
            (nama, email, password_hash, role, created_at)
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def count_by_role(role):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role=%s", (role,))
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def delete(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        cursor.close()
