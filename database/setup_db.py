"""Siapkan database SI-PENAKERLA: buat database, muat skema, data dasar, dan (opsional) data dummy.

Contoh:
  python database/setup_db.py --dummy                 # pakai DB_NAME dari .env
  python database/setup_db.py --db si_penakerla_test  # database lain (mis. untuk pengujian)
PERINGATAN: skema memakai DROP TABLE, semua data pada database tujuan dihapus.
"""
import argparse
import os

import mysql.connector
from dotenv import load_dotenv

FOLDER = os.path.dirname(os.path.abspath(__file__))


def _jalankan_file(cursor, nama_file):
    with open(os.path.join(FOLDER, nama_file), encoding='utf8') as f:
        sql = f.read()
    for _ in cursor.execute(sql, multi=True):
        pass


def setup(db_name=None, dummy=False, base_seed=True):
    load_dotenv()
    db_name = db_name or os.environ.get('DB_NAME', 'si_penakerla')
    if not db_name.replace('_', '').isalnum():
        raise ValueError('Nama database hanya boleh huruf, angka, dan underscore')
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'), port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'), password=os.environ.get('DB_PASSWORD', ''),
        charset='utf8mb4', time_zone='+07:00')
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cur.execute(f"USE `{db_name}`")
    _jalankan_file(cur, 'schema.sql')
    if base_seed:
        _jalankan_file(cur, 'seed.sql')
        if dummy:
            _jalankan_file(cur, 'seed_dummy.sql')
    conn.commit()
    cur.close()
    conn.close()
    return db_name


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', help='nama database (default: DB_NAME di .env)')
    ap.add_argument('--dummy', action='store_true', help='muat juga seed_dummy.sql (data sintetis banyak)')
    ap.add_argument('--schema-only', action='store_true', help='hanya skema, tanpa data apa pun')
    a = ap.parse_args()
    nama = setup(a.db, dummy=a.dummy, base_seed=not a.schema_only)
    print(f"Database '{nama}' siap.")
