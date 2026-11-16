import re
import bcrypt
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.db import get_db_connection
from app.models.user import User
from app.models.pencari_kerja import PencariKerja
from app.models.perusahaan import Perusahaan

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'perusahaan':
            return redirect(url_for('perusahaan.dashboard'))
        elif current_user.role == 'pencari_kerja':
            return redirect(url_for('pencari.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'perusahaan':
            return redirect(url_for('perusahaan.dashboard'))
        elif current_user.role == 'pencari_kerja':
            return redirect(url_for('pencari.dashboard'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        
        user = User.get_by_email(email) if email else None
        try:
            password_valid = bool(user) and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))
        except ValueError:
            password_valid = False
        
        if password_valid:
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'perusahaan':
                return redirect(url_for('perusahaan.dashboard'))
            elif user.role == 'pencari_kerja':
                return redirect(url_for('pencari.dashboard'))
        else:
            flash('Email atau password salah.', 'danger')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nama = (request.form.get('nama') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        if not nama or not email or not password or not confirm_password or not role:
            flash('Semua kolom wajib diisi.', 'danger')
            return redirect(url_for('auth.register'))

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash('Format email tidak valid.', 'danger')
            return redirect(url_for('auth.register'))

        if User.get_by_email(email):
            flash('Email sudah terdaftar.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password minimal 6 karakter.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok.', 'danger')
            return redirect(url_for('auth.register'))

        if role not in ['pencari_kerja', 'perusahaan']:
            flash('Role tidak valid.', 'danger')
            return redirect(url_for('auth.register'))

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_id = User.create(nama, email, password_hash, role)

        if role == 'pencari_kerja':
            PencariKerja.create(user_id, None, None, None, None, None, None, None, None)
        elif role == 'perusahaan':
            Perusahaan.create(user_id, None, None, None, None, None)
            # Notify all admins
            from app.models.notifikasi import Notifikasi
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE role='admin'")
            admins = cursor.fetchall()
            cursor.close()
            for admin in admins:
                Notifikasi.create(
                    admin['id'],
                    'Perusahaan Baru Mendaftar',
                    f'{nama} mendaftar sebagai perusahaan dan membutuhkan verifikasi.',
                    '/admin/verifikasi',
                    kategori='verifikasi'
                )

        flash('Registrasi berhasil, silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Berhasil logout', 'success')
    return redirect(url_for('auth.login'))

# ============ NOTIFIKASI ============

from app.models.notifikasi import Notifikasi, KATEGORI

@auth_bp.route('/notifikasi')
@login_required
def notifikasi():
    kategori = request.args.get('kategori')
    if kategori and kategori not in KATEGORI:
        kategori = None
    notif_list = Notifikasi.get_by_user(current_user.id, limit=50, kategori=kategori)
    return render_template('notifikasi.html', 
                           notif_list=notif_list, 
                           current_kategori=kategori,
                           kategori_map=KATEGORI)

@auth_bp.route('/notifikasi/baca/<int:id>')
@login_required
def notifikasi_baca(id):
    notif_list = Notifikasi.get_by_user(current_user.id)
    notif = None
    for n in notif_list:
        if n['id'] == id:
            notif = n
            break
    
    if notif:
        Notifikasi.mark_read(id, current_user.id)
        if notif.get('link'):
            return redirect(notif['link'])
    
    return redirect(url_for('auth.notifikasi'))

@auth_bp.route('/notifikasi/baca-semua', methods=['POST'])
@login_required
def notifikasi_baca_semua():
    Notifikasi.mark_all_read(current_user.id)
    flash('Semua notifikasi ditandai sudah dibaca.', 'success')
    return redirect(url_for('auth.notifikasi'))

@auth_bp.route('/api/notifikasi/status')
@login_required
def api_notifikasi_status():
    unread_count = Notifikasi.count_unread(current_user.id)
    latest = Notifikasi.get_latest_unread(current_user.id)
    return {
        'unread_count': unread_count,
        'latest': {
            'id': latest['id'],
            'judul': latest['judul'],
            'pesan': latest['pesan'],
            'link': latest['link'],
            'kategori': latest.get('kategori', 'sistem')
        } if latest else None
    }

