"""Uji 1 - Ketepatan hasil pencarian (wajib).

Menyiapkan database KHUSUS (default si_penakerla_eval, dibuat ulang tiap dijalankan), mengisi 50 lowongan
sintetis, menjalankan 20 kombinasi pencarian lewat Lowongan.search (kode produksi yang sama dengan halaman web),
lalu membandingkan himpunan ID sistem dengan acuan independen (tests/eval/data_uji1.py).

Jalankan dari folder project:   python -m tests.eval.run_uji1
Keluaran: hasil_uji/uji1_per_query.csv, hasil_uji/uji1_ringkasan.txt
"""
import csv
import os
import sys

import mysql.connector
from dotenv import load_dotenv

from database.setup_db import setup
from tests.eval.data_uji1 import HARI_UJI, LOWONGAN, QUERY, acuan

EVAL_DB = os.environ.get('EVAL_DB_NAME', 'si_penakerla_eval')
KELUARAN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'hasil_uji')


def siapkan_db():
    load_dotenv()
    setup(EVAL_DB, base_seed=False)  # skema kosong
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'), port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'), password=os.environ.get('DB_PASSWORD', ''),
        database=EVAL_DB, charset='utf8mb4')
    cur = conn.cursor()
    cur.execute("INSERT INTO users (id, nama, email, password, role) VALUES (1, 'PT Uji Pencarian', 'uji@example.com', 'x', 'perusahaan')")
    cur.execute("INSERT INTO perusahaan (id, user_id, nama_perusahaan, status_verifikasi) VALUES (1, 1, 'PT Uji Pencarian', 'terverifikasi')")
    for l in LOWONGAN:
        cur.execute(
            "INSERT INTO lowongan (id, perusahaan_id, posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline) "
            "VALUES (%s, 1, %s, 'Lowongan sintetis untuk Uji 1', %s, %s, 3000000, 1, %s, %s)",
            (l['id'], l['posisi'], l['pendidikan'], l['lokasi'], l['status'], l['deadline']))
    conn.commit()
    cur.close()
    conn.close()


def jalankan():
    from app import create_app
    from app.models.lowongan import Lowongan

    siapkan_db()
    app = create_app()
    app.config['DB_NAME'] = EVAL_DB
    baris = []
    with app.app_context():
        for kode, kategori, f in QUERY:
            harapan = acuan(f)
            hasil = {r['id'] for r in Lowongan.search(
                posisi=f.get('posisi'), lokasi=f.get('lokasi'), pendidikan=f.get('pendidikan'),
                status='aktif', hari_ini=HARI_UJI)}
            hilang, salah = sorted(harapan - hasil), sorted(hasil - harapan)
            tp = len(harapan & hasil)
            precision = tp / len(hasil) if hasil else 1.0
            recall = tp / len(harapan) if harapan else 1.0
            baris.append(dict(kode=kode, kategori=kategori, filter=str(f), jumlah_acuan=len(harapan), jumlah_sistem=len(hasil),
                              id_hilang=" ".join(map(str, hilang)), id_salah_masuk=" ".join(map(str, salah)),
                              tepat_seluruhnya=int(not hilang and not salah), precision=round(precision, 3), recall=round(recall, 3)))
    os.makedirs(KELUARAN, exist_ok=True)
    with open(os.path.join(KELUARAN, 'uji1_per_query.csv'), 'w', newline='', encoding='utf8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(baris[0]))
        w.writeheader()
        w.writerows(baris)
    tepat = sum(b['tepat_seluruhnya'] for b in baris)
    ring = [f"Uji 1 - ketepatan hasil pencarian (hari uji {HARI_UJI}, database {EVAL_DB})",
            f"Lowongan sintetis: {len(LOWONGAN)}   Kombinasi pencarian: {len(baris)}",
            f"Query tepat seluruhnya: {tepat}/{len(baris)}",
            f"Total ID hilang: {sum(len(b['id_hilang'].split()) for b in baris)}   "
            f"Total ID salah masuk: {sum(len(b['id_salah_masuk'].split()) for b in baris)}",
            f"Rata-rata precision: {sum(b['precision'] for b in baris) / len(baris):.3f}   "
            f"Rata-rata recall: {sum(b['recall'] for b in baris) / len(baris):.3f}"]
    for kat in ('nol', 'satu', 'banyak'):
        sub = [b for b in baris if b['kategori'] == kat]
        ring.append(f"  kategori {kat:6s}: {sum(b['tepat_seluruhnya'] for b in sub)}/{len(sub)} tepat")
    gagal = [b for b in baris if not b['tepat_seluruhnya']]
    if gagal:
        ring.append("Contoh kegagalan (isi tabel kegagalan di paper):")
        ring += [f"  {b['kode']} {b['filter']}: hilang [{b['id_hilang']}] salah masuk [{b['id_salah_masuk']}]" for b in gagal]
    teks = "\n".join(ring)
    with open(os.path.join(KELUARAN, 'uji1_ringkasan.txt'), 'w', encoding='utf8') as fh:
        fh.write(teks + "\n")
    print(teks)
    return baris


if __name__ == '__main__':
    hasil = jalankan()
    sys.exit(0 if all(b['tepat_seluruhnya'] for b in hasil) else 1)
