"""Pembantu pengujian: menyiapkan lowongan/akun dan menghitung record langsung di database uji."""
import uuid
from datetime import timedelta

from app.utils.waktu import today_wib

# Akun dari database/seed.sql
BUDI = 'budi@example.com'          # pencari_kerja id 1, profil lengkap
SITI = 'siti@example.com'          # pencari_kerja id 2, profil lengkap
PT_JAYA = 'hr@lamongan-jaya.com'   # perusahaan id 1, terverifikasi
PT_MAJU = 'hr@majubersama.com'     # perusahaan id 2, belum diverifikasi
PASSWORD = 'password123'


def buat_lowongan(db, status='aktif', offset_hari=30, perusahaan_id=1, posisi=None):
    """Sisipkan lowongan dengan deadline = hari ini (WIB) + offset_hari. Return (id, posisi)."""
    posisi = posisi or f"Uji {uuid.uuid4().hex[:8]}"
    cur = db.cursor()
    cur.execute(
        "INSERT INTO lowongan (perusahaan_id, posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline) "
        "VALUES (%s, %s, 'Lowongan untuk pengujian', 'SMA/SMK,D3,D4/S1', 'Lamongan', 3000000, 5, %s, %s)",
        (perusahaan_id, posisi, status, today_wib() + timedelta(days=offset_hari)))
    lid = cur.lastrowid
    cur.close()
    return lid, posisi


def jumlah_lamaran(db, lowongan_id, pencari_kerja_id=None):
    cur = db.cursor()
    if pencari_kerja_id:
        cur.execute("SELECT COUNT(*) FROM lamaran WHERE lowongan_id=%s AND pencari_kerja_id=%s", (lowongan_id, pencari_kerja_id))
    else:
        cur.execute("SELECT COUNT(*) FROM lamaran WHERE lowongan_id=%s", (lowongan_id,))
    n = cur.fetchone()[0]
    cur.close()
    return n


def id_lamaran(db, lowongan_id, pencari_kerja_id):
    cur = db.cursor()
    cur.execute("SELECT id FROM lamaran WHERE lowongan_id=%s AND pencari_kerja_id=%s", (lowongan_id, pencari_kerja_id))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def nilai(db, sql, params=()):
    cur = db.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def buat_pencari(db, lengkap=False, nama_depan='Uji'):
    """Buat akun pencari baru (password sama dengan seed). lengkap=False -> tidak ada baris profil."""
    email = f"{nama_depan.lower()}{uuid.uuid4().hex[:8]}@example.com"
    cur = db.cursor()
    cur.execute("INSERT INTO users (nama, email, password, role) SELECT %s, %s, password, 'pencari_kerja' FROM users WHERE email=%s",
                (f"{nama_depan} Uji", email, BUDI))
    uid = cur.lastrowid
    pid = None
    if lengkap:
        cur.execute("INSERT INTO pencari_kerja (user_id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan) "
                    "VALUES (%s, '0000000000000999', '1999-01-01', 'Laki-laki', 'Jl. Uji 1', 'Lamongan', 'D3', 'Ms Office')", (uid,))
        pid = cur.lastrowid
    cur.close()
    return email, uid, pid
