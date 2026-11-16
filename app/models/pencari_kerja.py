from app.db import get_db_connection

class PencariKerja:
    @staticmethod
    def get_by_user_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pencari_kerja WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pencari_kerja WHERE id=%s", (id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def create(user_id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan, cv):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO pencari_kerja (user_id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan, cv)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan, cv)
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    @staticmethod
    def update(user_id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan, cv):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE pencari_kerja 
               SET nik=%s, tanggal_lahir=%s, jenis_kelamin=%s, alamat=%s, kecamatan=%s, pendidikan=%s, keterampilan=%s, cv=%s
               WHERE user_id=%s""",
            (nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan, cv, user_id)
        )
        conn.commit()
        cursor.close()

    @staticmethod
    def get_all(kecamatan=None, pendidikan=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM pencari_kerja WHERE 1=1"
        params = []
        if kecamatan:
            query += " AND kecamatan=%s"
            params.append(kecamatan)
        if pendidikan:
            query += " AND pendidikan=%s"
            params.append(pendidikan)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def count():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM pencari_kerja")
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def is_profile_complete(user_id):
        row = PencariKerja.get_by_user_id(user_id)
        if not row:
            return False
        required_fields = ['nik', 'tanggal_lahir', 'jenis_kelamin', 'alamat', 'kecamatan', 'pendidikan']
        for field in required_fields:
            if not row.get(field):
                return False
        return True

    @staticmethod
    def get_with_user(pencari_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT pk.*, u.nama, u.email 
            FROM pencari_kerja pk
            JOIN users u ON pk.user_id = u.id
            WHERE pk.id = %s
        """
        cursor.execute(query, (pencari_id,))
        row = cursor.fetchone()
        cursor.close()
        return row
