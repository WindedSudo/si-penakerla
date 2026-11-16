import os
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.decorators import role_required
from app.db import get_db_connection
from app.models.pencari_kerja import PencariKerja
from app.models.lowongan import Lowongan
from app.models.lamaran import Lamaran
from app.models.penempatan import Penempatan
from app.models.pengalaman import Pengalaman
from app.models.keahlian import Keahlian
from app.models.portofolio import Portofolio
from app.models.lowongan_eksternal import LowonganEksternal
from app.models.perusahaan import Perusahaan
from app.models.notifikasi import Notifikasi, like_escape
from app.utils.matching import get_matched_lowongan, calculate_match_score, explain_match
from app.utils.chatbot import generate_reply
from app.utils.referensi import PENDIDIKAN_VALID, KECAMATAN_LAMONGAN
from app.utils.waktu import today_wib, tenggat_terlewati
import re
import uuid
import math
from datetime import datetime
from urllib.parse import urlparse

pencari_bp = Blueprint('pencari', __name__, url_prefix='/pencari')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@pencari_bp.route('/dashboard')
@login_required
@role_required('pencari_kerja')
def dashboard():
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    profile_complete = PencariKerja.is_profile_complete(current_user.id)
    
    total_lamaran = 0
    diproses = 0
    diterima = 0
    ditolak = 0
    recent_lamaran = []
    
    if pencari_kerja:
        all_lamaran = Lamaran.get_by_pencari(pencari_kerja['id'])
        total_lamaran = len(all_lamaran) if all_lamaran else 0
        diproses = Lamaran.count_by_pencari_status(pencari_kerja['id'], 'diproses')
        diterima = Lamaran.count_by_pencari_status(pencari_kerja['id'], 'diterima')
        ditolak = Lamaran.count_by_pencari_status(pencari_kerja['id'], 'ditolak')
        
        if all_lamaran:
            recent_lamaran = all_lamaran[:5]
            
    recent_lowongan = Lowongan.search()
    if recent_lowongan:
        recent_lowongan = recent_lowongan[:5]
        
    return render_template('pencari/dashboard.html',
                           pencari_kerja=pencari_kerja,
                           profile_complete=profile_complete,
                           total_lamaran=total_lamaran,
                           diproses=diproses,
                           diterima=diterima,
                           ditolak=ditolak,
                           recent_lowongan=recent_lowongan,
                           recent_lamaran=recent_lamaran)

@pencari_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('pencari_kerja')
def profile():
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    kecamatan_options = KECAMATAN_LAMONGAN
    pendidikan_options = PENDIDIKAN_VALID

    if request.method == 'POST':
        # String kosong harus menjadi NULL agar kolom DATE/ENUM tidak error di MySQL strict mode
        nik = (request.form.get('nik') or '').strip() or None
        tanggal_lahir = (request.form.get('tanggal_lahir') or '').strip() or None
        jenis_kelamin = request.form.get('jenis_kelamin') or None
        alamat = (request.form.get('alamat') or '').strip() or None
        kecamatan = request.form.get('kecamatan') or None
        pendidikan = request.form.get('pendidikan') or None
        keterampilan = (request.form.get('keterampilan') or '').strip() or None

        if nik and not re.fullmatch(r'\d{16}', nik):
            flash('NIK harus terdiri dari 16 digit angka.', 'danger')
            return redirect(url_for('pencari.profile'))
        if tanggal_lahir:
            try:
                if datetime.strptime(tanggal_lahir, '%Y-%m-%d').date() >= today_wib():
                    raise ValueError
            except ValueError:
                flash('Tanggal lahir tidak valid.', 'danger')
                return redirect(url_for('pencari.profile'))
        if jenis_kelamin not in (None, 'Laki-laki', 'Perempuan'):
            flash('Jenis kelamin tidak valid.', 'danger')
            return redirect(url_for('pencari.profile'))
        if kecamatan not in (None, *kecamatan_options) or pendidikan not in (None, *PENDIDIKAN_VALID):
            flash('Kecamatan atau pendidikan tidak valid.', 'danger')
            return redirect(url_for('pencari.profile'))
        
        cv_filename = pencari_kerja['cv'] if pencari_kerja else None
        
        if 'cv' in request.files:
            file = request.files['cv']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    # Ekstensi diambil dari nama asli; secure_filename bisa menghilangkannya
                    # untuk nama non-ASCII (mis. "cv saya.pdf" -> aman, "投稿.pdf" -> "pdf").
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    base = secure_filename(file.filename.rsplit('.', 1)[0]) or 'cv'
                    filename = f"{uuid.uuid4().hex}_{base}.{ext}"
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    cv_filename = filename
                else:
                    flash('Format file CV tidak didukung. Gunakan PDF, DOC, atau DOCX.', 'danger')
                    return redirect(url_for('pencari.profile'))

        if pencari_kerja:
            PencariKerja.update(current_user.id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan, cv_filename)
            flash('Profil berhasil diperbarui.', 'success')
        else:
            PencariKerja.create(current_user.id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan, cv_filename)
            flash('Profil berhasil disimpan.', 'success')
            
        return redirect(url_for('pencari.profile'))

    return render_template('pencari/profile.html', 
                           pencari_kerja=pencari_kerja,
                           kecamatan_options=kecamatan_options,
                           pendidikan_options=pendidikan_options)

@pencari_bp.route('/lowongan')
@login_required
@role_required('pencari_kerja')
def lowongan():
    posisi = request.args.get('posisi')
    lokasi = request.args.get('lokasi')
    pendidikan = request.args.get('pendidikan')
    sort_by = request.args.get('sort_by', 'deadline_asc')
    
    posisi_val = posisi if posisi else None
    lokasi_val = lokasi if lokasi else None
    pendidikan_val = pendidikan if pendidikan and pendidikan != 'Semua' else None
    
    lowongan_list = Lowongan.search(
        posisi=posisi_val, 
        lokasi=lokasi_val, 
        pendidikan=pendidikan_val, 
        status='aktif',
        sort_by=sort_by if sort_by != 'match' else 'deadline_asc'
    )
    
    # Add match scores
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    keahlian_list = Keahlian.get_by_pencari(pencari_kerja['id']) if pencari_kerja else []
    pengalaman_list = Pengalaman.get_by_pencari(pencari_kerja['id']) if pencari_kerja else []
    if pencari_kerja and lowongan_list:
        lowongan_list = get_matched_lowongan(pencari_kerja, lowongan_list, keahlian_list, pengalaman_list)
        if sort_by == 'match':
            lowongan_list.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    pendidikan_options = PENDIDIKAN_VALID
    
    return render_template('pencari/lowongan.html',
                           lowongan_list=lowongan_list,
                           posisi=posisi,
                           lokasi=lokasi,
                           pendidikan=pendidikan,
                           sort_by=sort_by,
                           pendidikan_options=pendidikan_options,
                           keahlian_list=keahlian_list)

@pencari_bp.route('/lowongan/<int:id>')
@login_required
@role_required('pencari_kerja')
def lowongan_detail(id):
    lowongan = Lowongan.get_with_perusahaan(id)
    if not lowongan or lowongan['status'] == 'draft':
        flash('Lowongan tidak ditemukan.', 'danger')
        return redirect(url_for('pencari.lowongan'))
        
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    is_applied = False
    
    if pencari_kerja:
        is_applied = Lamaran.check_existing(id, pencari_kerja['id'])
        
    jumlah_pelamar = Lowongan.count_pelamar(id)
    
    deadline_passed = tenggat_terlewati(lowongan['deadline'])
        
    profile_complete = PencariKerja.is_profile_complete(current_user.id)
    has_cv = bool(pencari_kerja and (pencari_kerja.get('cv') or profile_complete))
    
    # Calculate match score
    match_breakdown = {'total': 0, 'reasons': []}
    if pencari_kerja:
        skill_list = Keahlian.get_by_pencari(pencari_kerja['id'])
        experience_list = Pengalaman.get_by_pencari(pencari_kerja['id'])
        match_breakdown = explain_match(pencari_kerja, lowongan, skill_list, experience_list)
    match_score = match_breakdown['total']
    
    return render_template('pencari/lowongan_detail.html',
                           lowongan=lowongan,
                           is_applied=is_applied,
                           jumlah_pelamar=jumlah_pelamar,
                           deadline_passed=deadline_passed,
                           profile_complete=profile_complete,
                           has_cv=has_cv,
                           match_score=match_score,
                           match_breakdown=match_breakdown)

@pencari_bp.route('/lamar/<int:lowongan_id>', methods=['POST'])
@login_required
@role_required('pencari_kerja')
def lamar(lowongan_id):
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    
    if not PencariKerja.is_profile_complete(current_user.id):
        flash('Profil Anda belum lengkap. Silakan lengkapi profil Anda terlebih dahulu.', 'warning')
        return redirect(url_for('pencari.lowongan_detail', id=lowongan_id))
        
    lowongan = Lowongan.get_with_perusahaan(lowongan_id)
    if not lowongan or lowongan['status'] != 'aktif':
        flash('Lowongan tidak tersedia atau sudah ditutup.', 'danger')
        return redirect(url_for('pencari.lowongan'))
        
    if tenggat_terlewati(lowongan['deadline']):
        flash('Batas waktu pendaftaran untuk lowongan ini telah lewat.', 'danger')
        return redirect(url_for('pencari.lowongan_detail', id=lowongan_id))

    try:
        # Cek status/tenggat + simpan dilakukan atomik di satu statement; duplikat ditolak oleh UNIQUE KEY.
        hasil, lamaran_id = Lamaran.create_if_open(lowongan_id, pencari_kerja['id'])
        if hasil == 'duplikat':
            flash('Anda sudah melamar lowongan ini.', 'info')
            return redirect(url_for('pencari.lowongan_detail', id=lowongan_id))
        if hasil == 'ditutup':
            flash('Lowongan tidak tersedia, sudah ditutup, atau batas waktunya telah lewat.', 'danger')
            return redirect(url_for('pencari.lowongan_detail', id=lowongan_id))
        flash('Berhasil melamar lowongan pekerjaan.', 'success')
        
        # Notify perusahaan (hapus notif pelamar yang identik jika ada)
        perusahaan = Perusahaan.get_by_id(lowongan['perusahaan_id']) if lowongan.get('perusahaan_id') else None
        if perusahaan:
            pattern = f"%{like_escape(current_user.nama)} melamar posisi {like_escape(lowongan['posisi'])}%"
            Notifikasi.delete_by_pattern(perusahaan['user_id'], pattern)
            Notifikasi.create(
                perusahaan['user_id'],
                'Pelamar Baru',
                f'{current_user.nama} melamar posisi {lowongan["posisi"]}.',
                f'/perusahaan/pelamar/{lowongan_id}',
                kategori='lamaran'
            )
    except Exception:
        current_app.logger.exception('Gagal memproses lamaran')
        flash('Terjadi kesalahan saat melamar. Silakan coba lagi.', 'danger')
        
    return redirect(url_for('pencari.lowongan_detail', id=lowongan_id))

@pencari_bp.route('/lamaran')
@login_required
@role_required('pencari_kerja')
def lamaran():
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    if not pencari_kerja:
        flash('Silakan lengkapi profil Anda terlebih dahulu.', 'warning')
        return redirect(url_for('pencari.profile'))
        
    lamaran_list = Lamaran.get_by_pencari(pencari_kerja['id'])
    penempatan_list = Penempatan.get_by_pencari(pencari_kerja['id'])
    
    return render_template('pencari/lamaran.html',
                           lamaran_list=lamaran_list,
                           penempatan_list=penempatan_list)

# ============ CV BUILDER ============

@pencari_bp.route('/cv-builder')
@login_required
@role_required('pencari_kerja')
def cv_builder():
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    profile_complete = PencariKerja.is_profile_complete(current_user.id)
    pengalaman_list = []
    keahlian_list = []
    portofolio_list = []
    if pencari_kerja:
        pengalaman_list = Pengalaman.get_by_pencari(pencari_kerja['id'])
        keahlian_list = Keahlian.get_by_pencari(pencari_kerja['id'])
        portofolio_list = Portofolio.get_by_pencari(pencari_kerja['id'])
    
    return render_template('pencari/cv_builder.html',
                           pencari_kerja=pencari_kerja,
                           profile_complete=profile_complete,
                           pengalaman_list=pengalaman_list,
                           keahlian_list=keahlian_list,
                           portofolio_list=portofolio_list)

@pencari_bp.route('/cv-preview')
@login_required
@role_required('pencari_kerja')
def cv_preview():
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    if not pencari_kerja:
        flash('Silakan lengkapi profil terlebih dahulu.', 'warning')
        return redirect(url_for('pencari.profile'))
    
    pengalaman_list = Pengalaman.get_by_pencari(pencari_kerja['id'])
    keahlian_list = Keahlian.get_by_pencari(pencari_kerja['id'])
    portofolio_list = Portofolio.get_by_pencari(pencari_kerja['id'])
    
    return render_template('pencari/cv_preview.html',
                           pencari_kerja=pencari_kerja,
                           pengalaman_list=pengalaman_list,
                           keahlian_list=keahlian_list,
                           portofolio_list=portofolio_list)

@pencari_bp.route('/pengalaman/tambah', methods=['POST'])
@login_required
@role_required('pencari_kerja')
def pengalaman_tambah():
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    if not pencari_kerja:
        flash('Silakan lengkapi profil terlebih dahulu.', 'warning')
        return redirect(url_for('pencari.profile'))
    
    nama_perusahaan = request.form.get('nama_perusahaan')
    posisi = request.form.get('posisi')
    tahun_mulai = request.form.get('tahun_mulai')
    tahun_selesai = request.form.get('tahun_selesai') or None
    deskripsi = request.form.get('deskripsi')
    
    if not nama_perusahaan or not posisi or not tahun_mulai:
        flash('Nama perusahaan, posisi, dan tahun mulai wajib diisi.', 'danger')
        return redirect(url_for('pencari.cv_builder'))
    
    try:
        Pengalaman.create(pencari_kerja['id'], nama_perusahaan, posisi, int(tahun_mulai), 
                         int(tahun_selesai) if tahun_selesai else None, deskripsi)
        flash('Pengalaman kerja berhasil ditambahkan.', 'success')
    except Exception:
        current_app.logger.exception('Gagal menambah pengalaman')
        flash('Gagal menambahkan pengalaman. Periksa kembali data yang diisi.', 'danger')
    
    return redirect(url_for('pencari.cv_builder'))

@pencari_bp.route('/pengalaman/hapus/<int:id>', methods=['POST'])
@login_required
@role_required('pencari_kerja')
def pengalaman_hapus(id):
    pencari_kerja = PencariKerja.get_by_user_id(current_user.id)
    if not pencari_kerja:
        return redirect(url_for('pencari.profile'))
    
    # Verify ownership
    pengalaman = Pengalaman.get_by_id(id)
    if pengalaman and pengalaman['pencari_kerja_id'] == pencari_kerja['id']:
        Pengalaman.delete(id)
        flash('Pengalaman kerja berhasil dihapus.', 'success')
    else:
        flash('Pengalaman kerja tidak ditemukan.', 'danger')
    
    return redirect(url_for('pencari.cv_builder'))

# ============ KEAHLIAN, PORTOFOLIO, ASISTEN KARIER & LOWONGAN EKSTERNAL ============

@pencari_bp.route('/pengembangan')
@login_required
@role_required('pencari_kerja')
def pengembangan():
    pencari = PencariKerja.get_by_user_id(current_user.id)
    if not pencari:
        flash('Lengkapi profil dasar terlebih dahulu.', 'warning')
        return redirect(url_for('pencari.profile'))
    return render_template(
        'pencari/pengembangan.html',
        keahlian_list=Keahlian.get_by_pencari(pencari['id']),
        portofolio_list=Portofolio.get_by_pencari(pencari['id']),
        tahun_sekarang=today_wib().year,
        tingkat_options=['Pemula', 'Menengah', 'Mahir', 'Ahli']
    )


@pencari_bp.route('/skill/tambah', methods=['POST'])
@login_required
@role_required('pencari_kerja')
def skill_tambah():
    pencari = PencariKerja.get_by_user_id(current_user.id)
    if not pencari:
        flash('Lengkapi profil dasar terlebih dahulu.', 'warning')
        return redirect(url_for('pencari.profile'))

    nama = (request.form.get('nama_skill') or '').strip()
    kategori = (request.form.get('kategori') or '').strip() or None
    tingkat = request.form.get('tingkat') or 'Menengah'
    pengalaman_raw = (request.form.get('pengalaman_tahun') or '0').strip()
    if not nama or len(nama) > 100 or tingkat not in ['Pemula', 'Menengah', 'Mahir', 'Ahli']:
        flash('Nama skill atau tingkat penguasaan tidak valid.', 'danger')
        return redirect(url_for('pencari.pengembangan'))
    if kategori and len(kategori) > 60:
        flash('Kategori skill maksimal 60 karakter.', 'danger')
        return redirect(url_for('pencari.pengembangan'))
    try:
        pengalaman_tahun = float(pengalaman_raw)
        if not math.isfinite(pengalaman_tahun) or pengalaman_tahun < 0 or pengalaman_tahun > 60:
            raise ValueError
        Keahlian.create(pencari['id'], nama, kategori, tingkat, pengalaman_tahun)
        flash('Keahlian berhasil ditambahkan.', 'success')
    except ValueError:
        flash('Lama pengalaman harus berupa angka antara 0 sampai 60 tahun.', 'danger')
    except Exception:
        current_app.logger.exception('Gagal menambahkan skill pencari kerja')
        flash('Skill sudah terdaftar atau gagal disimpan.', 'warning')
    return redirect(url_for('pencari.pengembangan'))


@pencari_bp.route('/skill/hapus/<int:skill_id>', methods=['POST'])
@login_required
@role_required('pencari_kerja')
def skill_hapus(skill_id):
    pencari = PencariKerja.get_by_user_id(current_user.id)
    if not pencari or not Keahlian.delete_for_pencari(skill_id, pencari['id']):
        flash('Keahlian tidak ditemukan.', 'warning')
    else:
        flash('Keahlian berhasil dihapus.', 'success')
    return redirect(url_for('pencari.pengembangan'))


@pencari_bp.route('/portofolio/tambah', methods=['POST'])
@login_required
@role_required('pencari_kerja')
def portofolio_tambah():
    pencari = PencariKerja.get_by_user_id(current_user.id)
    if not pencari:
        flash('Lengkapi profil dasar terlebih dahulu.', 'warning')
        return redirect(url_for('pencari.profile'))

    judul = (request.form.get('judul') or '').strip()
    deskripsi = (request.form.get('deskripsi') or '').strip() or None
    tautan = (request.form.get('tautan') or '').strip() or None
    tahun_raw = (request.form.get('tahun') or '').strip()
    if not judul or len(judul) > 150:
        flash('Judul portofolio wajib diisi (maksimal 150 karakter).', 'danger')
        return redirect(url_for('pencari.pengembangan'))
    if deskripsi and len(deskripsi) > 10000:
        flash('Deskripsi portofolio maksimal 10.000 karakter.', 'danger')
        return redirect(url_for('pencari.pengembangan'))
    if tautan:
        parsed = urlparse(tautan)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username or parsed.password):
            flash('Tautan portofolio harus berupa URL HTTP/HTTPS yang valid tanpa kredensial.', 'danger')
            return redirect(url_for('pencari.pengembangan'))
        if len(tautan) > 500:
            flash('Tautan portofolio terlalu panjang.', 'danger')
            return redirect(url_for('pencari.pengembangan'))
    try:
        tahun = int(tahun_raw) if tahun_raw else None
        if tahun is not None and (tahun < 1950 or tahun > today_wib().year + 1):
            raise ValueError
        Portofolio.create(pencari['id'], judul, deskripsi, tautan, tahun)
        flash('Portofolio berhasil ditambahkan.', 'success')
    except ValueError:
        flash('Tahun portofolio tidak valid.', 'danger')
    except Exception:
        current_app.logger.exception('Gagal menambahkan portofolio')
        flash('Portofolio gagal disimpan.', 'danger')
    return redirect(url_for('pencari.pengembangan'))


@pencari_bp.route('/portofolio/hapus/<int:portofolio_id>', methods=['POST'])
@login_required
@role_required('pencari_kerja')
def portofolio_hapus(portofolio_id):
    pencari = PencariKerja.get_by_user_id(current_user.id)
    if not pencari or not Portofolio.delete_for_pencari(portofolio_id, pencari['id']):
        flash('Portofolio tidak ditemukan.', 'warning')
    else:
        flash('Portofolio berhasil dihapus.', 'success')
    return redirect(url_for('pencari.pengembangan'))


@pencari_bp.route('/asisten-karier')
@login_required
@role_required('pencari_kerja')
def asisten_karier():
    return render_template('pencari/asisten_karier.html')


@pencari_bp.route('/api/asisten-karier', methods=['POST'])
@login_required
@role_required('pencari_kerja')
def api_asisten_karier():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'error': 'Format pesan tidak valid.'}), 400
    raw_message = payload.get('message')
    if not isinstance(raw_message, str):
        return jsonify({'error': 'Pesan harus berupa teks.'}), 400
    message = raw_message.strip()
    if not message:
        return jsonify({'error': 'Pesan tidak boleh kosong.'}), 400
    if len(message) > 1000:
        return jsonify({'error': 'Pesan maksimal 1.000 karakter.'}), 400

    pencari = PencariKerja.get_by_user_id(current_user.id)
    profile = {}
    if pencari:
        profile = {
            'pendidikan': pencari.get('pendidikan'),
            'kecamatan': pencari.get('kecamatan'),
            'keahlian': Keahlian.get_by_pencari(pencari['id']),
            'pengalaman': Pengalaman.get_by_pencari(pencari['id'])
        }
    reply, mode = generate_reply(
        message,
        profile=profile,
        api_key=current_app.config.get('AI_API_KEY'),
        api_url=current_app.config.get('AI_API_URL'),
        model=current_app.config.get('AI_MODEL')
    )
    return jsonify({'reply': reply, 'mode': mode})


@pencari_bp.route('/lowongan-eksternal')
@login_required
@role_required('pencari_kerja')
def lowongan_eksternal():
    keyword = (request.args.get('q') or '').strip()
    lokasi = (request.args.get('lokasi') or '').strip()
    lowongan_list = LowonganEksternal.search(keyword=keyword, lokasi=lokasi)
    return render_template(
        'pencari/lowongan_eksternal.html',
        lowongan_list=lowongan_list,
        keyword=keyword,
        lokasi=lokasi
    )

