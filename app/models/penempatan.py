from app.db import get_db_connection
from app.utils.waktu import today_wib

class Penempatan:
    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM penempatan WHERE id=%s", (id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def get_by_lamaran(lamaran_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM penempatan WHERE lamaran_id=%s", (lamaran_id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def create(lamaran_id, posisi):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM penempatan WHERE lamaran_id=%s", (lamaran_id,))
        if cursor.fetchone():
            cursor.close()
            return None
            
        cursor.execute(
            """INSERT INTO penempatan (lamaran_id, tanggal_penempatan, posisi, status)
               VALUES (%s, %s, %s, 'aktif')""",
            (lamaran_id, today_wib(), posisi)
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    @staticmethod
    def update_status(id, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE penempatan SET status=%s WHERE id=%s", (status, id))
        conn.commit()
        cursor.close()

    @staticmethod
    def count():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM penempatan")
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def get_all(status=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT pen.*, l.tanggal_lamaran, lw.posisi as posisi_lowongan, 
                   p.nama_perusahaan, u.nama as nama_pelamar
            FROM penempatan pen
            JOIN lamaran l ON pen.lamaran_id = l.id
            JOIN lowongan lw ON l.lowongan_id = lw.id
            JOIN perusahaan p ON lw.perusahaan_id = p.id
            JOIN pencari_kerja pk ON l.pencari_kerja_id = pk.id
            JOIN users u ON pk.user_id = u.id
        """
        params = []
        if status:
            query += " WHERE pen.status=%s"
            params.append(status)
        query += " ORDER BY pen.tanggal_penempatan DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def get_by_pencari(pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT pen.*, p.nama_perusahaan, lw.posisi as posisi_lowongan
            FROM penempatan pen
            JOIN lamaran l ON pen.lamaran_id = l.id
            JOIN lowongan lw ON l.lowongan_id = lw.id
            JOIN perusahaan p ON lw.perusahaan_id = p.id
            WHERE l.pencari_kerja_id = %s
            ORDER BY pen.tanggal_penempatan DESC
        """
        cursor.execute(query, (pencari_kerja_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows
