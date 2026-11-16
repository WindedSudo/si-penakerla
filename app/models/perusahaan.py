from app.db import get_db_connection

class Perusahaan:
    @staticmethod
    def get_by_user_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM perusahaan WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM perusahaan WHERE id=%s", (id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def create(user_id, nama_perusahaan, alamat, kecamatan, email, telepon):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO perusahaan (user_id, nama_perusahaan, alamat, kecamatan, email, telepon, status_verifikasi)
               VALUES (%s, %s, %s, %s, %s, %s, 'belum_diverifikasi')""",
            (user_id, nama_perusahaan, alamat, kecamatan, email, telepon)
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    @staticmethod
    def update(user_id, nama_perusahaan, alamat, kecamatan, email, telepon):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE perusahaan 
               SET nama_perusahaan=%s, alamat=%s, kecamatan=%s, email=%s, telepon=%s
               WHERE user_id=%s""",
            (nama_perusahaan, alamat, kecamatan, email, telepon, user_id)
        )
        conn.commit()
        cursor.close()

    @staticmethod
    def update_status(id, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE perusahaan SET status_verifikasi=%s WHERE id=%s",
            (status, id)
        )
        conn.commit()
        cursor.close()

    @staticmethod
    def get_all(status=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM perusahaan"
        params = []
        if status:
            query += " WHERE status_verifikasi=%s"
            params.append(status)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def count():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM perusahaan")
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def count_by_status(status):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM perusahaan WHERE status_verifikasi=%s", (status,))
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def get_with_user(perusahaan_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.*, u.nama, u.email as user_email 
            FROM perusahaan p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s
        """
        cursor.execute(query, (perusahaan_id,))
        row = cursor.fetchone()
        cursor.close()
        return row
