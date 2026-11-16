from tests.conftest import login
from tests.helpers import BUDI, SITI, PT_JAYA, PASSWORD, buat_lowongan, jumlah_lamaran, id_lamaran, nilai


def test_submit_lamaran(client, db):
    """TC-06: Submit lamaran"""
    lid, _ = buat_lowongan(db)
    login(client, SITI, PASSWORD)
    response = client.post(f'/pencari/lamar/{lid}', follow_redirects=True)
    assert response.status_code == 200
    assert jumlah_lamaran(db, lid, 2) == 1


def test_duplicate_lamaran(client, db):
    """TC-07: Duplicate lamaran"""
    lid, _ = buat_lowongan(db)
    login(client, SITI, PASSWORD)
    client.post(f'/pencari/lamar/{lid}', follow_redirects=True)
    response = client.post(f'/pencari/lamar/{lid}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Anda sudah melamar' in response.data
    assert jumlah_lamaran(db, lid, 2) == 1


def test_update_pelamar_status(app, db):
    """TC-09: Update lamaran status"""
    lid, _ = buat_lowongan(db)
    pencari = app.test_client()
    login(pencari, BUDI, PASSWORD)
    pencari.post(f'/pencari/lamar/{lid}')
    lam = id_lamaran(db, lid, 1)
    pt = app.test_client()
    login(pt, PT_JAYA, PASSWORD)
    response = pt.post(f'/perusahaan/pelamar/status/{lam}', data={'status': 'diproses'}, follow_redirects=True)
    assert response.status_code == 200
    assert nilai(db, "SELECT status FROM lamaran WHERE id=%s", (lam,)) == 'diproses'


def test_accept_candidate(app, db):
    """TC-10: Accept candidate -> penempatan terbentuk"""
    lid, _ = buat_lowongan(db)
    pencari = app.test_client()
    login(pencari, BUDI, PASSWORD)
    pencari.post(f'/pencari/lamar/{lid}')
    lam = id_lamaran(db, lid, 1)
    pt = app.test_client()
    login(pt, PT_JAYA, PASSWORD)
    response = pt.post(f'/perusahaan/pelamar/status/{lam}', data={'status': 'diterima'}, follow_redirects=True)
    assert response.status_code == 200
    assert nilai(db, "SELECT COUNT(*) FROM penempatan WHERE lamaran_id=%s", (lam,)) == 1
