from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort, current_app
from flask_login import login_required, current_user
from app.utils.waktu import today_wib
from app.decorators import role_required
from app.db import get_db_connection
from app.models.user import User
from app.models.pencari_kerja import PencariKerja
from app.models.perusahaan import Perusahaan
from app.models.lowongan import Lowongan
from app.models.lamaran import Lamaran
from app.models.penempatan import Penempatan
from app.models.pengalaman import Pengalaman
from app.models.keahlian import Keahlian
from app.models.portofolio import Portofolio
from app.models.lowongan_eksternal import LowonganEksternal
from app.utils.job_scraper import sync_configured_feeds
from app.models.notifikasi import Notifikasi
import csv
import io
from datetime import date, datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    stats = {
        'total_users': len(User.get_all()),
        'total_pencari': User.count_by_role('pencari_kerja'),
        'total_perusahaan': User.count_by_role('perusahaan'),
        'perusahaan_terverifikasi': Perusahaan.count_by_status('terverifikasi'),
        'total_lowongan': Lowongan.count(),
        'lowongan_aktif': Lowongan.count_by_status('aktif'),
        'total_lamaran': Lamaran.count(),
        'lamaran_diterima': Lamaran.count_by_status('diterima'),
        'total_penempatan': Penempatan.count()
    }
    
    # Simulating data for chart
    lamaran_stats = {
        'diajukan': Lamaran.count_by_status('diajukan'),
        'diproses': Lamaran.count_by_status('diproses'),
        'diterima': Lamaran.count_by_status('diterima'),
        'ditolak': Lamaran.count_by_status('ditolak')
    }
    
    return render_template('admin/dashboard.html', stats=stats, lamaran_stats=lamaran_stats)

@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    search = request.args.get('search', '')
    all_users = User.get_all()
    if search:
        all_users = [u for u in all_users if search.lower() in u['nama'].lower() or search.lower() in u['email'].lower()]
    return render_template('admin/users.html', users=all_users, search=search)

@admin_bp.route('/users/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(id):
    if current_user.id == id:
        flash('Tidak dapat menghapus akun sendiri.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        User.delete(id)
        flash('Pengguna berhasil dihapus.', 'success')
    except Exception:
        current_app.logger.exception('Gagal menghapus pengguna')
        flash('Gagal menghapus pengguna.', 'danger')
        
    return redirect(url_for('admin.users'))

@admin_bp.route('/verifikasi')
@login_required
@role_required('admin')
def verifikasi():
    status = request.args.get('status')
    perusahaan_list = Perusahaan.get_all(status=status)
    return render_template('admin/verifikasi.html', perusahaan_list=perusahaan_list, current_status=status)

@admin_bp.route('/verifikasi/<int:id>/<action>', methods=['POST'])
@login_required
@role_required('admin')
def verifikasi_action(id, action):
    if action not in ['terverifikasi', 'ditolak']:
        abort(400)
    
    try:
        Perusahaan.update_status(id, action)
        flash(f'Status perusahaan berhasil diubah menjadi {action}.', 'success')
        
        # Notify perusahaan
        perusahaan = Perusahaan.get_by_id(id)
        if perusahaan:
            if action == 'terverifikasi':
                Notifikasi.create(
                    perusahaan['user_id'],
                    'Akun Terverifikasi ✅',
                    'Selamat! Akun perusahaan Anda telah diverifikasi. Anda sekarang dapat membuat lowongan pekerjaan.',
                    '/perusahaan/lowongan',
                    kategori='verifikasi'
                )
            else:
                Notifikasi.create(
                    perusahaan['user_id'],
                    'Verifikasi Ditolak',
                    'Maaf, verifikasi akun perusahaan Anda ditolak. Silakan periksa kembali data profil Anda.',
                    '/perusahaan/profil',
                    kategori='verifikasi'
                )
    except Exception:
        current_app.logger.exception('Gagal mengubah status verifikasi')
        flash('Gagal mengubah status verifikasi.', 'danger')
        
    return redirect(url_for('admin.verifikasi'))

@admin_bp.route('/lowongan')
@login_required
@role_required('admin')
def lowongan():
    lowongan_list = Lowongan.get_all()
    return render_template('admin/lowongan.html', lowongan_list=lowongan_list)

@admin_bp.route('/lamaran')
@login_required
@role_required('admin')
def lamaran():
    status = request.args.get('status')
    lamaran_list = Lamaran.get_all(status=status)
    return render_template('admin/lamaran.html', lamaran_list=lamaran_list, current_status=status)

@admin_bp.route('/penempatan')
@login_required
@role_required('admin')
def penempatan():
    status = request.args.get('status')
    penempatan_list = Penempatan.get_all(status=status)
    return render_template('admin/penempatan.html', penempatan_list=penempatan_list, current_status=status)

@admin_bp.route('/laporan')
@login_required
@role_required('admin')
def laporan():
    return render_template('admin/laporan.html')

@admin_bp.route('/laporan/export')
@login_required
@role_required('admin')
def laporan_export():
    report_type = request.args.get('type')
    if not report_type:
        flash('Jenis laporan tidak valid', 'danger')
        return redirect(url_for('admin.laporan'))

    si = io.StringIO()
    cw = csv.writer(si)

    filename = f"laporan_{report_type}_{today_wib().strftime('%Y%m%d')}.csv"

    if report_type == 'pengguna':
        data = User.get_all()
        cw.writerow(['ID', 'Nama', 'Email', 'Role', 'Tanggal Daftar'])
        for item in data:
            cw.writerow([item['id'], item['nama'], item['email'], item['role'], item.get('created_at', '')])
            
    elif report_type == 'pencari':
        data = PencariKerja.get_all()
        cw.writerow(['ID', 'NIK', 'Alamat', 'Kecamatan', 'Pendidikan', 'Keterampilan'])
        for item in data:
            cw.writerow([item['id'], item.get('nik', ''), item.get('alamat', ''), item.get('kecamatan', ''), item.get('pendidikan', ''), item.get('keterampilan', '')])
            
    elif report_type == 'perusahaan':
        data = Perusahaan.get_all()
        cw.writerow(['ID', 'Nama Perusahaan', 'Alamat', 'Kecamatan', 'Email', 'Telepon', 'Status Verifikasi'])
        for item in data:
            cw.writerow([item['id'], item.get('nama_perusahaan', ''), item.get('alamat', ''), item.get('kecamatan', ''), item.get('email', ''), item.get('telepon', ''), item.get('status_verifikasi', '')])
            
    elif report_type == 'lowongan':
        data = Lowongan.get_all()
        cw.writerow(['ID', 'Posisi', 'Perusahaan', 'Lokasi', 'Gaji', 'Jumlah Kebutuhan', 'Deadline', 'Status'])
        for item in data:
            cw.writerow([item['id'], item.get('posisi', ''), item.get('nama_perusahaan', ''), item.get('lokasi', ''), item.get('gaji', ''), item.get('jumlah_kebutuhan', ''), item.get('deadline', ''), item.get('status', '')])
            
    elif report_type == 'lamaran':
        data = Lamaran.get_all()
        cw.writerow(['ID', 'Pencari Kerja', 'Posisi', 'Perusahaan', 'Tanggal Lamaran', 'Status'])
        for item in data:
            cw.writerow([item['id'], item.get('nama_pelamar', ''), item.get('posisi', ''), item.get('nama_perusahaan', ''), item.get('tanggal_lamaran', ''), item.get('status', '')])
            
    elif report_type == 'penempatan':
        data = Penempatan.get_all()
        cw.writerow(['ID', 'Pencari Kerja', 'Posisi', 'Perusahaan', 'Tanggal Penempatan', 'Status'])
        for item in data:
            cw.writerow([item['id'], item.get('nama_pelamar', ''), item.get('posisi', ''), item.get('nama_perusahaan', ''), item.get('tanggal_penempatan', ''), item.get('status', '')])
            
    else:
        abort(400)

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@admin_bp.route('/cv/<int:pencari_id>')
@login_required
@role_required('admin')
def lihat_cv(pencari_id):
    pencari = PencariKerja.get_with_user(pencari_id)
    if not pencari:
        flash('Data pencari kerja tidak ditemukan.', 'danger')
        return redirect(url_for('admin.users'))
    
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
                           viewer_role='admin',
                           back_url=request.referrer or url_for('admin.lamaran'))

@admin_bp.route('/lowongan-eksternal')
@login_required
@role_required('admin')
def lowongan_eksternal():
    lowongan_list = LowonganEksternal.search(limit=200)
    return render_template(
        'admin/lowongan_eksternal.html',
        lowongan_list=lowongan_list,
        feed_urls=current_app.config.get('JOB_FEED_URLS', []),
        total_eksternal=LowonganEksternal.count()
    )


@admin_bp.route('/lowongan-eksternal/sinkronisasi', methods=['POST'])
@login_required
@role_required('admin')
def sinkronisasi_lowongan_eksternal():
    feed_urls = current_app.config.get('JOB_FEED_URLS', [])
    if not feed_urls:
        flash('Belum ada feed RSS/Atom. Atur JOB_FEED_URLS di file environment server.', 'warning')
        return redirect(url_for('admin.lowongan_eksternal'))
    try:
        result = sync_configured_feeds(feed_urls)
        imported = result['total']
        failed = [item for item in result['feeds'] if item['error']]
        flash(f'Sinkronisasi selesai. {imported} item lowongan diproses dari {len(result["feeds"])} feed.', 'success')
        for item in failed:
            current_app.logger.warning('Feed lowongan gagal %s: %s', item['url'], item['error'])
        if failed:
            flash(f'{len(failed)} feed gagal diambil. Detail tersedia pada log aplikasi.', 'warning')
    except Exception:
        current_app.logger.exception('Sinkronisasi lowongan eksternal gagal')
        flash('Sinkronisasi gagal. Periksa konfigurasi dan log aplikasi.', 'danger')
    return redirect(url_for('admin.lowongan_eksternal'))

