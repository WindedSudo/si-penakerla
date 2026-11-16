import pytest
from tests.conftest import login, register

# Note: These tests require a running database with seed data applied.

@pytest.mark.skipif(False, reason="Assuming DB is seeded")
def test_login_valid(client):
    """TC-01: Login with valid credentials"""
    response = login(client, 'admin@penakerla.local', 'admin123')
    assert response.status_code == 200
    assert b'Dashboard Admin' in response.data or b'Logout' in response.data

@pytest.mark.skipif(False, reason="Assuming DB is seeded")
def test_login_wrong_password(client):
    """TC-02: Login with wrong password"""
    response = login(client, 'admin@penakerla.local', 'wrongpass')
    assert response.status_code == 200
    assert b'Email atau password salah' in response.data

@pytest.mark.skipif(False, reason="Assuming DB is seeded")
def test_register_valid(client):
    """TC-03: Register new user"""
    # Use a unique email
    import time
    email = f"testuser_{int(time.time())}@example.com"
    response = register(client, 'Test User', email, 'pass123', 'pass123', 'pencari_kerja')
    assert response.status_code == 200
    assert b'Registrasi berhasil' in response.data or b'Login' in response.data

@pytest.mark.skipif(False, reason="Assuming DB is seeded")
def test_register_duplicate_email(client):
    """TC-04: Register with existing email"""
    response = register(client, 'Budi Baru', 'budi@example.com', 'pass123', 'pass123', 'pencari_kerja')
    assert response.status_code == 200
    assert b'Email sudah terdaftar' in response.data

@pytest.mark.skipif(False, reason="Assuming DB is seeded")
def test_pencari_access_admin(client):
    """TC-08: Pencari trying to access admin dashboard"""
    login(client, 'budi@example.com', 'password123')
    response = client.get('/admin/dashboard', follow_redirects=True)
    assert response.status_code == 403 or b'Anda tidak memiliki akses' in response.data
