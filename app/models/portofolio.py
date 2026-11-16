from app.db import get_db_connection


class Portofolio:
    """Item portofolio proyek/karya milik seorang pencari kerja."""

    @staticmethod
    def get_by_pencari(pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT * FROM portofolio_kerja
               WHERE pencari_kerja_id=%s
               ORDER BY tahun DESC, id DESC""",
            (pencari_kerja_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def create(pencari_kerja_id, judul, deskripsi, tautan, tahun):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO portofolio_kerja
               (pencari_kerja_id, judul, deskripsi, tautan, tahun)
               VALUES (%s, %s, %s, %s, %s)""",
            (pencari_kerja_id, judul, deskripsi, tautan, tahun)
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    @staticmethod
    def delete_for_pencari(portofolio_id, pencari_kerja_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM portofolio_kerja WHERE id=%s AND pencari_kerja_id=%s",
            (portofolio_id, pencari_kerja_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted
