from app.db import get_db_connection
from app.utils.waktu import now_wib

# Kategori notifikasi
KATEGORI = {
    'lamaran': 'Lamaran',
    'lowongan': 'Lowongan',
    'verifikasi': 'Verifikasi',
    'sistem': 'Sistem',
}

def like_escape(text):
    """Escape karakter wildcard LIKE (\\, %, _) pada data dinamis seperti nama user/perusahaan."""
    return (text or '').replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


class Notifikasi:
    @staticmethod
    def get_by_user(user_id, limit=50, kategori=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if kategori:
            cursor.execute(
                "SELECT * FROM notifikasi WHERE user_id=%s AND kategori=%s ORDER BY created_at DESC LIMIT %s",
                (user_id, kategori, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM notifikasi WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
                (user_id, limit)
            )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def count_unread(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(*) as count FROM notifikasi WHERE user_id=%s AND dibaca=FALSE",
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def create(user_id, judul, pesan, link=None, kategori='sistem'):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO notifikasi (user_id, judul, pesan, link, kategori, dibaca, created_at)
               VALUES (%s, %s, %s, %s, %s, FALSE, %s)""",
            (user_id, judul, pesan, link, kategori, now_wib())
        )
        conn.commit()
        cursor.close()

    @staticmethod
    def mark_read(id, user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifikasi SET dibaca=TRUE WHERE id=%s AND user_id=%s",
            (id, user_id)
        )
        conn.commit()
        cursor.close()

    @staticmethod
    def mark_all_read(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifikasi SET dibaca=TRUE WHERE user_id=%s AND dibaca=FALSE",
            (user_id,)
        )
        conn.commit()
        cursor.close()

    @staticmethod
    def delete_by_pattern(user_id, pattern):
        """Hapus notifikasi lama berdasarkan pattern pesan agar tidak dobel/bertentangan."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notifikasi WHERE user_id=%s AND pesan LIKE %s",
            (user_id, pattern)
        )
        conn.commit()
        cursor.close()

    @staticmethod
    def get_latest_unread(user_id):
        """Ambil notifikasi unread terbaru untuk real-time alert/toast."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM notifikasi WHERE user_id=%s AND dibaca=FALSE ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def delete_old(user_id, keep=50):
        """Keep only the latest N notifications per user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """DELETE FROM notifikasi WHERE user_id=%s AND id NOT IN (
                SELECT id FROM (SELECT id FROM notifikasi WHERE user_id=%s ORDER BY created_at DESC LIMIT %s) AS t
            )""",
            (user_id, user_id, keep)
        )
        conn.commit()
        cursor.close()
