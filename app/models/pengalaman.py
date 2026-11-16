from app.db import get_db_connection

class Pengalaman:
    @staticmethod
    def get_by_pencari(pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM pengalaman_kerja WHERE pencari_kerja_id=%s ORDER BY tahun_mulai DESC",
            (pencari_kerja_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pengalaman_kerja WHERE id=%s", (id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    @staticmethod
    def create(pencari_kerja_id, nama_perusahaan, posisi, tahun_mulai, tahun_selesai, deskripsi):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO pengalaman_kerja (pencari_kerja_id, nama_perusahaan, posisi, tahun_mulai, tahun_selesai, deskripsi)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (pencari_kerja_id, nama_perusahaan, posisi, tahun_mulai, tahun_selesai, deskripsi)
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    @staticmethod
    def delete(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pengalaman_kerja WHERE id=%s", (id,))
        conn.commit()
        cursor.close()

    @staticmethod
    def count_by_pencari(pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM pengalaman_kerja WHERE pencari_kerja_id=%s", (pencari_kerja_id,))
        row = cursor.fetchone()
        cursor.close()
        return row['count'] if row else 0
