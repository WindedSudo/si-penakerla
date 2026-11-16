import hashlib
from app.db import get_db_connection


class LowonganEksternal:
    @staticmethod
    def upsert_many(items):
        if not items:
            return 0
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """INSERT INTO lowongan_eksternal
            (sumber, source_key, source_hash, posisi, perusahaan, deskripsi, lokasi, url_lamaran, tanggal_publikasi, terakhir_diambil)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                posisi=VALUES(posisi), perusahaan=VALUES(perusahaan),
                deskripsi=VALUES(deskripsi), lokasi=VALUES(lokasi),
                url_lamaran=VALUES(url_lamaran),
                tanggal_publikasi=COALESCE(VALUES(tanggal_publikasi), tanggal_publikasi),
                terakhir_diambil=CURRENT_TIMESTAMP"""
        values = [(
            item['sumber'], item['source_key'],
            hashlib.sha256((item['sumber'] + '\n' + item['source_key']).encode('utf-8')).hexdigest(),
            item['posisi'], item.get('perusahaan'), item.get('deskripsi'), item.get('lokasi'),
            item['url_lamaran'], item.get('tanggal_publikasi')
        ) for item in items]
        cursor.executemany(query, values)
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        return affected

    @staticmethod
    def search(keyword=None, lokasi=None, limit=100):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM lowongan_eksternal WHERE 1=1"
        params = []
        if keyword and keyword.strip():
            term = f"%{keyword.strip()}%"
            query += " AND (posisi LIKE %s OR perusahaan LIKE %s OR deskripsi LIKE %s)"
            params.extend([term, term, term])
        if lokasi and lokasi.strip():
            query += " AND lokasi LIKE %s"
            params.append(f"%{lokasi.strip()}%")
        query += " ORDER BY COALESCE(tanggal_publikasi, terakhir_diambil) DESC, id DESC LIMIT %s"
        params.append(max(1, min(int(limit), 300)))
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def count():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS jumlah FROM lowongan_eksternal")
        row = cursor.fetchone()
        cursor.close()
        return row['jumlah'] if row else 0
