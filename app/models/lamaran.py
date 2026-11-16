import mysql.connector
from app.db import get_db_connection
from app.utils.waktu import today_wib

class Lamaran:
    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lamaran WHERE id=%s", (id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def create(lowongan_id, pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO lamaran (lowongan_id, pencari_kerja_id, tanggal_lamaran, status)
                   VALUES (%s, %s, %s, 'diajukan')""",
                (lowongan_id, pencari_kerja_id, today_wib())
            )
            conn.commit()
            lastrowid = cursor.lastrowid
            return lastrowid
        except mysql.connector.IntegrityError:
            conn.rollback()
            return None
        finally:
            cursor.close()

    @staticmethod
    def create_if_open(lowongan_id, pencari_kerja_id, hari_ini=None):
        """Buat lamaran HANYA jika lowongan masih aktif dan belum lewat tenggat, dalam SATU statement.

        Pengecekan dan insert atomik, jadi tidak ada celah antara "cek" dan "simpan"
        (mis. tenggat lewat tengah malam, atau lowongan ditutup perusahaan di saat yang sama).
        Duplikat dicegah oleh UNIQUE KEY (lowongan_id, pencari_kerja_id).

        Return (hasil, lamaran_id): hasil in {'ok', 'duplikat', 'ditutup'}.
        """
        hari_ini = hari_ini or today_wib()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO lamaran (lowongan_id, pencari_kerja_id, tanggal_lamaran, status)
                   SELECT id, %s, %s, 'diajukan' FROM lowongan
                   WHERE id=%s AND status='aktif' AND deadline >= %s""",
                (pencari_kerja_id, hari_ini, lowongan_id, hari_ini)
            )
            if cursor.rowcount == 0:
                conn.rollback()
                return 'ditutup', None
            conn.commit()
            return 'ok', cursor.lastrowid
        except mysql.connector.IntegrityError:
            conn.rollback()
            return 'duplikat', None
        finally:
            cursor.close()

    @staticmethod
    def get_by_pencari(pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT l.*, lw.posisi, p.nama_perusahaan
            FROM lamaran l
            JOIN lowongan lw ON l.lowongan_id = lw.id
            JOIN perusahaan p ON lw.perusahaan_id = p.id
            WHERE l.pencari_kerja_id = %s
            ORDER BY l.tanggal_lamaran DESC
        """
        cursor.execute(query, (pencari_kerja_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def get_by_lowongan(lowongan_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT l.*, pk.nik, pk.pendidikan, u.nama, u.email
            FROM lamaran l
            JOIN pencari_kerja pk ON l.pencari_kerja_id = pk.id
            JOIN users u ON pk.user_id = u.id
            WHERE l.lowongan_id = %s
            ORDER BY l.tanggal_lamaran DESC
        """
        cursor.execute(query, (lowongan_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def update_status(id, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE lamaran SET status=%s WHERE id=%s", (status, id))
        conn.commit()
        cursor.close()

    @staticmethod
    def check_existing(lowongan_id, pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM lamaran WHERE lowongan_id=%s AND pencari_kerja_id=%s", (lowongan_id, pencari_kerja_id))
        row = cursor.fetchone()
        cursor.close()
        return row is not None

    @staticmethod
    def count():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM lamaran")
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def count_by_status(status):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM lamaran WHERE status=%s", (status,))
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def count_by_pencari_status(pencari_kerja_id, status):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM lamaran WHERE pencari_kerja_id=%s AND status=%s", (pencari_kerja_id, status))
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def get_all(status=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT l.*, lw.posisi, p.nama_perusahaan, u.nama as nama_pelamar
            FROM lamaran l
            JOIN lowongan lw ON l.lowongan_id = lw.id
            JOIN perusahaan p ON lw.perusahaan_id = p.id
            JOIN pencari_kerja pk ON l.pencari_kerja_id = pk.id
            JOIN users u ON pk.user_id = u.id
        """
        params = []
        if status:
            query += " WHERE l.status=%s"
            params.append(status)
        query += " ORDER BY l.tanggal_lamaran DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def get_detail(lamaran_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT l.*, lw.posisi, lw.deskripsi, p.nama_perusahaan, 
                   pk.nik, pk.pendidikan, pk.keterampilan, u.nama, u.email
            FROM lamaran l
            JOIN lowongan lw ON l.lowongan_id = lw.id
            JOIN perusahaan p ON lw.perusahaan_id = p.id
            JOIN pencari_kerja pk ON l.pencari_kerja_id = pk.id
            JOIN users u ON pk.user_id = u.id
            WHERE l.id = %s
        """
        cursor.execute(query, (lamaran_id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def pencari_melamar_ke_perusahaan(pencari_kerja_id, perusahaan_id):
        """True jika pencari kerja pernah melamar ke salah satu lowongan perusahaan tsb."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT 1 FROM lamaran l JOIN lowongan lw ON l.lowongan_id = lw.id
               WHERE l.pencari_kerja_id=%s AND lw.perusahaan_id=%s LIMIT 1""",
            (pencari_kerja_id, perusahaan_id)
        )
        row = cursor.fetchone()
        cursor.close()
        return row is not None
