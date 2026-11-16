"""Uji 3 - Konsistensi alur lamaran (wajib).

Setiap kasus mencatat: kasus, waktu server, status lowongan, respons, jumlah lamaran, lulus/gagal
-> hasil_uji/uji3_log.csv (dibuat otomatis di akhir sesi pytest).
Tenggat berlaku sampai akhir hari tenggat menurut WIB (lihat app/utils/waktu.py).
"""
import threading

from tests.conftest import login
from tests.helpers import (BUDI, SITI, PT_JAYA, PT_MAJU, PASSWORD, buat_lowongan, jumlah_lamaran, id_lamaran,
                           nilai, buat_pencari)


def _lamar(client, lowongan_id):
    return client.post(f'/pencari/lamar/{lowongan_id}', follow_redirects=True)


def test_u3_01_lamar_sekali(client, db, catat):
    lid, _ = buat_lowongan(db)
    login(client, SITI, PASSWORD)
    r = _lamar(client, lid)
    n = jumlah_lamaran(db, lid)
    catat('U3-01 lamar sekali pada lowongan terbuka', 1, n, n, 'aktif', 'Berhasil melamar' if b'Berhasil melamar' in r.data else 'lain')
    assert n == 1 and b'Berhasil melamar' in r.data


def test_u3_02_lamar_dua_kali(client, db, catat):
    lid, _ = buat_lowongan(db)
    login(client, SITI, PASSWORD)
    _lamar(client, lid)
    r = _lamar(client, lid)
    n = jumlah_lamaran(db, lid)
    catat('U3-02 lamar dua kali (berurutan)', 1, n, n, 'aktif', 'Anda sudah melamar' if b'Anda sudah melamar' in r.data else 'lain')
    assert n == 1 and b'Anda sudah melamar' in r.data


def test_u3_03_kirim_ulang_serentak(app, db, catat):
    """Permintaan identik dikirim bersamaan (klik ganda/kirim ulang) -> tetap satu record."""
    lid, _ = buat_lowongan(db)
    jumlah_thread = 8
    klien = []
    for _ in range(jumlah_thread):
        c = app.test_client()
        login(c, SITI, PASSWORD)
        klien.append(c)
    gerbang = threading.Barrier(jumlah_thread)
    kode = []

    def kirim(c):
        gerbang.wait()
        kode.append(c.post(f'/pencari/lamar/{lid}').status_code)

    ts = [threading.Thread(target=kirim, args=(c,)) for c in klien]
    [t.start() for t in ts]
    [t.join() for t in ts]
    n = jumlah_lamaran(db, lid)
    catat(f'U3-03 {jumlah_thread} permintaan serentak', 1, n, n, 'aktif', f'status HTTP {sorted(set(kode))}')
    assert n == 1


def test_u3_04_tenggat_hari_ini_masih_terbuka(client, db, catat):
    lid, _ = buat_lowongan(db, offset_hari=0)
    login(client, SITI, PASSWORD)
    _lamar(client, lid)
    n = jumlah_lamaran(db, lid)
    catat('U3-04 tepat pada hari tenggat (hari ini)', 1, n, n, 'aktif, deadline=hari ini')
    assert n == 1


def test_u3_05_tenggat_kemarin_ditolak(client, db, catat):
    lid, _ = buat_lowongan(db, offset_hari=-1)
    login(client, SITI, PASSWORD)
    r = _lamar(client, lid)
    n = jumlah_lamaran(db, lid)
    catat('U3-05 sehari setelah tenggat', 0, n, n, 'aktif, deadline=kemarin', 'Batas waktu' if b'Batas waktu' in r.data else 'lain')
    assert n == 0 and b'Batas waktu' in r.data


def test_u3_06_lowongan_ditutup_dan_draft(client, db, catat):
    login(client, SITI, PASSWORD)
    for status in ('ditutup', 'draft'):
        lid, _ = buat_lowongan(db, status=status)
        _lamar(client, lid)
        n = jumlah_lamaran(db, lid)
        catat(f'U3-06 lowongan berstatus {status}', 0, n, n, status)
        assert n == 0


def test_u3_07_lowongan_tidak_ada(client, db, catat):
    login(client, SITI, PASSWORD)
    r = _lamar(client, 99999999)
    n = nilai(db, "SELECT COUNT(*) FROM lamaran WHERE lowongan_id=99999999")
    catat('U3-07 lowongan tidak ada', 0, n, n, '-', f'HTTP {r.status_code}')
    assert n == 0


def test_u3_08_profil_belum_ada_atau_kosong(client, db, catat):
    lid, _ = buat_lowongan(db)
    email, uid, _ = buat_pencari(db, lengkap=False)           # tidak ada baris profil
    login(client, email, PASSWORD)
    r = _lamar(client, lid)
    n = jumlah_lamaran(db, lid)
    catat('U3-08a pencari tanpa profil', 0, n, n, 'aktif', 'Profil belum lengkap' if b'belum lengkap' in r.data else 'lain')
    assert n == 0

    email2, uid2, pid2 = buat_pencari(db, lengkap=True)        # profil ada, data wajib dikosongkan
    cur = db.cursor()
    cur.execute("UPDATE pencari_kerja SET alamat=NULL, nik=NULL WHERE id=%s", (pid2,))
    cur.close()
    c2 = client.application.test_client()
    login(c2, email2, PASSWORD)
    _lamar(c2, lid)
    n2 = jumlah_lamaran(db, lid)
    catat('U3-08b profil dengan data wajib kosong (NIK, alamat)', 0, n2, n2, 'aktif')
    assert n2 == 0


def test_u3_09_akun_lain_tidak_bisa_mengakses_lamaran(app, db, catat):
    lid, posisi = buat_lowongan(db, perusahaan_id=1)
    budi = app.test_client()
    login(budi, BUDI, PASSWORD)
    _lamar(budi, lid)
    lam = id_lamaran(db, lid, 1)          # pencari_kerja id 1 = Budi
    assert lam

    # perusahaan lain (id 2) mencoba membuka / mengubah lamaran milik perusahaan 1
    lain = app.test_client()
    login(lain, PT_MAJU, PASSWORD)
    kasus = [
        ('lihat detail pelamar', lain.get(f'/perusahaan/pelamar/detail/{lam}')),
        ('ubah status lamaran', lain.post(f'/perusahaan/pelamar/status/{lam}', data={'status': 'diterima'})),
        ('lihat daftar pelamar lowongan', lain.get(f'/perusahaan/pelamar/{lid}')),
        ('lihat CV pelamar', lain.get('/perusahaan/cv/1')),
        ('hapus lowongan milik lain', lain.post(f'/perusahaan/lowongan/hapus/{lid}')),
    ]
    for nama, resp in kasus:
        catat(f'U3-09 perusahaan lain: {nama}', 404, resp.status_code, jumlah_lamaran(db, lid), 'aktif', f'HTTP {resp.status_code}')
        assert resp.status_code == 404, nama
    status_akhir = nilai(db, "SELECT status FROM lamaran WHERE id=%s", (lam,))
    penempatan = nilai(db, "SELECT COUNT(*) FROM penempatan WHERE lamaran_id=%s", (lam,))
    catat('U3-09 status lamaran & penempatan tidak berubah', 'diajukan/0', f'{status_akhir}/{penempatan}', jumlah_lamaran(db, lid))
    assert status_akhir == 'diajukan' and penempatan == 0
    assert nilai(db, "SELECT COUNT(*) FROM lowongan WHERE id=%s", (lid,)) == 1

    # pencari lain tidak melihat lamaran Budi dan tidak boleh memakai rute perusahaan
    siti = app.test_client()
    login(siti, SITI, PASSWORD)
    halaman = siti.get('/pencari/lamaran')
    catat('U3-09 pencari lain melihat daftar lamarannya sendiri', 'tidak memuat lamaran Budi', 'memuat' if posisi.encode() in halaman.data else 'tidak memuat')
    assert posisi.encode() not in halaman.data
    r = siti.post(f'/perusahaan/pelamar/status/{lam}', data={'status': 'diterima'})
    catat('U3-09 pencari memakai rute perusahaan', 403, r.status_code)
    assert r.status_code == 403


def test_u3_10_status_diterima_membuat_satu_penempatan(app, db, catat):
    lid, _ = buat_lowongan(db, perusahaan_id=1)
    budi = app.test_client()
    login(budi, BUDI, PASSWORD)
    _lamar(budi, lid)
    lam = id_lamaran(db, lid, 1)
    pt = app.test_client()
    login(pt, PT_JAYA, PASSWORD)
    pt.post(f'/perusahaan/pelamar/status/{lam}', data={'status': 'diterima'})
    pt.post(f'/perusahaan/pelamar/status/{lam}', data={'status': 'diterima'})   # kirim ulang
    n1 = nilai(db, "SELECT COUNT(*) FROM penempatan WHERE lamaran_id=%s", (lam,))
    catat('U3-10a diterima dua kali -> satu penempatan', 1, n1, jumlah_lamaran(db, lid))
    pt.post(f'/perusahaan/pelamar/status/{lam}', data={'status': 'ditolak'})
    n2 = nilai(db, "SELECT COUNT(*) FROM penempatan WHERE lamaran_id=%s", (lam,))
    catat('U3-10b diubah ke ditolak -> penempatan dihapus', 0, n2, jumlah_lamaran(db, lid))
    assert n1 == 1 and n2 == 0
