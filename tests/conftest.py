import csv
import os
import threading

# Pengujian SELALU memakai database terpisah (skema dibuat ulang), bukan database kerja.
# Variabel ini harus diset sebelum `app` diimpor karena Config membaca environment saat import.
os.environ['DB_NAME'] = os.environ.get('TEST_DB_NAME', 'si_penakerla_test')
assert os.environ['DB_NAME'].endswith('_test'), "TEST_DB_NAME harus berakhiran _test (skema akan di-DROP)"

import mysql.connector
import pytest

from app import create_app
from app.utils.waktu import now_wib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_UJI3 = []


@pytest.fixture(scope='session', autouse=True)
def database_uji():
    """Buat ulang database uji: skema + data dasar (seed.sql)."""
    from database.setup_db import setup
    setup(os.environ['DB_NAME'], dummy=False)


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def db():
    """Koneksi langsung ke database uji (autocommit) untuk menyiapkan dan memeriksa data."""
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'), port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'), password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ['DB_NAME'], charset='utf8mb4', time_zone='+07:00', autocommit=True)
    yield conn
    conn.close()


@pytest.fixture
def catat():
    """Catat satu kasus Uji 3 ke hasil_uji/uji3_log.csv."""
    def _catat(kasus, diharapkan, aktual, jumlah_lamaran, status_lowongan='', respons=''):
        _LOG_UJI3.append(dict(
            kasus=kasus, waktu_server=now_wib().isoformat(sep=' '), status_lowongan=status_lowongan, respons=respons,
            jumlah_lamaran=jumlah_lamaran, diharapkan=diharapkan, aktual=aktual,
            hasil='lulus' if diharapkan == aktual else 'gagal'))
    return _catat


def pytest_sessionfinish(session, exitstatus):
    if _LOG_UJI3:
        folder = os.path.join(RAIZ, 'hasil_uji')
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, 'uji3_log.csv'), 'w', newline='', encoding='utf8') as fh:
            w = csv.DictWriter(fh, fieldnames=list(_LOG_UJI3[0]))
            w.writeheader()
            w.writerows(_LOG_UJI3)


def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

def register(client, nama, email, password, confirm_password, role):
    return client.post('/register', data={
        'nama': nama, 'email': email, 'password': password,
        'confirm_password': confirm_password, 'role': role
    }, follow_redirects=True)
