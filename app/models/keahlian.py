from app.db import get_db_connection


class Keahlian:
    """Daftar skill spesifik yang dimiliki pencari kerja."""

    @staticmethod
    def get_by_pencari(pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT * FROM keahlian_pencari
               WHERE pencari_kerja_id=%s
               ORDER BY kategori, nama_skill""",
            (pencari_kerja_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def create(pencari_kerja_id, nama_skill, kategori, tingkat, pengalaman_tahun):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO keahlian_pencari
                   (pencari_kerja_id, nama_skill, kategori, tingkat, pengalaman_tahun)
                   VALUES (%s, %s, %s, %s, %s)""",
                (pencari_kerja_id, nama_skill, kategori, tingkat, pengalaman_tahun)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

    @staticmethod
    def delete_for_pencari(keahlian_id, pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM keahlian_pencari WHERE id=%s AND pencari_kerja_id=%s",
            (keahlian_id, pencari_kerja_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted
