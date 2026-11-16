import pytest
from datetime import timedelta
from app.utils.waktu import today_wib
from tests.conftest import login

# Catatan: test ini membutuhkan database MySQL yang sudah di-seed (database/schema.sql).


def test_create_lowongan(client):
    """TC-05: Buat lowongan dengan data valid (perusahaan terverifikasi)."""
    login(client, 'hr@lamongan-jaya.com', 'password123')
    deadline = (today_wib() + timedelta(days=30)).strftime('%Y-%m-%d')

    response = client.post('/perusahaan/lowongan/tambah', data={
        'posisi': 'Software Engineer (Test)',
        'deskripsi': 'Deskripsi untuk testing',
        'pendidikan': 'D4/S1',
        'lokasi': 'Lamongan',
        'gaji': '5000000',
        'jumlah_kebutuhan': '2',
        'status': 'aktif',
        'deadline': deadline,
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Software Engineer (Test)' in response.data
