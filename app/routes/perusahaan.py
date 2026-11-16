from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.decorators import role_required
from app.db import get_db_connection
from app.models.perusahaan import Perusahaan
from app.models.lowongan import Lowongan
from app.models.lamaran import Lamaran
from app.models.penempatan import Penempatan
from app.models.pencari_kerja import PencariKerja
from app.models.pengalaman import Pengalaman
from app.models.keahlian import Keahlian
from app.models.portofolio import Portofolio
from app.models.notifikasi import Notifikasi, like_escape
from app.models.user import User
from datetime import datetime
from app.utils.referensi import PENDIDIKAN_VALID, simpan_pendidikan, baca_pendidikan
from app.utils.waktu import today_wib

perusahaan_bp = Blueprint('perusahaan', __name__, url_prefix='/perusahaan')

STATUS_LOWONGAN = ('draft', 'aktif', 'ditutup')

@perusahaan_bp.route('/dashboard')
@login_required
@role_required('perusahaan')
def dashboard():
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan:
        flash('Data perusahaan tidak ditemukan. Silakan lengkapi profil.', 'warning')
        return redirect(url_for('perusahaan.profil'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Count total lowongan
    cursor.execute('SELECT COUNT(*) as total FROM lowongan WHERE perusahaan_id = %s', (perusahaan['id'],))
    row = cursor.fetchone()
    total_lowongan = row['total'] if row else 0
    
    # Count lowongan aktif
    cursor.execute("SELECT COUNT(*) as total FROM lowongan WHERE perusahaan_id = %s AND status = 'aktif'", (perusahaan['id'],))
    row = cursor.fetchone()
    lowongan_aktif = row['total'] if row else 0
    
    # Count total pelamar
    cursor.execute('''
        SELECT COUNT(*) as total 
        FROM lamaran l 
        JOIN lowongan lo ON l.lowongan_id = lo.id 
        WHERE lo.perusahaan_id = %s
    ''', (perusahaan['id'],))
    row = cursor.fetchone()
    total_pelamar = row['total'] if row else 0
    
    # Count pelamar by status
    cursor.execute('''
        SELECT l.status, COUNT(*) as total 
        FROM lamaran l 
        JOIN lowongan lo ON l.lowongan_id = lo.id 
        WHERE lo.perusahaan_id = %s AND l.status IN ('diproses', 'diterima')
        GROUP BY l.status
    ''', (perusahaan['id'],))
    status_counts = {row['status']: row['total'] for row in cursor.fetchall()}
    pelamar_diterima = status_counts.get('diterima', 0)
    pelamar_diproses = status_counts.get('diproses', 0)
    
    cursor.close()
    
    return render_template('perusahaan/dashboard.html', 
                           perusahaan=perusahaan,
                           total_lowongan=total_lowongan,
                           lowongan_aktif=lowongan_aktif,
                           total_pelamar=total_pelamar,
                           pelamar_diterima=pelamar_diterima,
                           pelamar_diproses=pelamar_diproses)

@perusahaan_bp.route('/profil', methods=['GET', 'POST'])
@login_required
@role_required('perusahaan')
def profil():
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    
    if request.method == 'POST':
        nama_perusahaan = request.form.get('nama_perusahaan')
        alamat = request.form.get('alamat')
        kecamatan = request.form.get('kecamatan')
        email = request.form.get('email')
        telepon = request.form.get('telepon')
        
        if not nama_perusahaan or not alamat:
            flash('Nama Perusahaan dan Alamat wajib diisi.', 'danger')
        else:
            Perusahaan.update(current_user.id, nama_perusahaan, alamat, kecamatan, email, telepon)
            flash('Profil berhasil diperbarui.', 'success')
            return redirect(url_for('perusahaan.profil'))
            
    kecamatan_options = ['Lamongan', 'Babat', 'Brondong', 'Paciran', 'Sukodadi', 'Pucuk', 'Tikung', 'Sugio', 'Kedungpring', 'Modo', 'Ngimbang', 'Mantup', 'Sambeng', 'Bluluk', 'Solokuro', 'Kalitengah', 'Karanggeneng', 'Turi', 'Karangbinangun', 'Glagah', 'Maduran', 'Laren', 'Sekaran', 'Deket', 'Sukorame', 'Kembangbahu']
    return render_template('perusahaan/profil.html', perusahaan=perusahaan, kecamatan_options=kecamatan_options)


@perusahaan_bp.route('/lowongan')
@login_required
@role_required('perusahaan')
def lowongan_list():
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan:
        flash('Silakan lengkapi profil terlebih dahulu.', 'warning')
        return redirect(url_for('perusahaan.profil'))
        
    if perusahaan['status_verifikasi'] != 'terverifikasi':
        flash('Perusahaan Anda belum diverifikasi. Anda tidak dapat mengelola lowongan saat ini.', 'warning')
        
    lowongan_data = Lowongan.get_by_perusahaan(perusahaan['id'])
    for lowongan in lowongan_data:
        lowongan['jumlah_pelamar'] = Lowongan.count_pelamar(lowongan['id'])
        
    return render_template('perusahaan/lowongan_list.html', lowongan_list=lowongan_data, perusahaan=perusahaan)


@perusahaan_bp.route('/lowongan/tambah', methods=['GET', 'POST'])
@login_required
@role_required('perusahaan')
def lowongan_tambah():
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan or perusahaan['status_verifikasi'] != 'terverifikasi':
        flash('Hanya perusahaan yang terverifikasi yang dapat menambah lowongan.', 'danger')
        return redirect(url_for('perusahaan.lowongan_list'))
        
    if request.method == 'POST':
        posisi = request.form.get('posisi')
        deskripsi = request.form.get('deskripsi')
        pendidikan = simpan_pendidikan(request.form.getlist('pendidikan'))
        lokasi = request.form.get('lokasi')
        gaji = request.form.get('gaji')
        jumlah_kebutuhan = request.form.get('jumlah_kebutuhan')
        status = request.form.get('status', 'draft')
        deadline = request.form.get('deadline')
        
        if status not in STATUS_LOWONGAN:
            status = 'draft'

        if not posisi or not deskripsi or not pendidikan or not lokasi or not jumlah_kebutuhan or not deadline:
            flash('Semua kolom yang wajib harus diisi.', 'danger')
        else:
            try:
                gaji_val = float(gaji) if gaji else None
                jumlah_val = int(jumlah_kebutuhan)
                if jumlah_val <= 0:
                    raise ValueError("Jumlah kebutuhan harus lebih besar dari 0")
                
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                if deadline_date < today_wib():
                    flash('Deadline tidak boleh di masa lalu.', 'danger')
                else:
                    Lowongan.create(perusahaan['id'], posisi, deskripsi, pendidikan, lokasi, gaji_val, jumlah_val, status, deadline_date)
                    flash('Lowongan berhasil ditambahkan.', 'success')
                    
                    # Notify all pencari kerja about new lowongan
                    if status == 'aktif':
                        conn = get_db_connection()
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute("SELECT id FROM users WHERE role='pencari_kerja'")
                        pencari_users = cursor.fetchall()
                        cursor.close()
                        for pu in pencari_users:
                            Notifikasi.create(
                                pu['id'],
                                'Lowongan Baru 🆕',
                                f'{perusahaan["nama_perusahaan"] or current_user.nama} membuka lowongan {posisi} di {lokasi}.',
                                '/pencari/lowongan',
                                kategori='lowongan'
                            )
                    
                    return redirect(url_for('perusahaan.lowongan_list'))
            except ValueError as e:
                flash(str(e) if 'Jumlah' in str(e) else 'Data tidak valid.', 'danger')
                
    pendidikan_options = PENDIDIKAN_VALID
    return render_template('perusahaan/lowongan_form.html', mode='tambah', pendidikan_terpilih=[], pendidikan_options=pendidikan_options, today=today_wib().strftime('%Y-%m-%d'))


@perusahaan_bp.route('/lowongan/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('perusahaan')
def lowongan_edit(id):
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan or perusahaan['status_verifikasi'] != 'terverifikasi':
        flash('Hanya perusahaan yang terverifikasi yang dapat mengedit lowongan.', 'danger')
        return redirect(url_for('perusahaan.lowongan_list'))
        
    lowongan = Lowongan.get_by_id(id)
    if not lowongan or lowongan['perusahaan_id'] != perusahaan['id']:
        abort(404)
        
    if request.method == 'POST':
        posisi = request.form.get('posisi')
        deskripsi = request.form.get('deskripsi')
        pendidikan = simpan_pendidikan(request.form.getlist('pendidikan'))
        lokasi = request.form.get('lokasi')
        gaji = request.form.get('gaji')
        jumlah_kebutuhan = request.form.get('jumlah_kebutuhan')
        status = request.form.get('status')
        deadline = request.form.get('deadline')
        
        if status not in STATUS_LOWONGAN:
            status = lowongan['status']

        if not posisi or not deskripsi or not pendidikan or not lokasi or not jumlah_kebutuhan or not deadline:
            flash('Semua kolom yang wajib harus diisi.', 'danger')
        else:
            try:
                gaji_val = float(gaji) if gaji else None
                jumlah_val = int(jumlah_kebutuhan)
                if jumlah_val <= 0:
                    raise ValueError("Jumlah kebutuhan harus lebih besar dari 0")
                
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                if deadline_date < today_wib() and deadline_date != lowongan['deadline']:
                    flash('Deadline tidak boleh di masa lalu.', 'danger')
                else:
                    Lowongan.update(id, posisi, deskripsi, pendidikan, lokasi, gaji_val, jumlah_val, status, deadline_date)
                    flash('Lowongan berhasil diperbarui.', 'success')
                    return redirect(url_for('perusahaan.lowongan_list'))
            except ValueError as e:
                flash(str(e) if 'Jumlah' in str(e) else 'Data tidak valid.', 'danger')

    pendidikan_options = PENDIDIKAN_VALID
    return render_template('perusahaan/lowongan_form.html', mode='edit', lowongan=lowongan, pendidikan_terpilih=baca_pendidikan(lowongan['pendidikan']), pendidikan_options=pendidikan_options, today=today_wib().strftime('%Y-%m-%d'))


@perusahaan_bp.route('/lowongan/hapus/<int:id>', methods=['POST'])
@login_required
@role_required('perusahaan')
def lowongan_hapus(id):
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan:
        abort(404)
    lowongan = Lowongan.get_by_id(id)
    if not lowongan or lowongan['perusahaan_id'] != perusahaan['id']:
        abort(404)
        
    Lowongan.delete(id)
    flash('Lowongan berhasil dihapus.', 'success')
    return redirect(url_for('perusahaan.lowongan_list'))


@perusahaan_bp.route('/pelamar/<int:lowongan_id>')
@login_required
@role_required('perusahaan')
def pelamar_list(lowongan_id):
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan:
        abort(404)
    lowongan = Lowongan.get_by_id(lowongan_id)
    if not lowongan or lowongan['perusahaan_id'] != perusahaan['id']:
        abort(404)
        
    pelamar_list_data = Lamaran.get_by_lowongan(lowongan_id)
    return render_template('perusahaan/pelamar.html', pelamar_list=pelamar_list_data, lowongan=lowongan)


@perusahaan_bp.route('/pelamar/detail/<int:lamaran_id>')
@login_required
@role_required('perusahaan')
def pelamar_detail(lamaran_id):
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan:
        abort(404)
    lamaran = Lamaran.get_detail(lamaran_id)
    if not lamaran:
        abort(404)
        
    lowongan = Lowongan.get_by_id(lamaran['lowongan_id'])
    if not lowongan or lowongan['perusahaan_id'] != perusahaan['id']:
        abort(404)
        
    penempatan = Penempatan.get_by_lamaran(lamaran_id)
    return render_template('perusahaan/pelamar_detail.html', lamaran=lamaran, lowongan=lowongan, penempatan=penempatan)


@perusahaan_bp.route('/pelamar/status/<int:lamaran_id>', methods=['POST'])
@login_required
@role_required('perusahaan')
def update_status(lamaran_id):
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan:
        abort(404)
    lamaran = Lamaran.get_detail(lamaran_id)
    if not lamaran:
        abort(404)
        
    lowongan = Lowongan.get_by_id(lamaran['lowongan_id'])
    if not lowongan or lowongan['perusahaan_id'] != perusahaan['id']:
        abort(404)
        
    status = request.form.get('status')
    if status in ['diproses', 'diterima', 'ditolak']:
        if status == lamaran['status']:
            flash(f'Status lamaran sudah {status}.', 'info')
            return redirect(url_for('perusahaan.pelamar_detail', lamaran_id=lamaran_id))

        Lamaran.update_status(lamaran_id, status)
        
        if status == 'diterima':
            penempatan = Penempatan.get_by_lamaran(lamaran_id)
            if not penempatan:
                Penempatan.create(lamaran_id, lowongan['posisi'])
        elif status in ['diproses', 'ditolak']:
            penempatan = Penempatan.get_by_lamaran(lamaran_id)
            if penempatan:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM penempatan WHERE lamaran_id=%s", (lamaran_id,))
                conn.commit()
                cur.close()
        
        # Notify pencari kerja (hapus notifikasi status lama untuk posisi & perusahaan ini agar tidak ada notifikasi dobel/kontradiksi)
        pencari = PencariKerja.get_by_id(lamaran['pencari_kerja_id'])
        if pencari:
            nama_pt = perusahaan.get("nama_perusahaan") or "Perusahaan"
            posisi = lowongan["posisi"]
            pattern = f"%posisi {like_escape(posisi)} di {like_escape(nama_pt)}%"
            Notifikasi.delete_by_pattern(pencari['user_id'], pattern)

            status_label = {'diproses': 'sedang diproses', 'diterima': 'DITERIMA ✅', 'ditolak': 'ditolak'}
            Notifikasi.create(
                pencari['user_id'],
                f'Lamaran {status_label.get(status, status)}',
                f'Lamaran Anda untuk posisi {posisi} di {nama_pt} {status_label.get(status, status)}.',
                '/pencari/lamaran',
                kategori='lamaran'
            )
                
        flash('Status lamaran berhasil diperbarui.', 'success')
    else:
        flash('Status tidak valid.', 'danger')
        
    return redirect(url_for('perusahaan.pelamar_detail', lamaran_id=lamaran_id))

@perusahaan_bp.route('/cv/<int:pencari_id>')
@login_required
@role_required('perusahaan')
def lihat_cv(pencari_id):
    perusahaan = Perusahaan.get_by_user_id(current_user.id)
    if not perusahaan or not Lamaran.pencari_melamar_ke_perusahaan(pencari_id, perusahaan['id']):
        abort(404)
    pencari = PencariKerja.get_with_user(pencari_id)
    if not pencari:
        flash('Data pencari kerja tidak ditemukan.', 'danger')
        return redirect(url_for('perusahaan.dashboard'))
    
    user = User.get_by_id(pencari['user_id'])
    pengalaman_list = Pengalaman.get_by_pencari(pencari_id)
    keahlian_list = Keahlian.get_by_pencari(pencari_id)
    portofolio_list = Portofolio.get_by_pencari(pencari_id)
    
    return render_template('shared/cv_view.html',
                           pencari_kerja=pencari,
                           user=user,
                           pengalaman_list=pengalaman_list,
                           keahlian_list=keahlian_list,
                           portofolio_list=portofolio_list,
                           viewer_role='perusahaan',
                           back_url=request.referrer or url_for('perusahaan.lowongan_list'))
