from app.db import get_db_connection
from app.utils.waktu import today_wib


def _like_escape(text):
    """Escape wildcard LIKE (\\, %, _) agar input pengguna dicocokkan secara harfiah."""
    return (text or '').replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


class Lowongan:
    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lowongan WHERE id=%s", (id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def get_by_perusahaan(perusahaan_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lowongan WHERE perusahaan_id=%s ORDER BY id DESC", (perusahaan_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def create(perusahaan_id, posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO lowongan (perusahaan_id, posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (perusahaan_id, posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline)
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    @staticmethod
    def update(id, posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE lowongan 
               SET posisi=%s, deskripsi=%s, pendidikan=%s, lokasi=%s, gaji=%s, jumlah_kebutuhan=%s, status=%s, deadline=%s
               WHERE id=%s""",
            (posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline, id)
        )
        conn.commit()
        cursor.close()

    @staticmethod
    def delete(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lowongan WHERE id=%s", (id,))
        conn.commit()
        cursor.close()

    @staticmethod
    def search(posisi=None, lokasi=None, pendidikan=None, status=None, perusahaan_id=None,
               sort_by='deadline_asc', hari_ini=None):
        """Cari lowongan. Aturan (acuan Uji 1):

        - Semua filter yang diisi digabung dengan AND.
        - status kosong -> 'aktif'. Lowongan aktif hanya tampil jika deadline >= hari_ini (WIB);
          deadline = hari ini masih terbuka.
        - posisi dan lokasi: cocok jika mengandung teks (tanpa beda huruf besar/kecil), wildcard di-escape.
        - pendidikan: cocok jika jenjang tersebut ADA di daftar jenjang yang diterima lowongan
          (kolom pendidikan berisi CSV kanonik, mis. 'SMA/SMK,D3,D4/S1').
        - Urutan selalu deterministik (ada tie-breaker id).
        """
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        hari_ini = hari_ini or today_wib()
        query = """
            SELECT l.*, p.nama_perusahaan
            FROM lowongan l
            JOIN perusahaan p ON l.perusahaan_id = p.id
            WHERE 1=1
        """
        params = []

        if not status:
            status = 'aktif'
        query += " AND l.status=%s"
        params.append(status)
        if status == 'aktif':
            # Lowongan yang sudah lewat deadline tidak ditampilkan ke pencari kerja
            query += " AND l.deadline >= %s"
            params.append(hari_ini)

        if posisi and posisi.strip():
            query += " AND l.posisi LIKE %s"
            params.append(f"%{_like_escape(posisi.strip())}%")
        if lokasi and lokasi.strip():
            query += " AND l.lokasi LIKE %s"
            params.append(f"%{_like_escape(lokasi.strip())}%")
        if pendidikan:
            query += " AND FIND_IN_SET(%s, REPLACE(l.pendidikan, ' ', '')) > 0"
            params.append(pendidikan)
        if perusahaan_id:
            query += " AND l.perusahaan_id = %s"
            params.append(perusahaan_id)

        if sort_by == 'deadline_asc':
            query += " ORDER BY l.deadline ASC, l.id ASC"
        elif sort_by == 'deadline_desc':
            query += " ORDER BY l.deadline DESC, l.id ASC"
        else:
            query += " ORDER BY l.id DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def count():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM lowongan")
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def count_by_status(status):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM lowongan WHERE status=%s", (status,))
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0

    @staticmethod
    def get_with_perusahaan(id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT l.*, p.nama_perusahaan, p.alamat, p.email as perusahaan_email, p.telepon 
            FROM lowongan l
            JOIN perusahaan p ON l.perusahaan_id = p.id
            WHERE l.id = %s
        """
        cursor.execute(query, (id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT l.*, p.nama_perusahaan 
            FROM lowongan l
            JOIN perusahaan p ON l.perusahaan_id = p.id
            ORDER BY l.id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def count_pelamar(lowongan_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM lamaran WHERE lowongan_id=%s", (lowongan_id,))
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0
