"""Pembangkit data dummy SI-PENAKERLA -> database/seed_dummy.sql

Data SINTETIS (bukan hasil scraping): nama perusahaan fiktif, orang fiktif, NIK berawalan 0000,
email @example.com. Hasil deterministik (seed tetap) sehingga bisa dibuat ulang dan dicantumkan di paper.
Tanggal dibuat relatif terhadap CURDATE() saat SQL dijalankan, supaya lowongan tidak cepat basi.

Prasyarat saat SQL dijalankan: schema.sql dan seed.sql sudah dimuat (ID mulai setelah data dasar).
Jalankan ulang:  python database/generate_seed_dummy.py
"""
import os
import random
import sys
from collections import Counter

RNG = random.Random(20261028)
HASH_PASSWORD123 = '$2b$12$/FHJCcahYJou/oI6WaYauOvDkojbSKhvzNqXCrSValt9vOKo5m/my'  # password123
JUMLAH_PENCARI = 140
TARGET_LOWONGAN = 260

# ID terakhir data dasar (seed.sql)
BASE = dict(users=6, perusahaan=2, pencari=3, lowongan=3, pengalaman=3, notifikasi=4)

KECAMATAN = ["Babat", "Bluluk", "Brondong", "Deket", "Glagah", "Kalitengah", "Karanggeneng", "Karangbinangun",
             "Kedungpring", "Kembangbahu", "Lamongan", "Laren", "Maduran", "Mantup", "Modo", "Ngimbang", "Paciran",
             "Pucuk", "Sambeng", "Sarirejo", "Sekaran", "Solokuro", "Sugio", "Sukodadi", "Sukorame", "Tikung", "Turi"]
KEC_BOBOT = {"Lamongan": 8, "Babat": 6, "Paciran": 4, "Brondong": 4, "Sukodadi": 3, "Deket": 3, "Kedungpring": 3}

# ---- kategori pekerjaan: keterampilan pencari + pendidikan umum ------------------------------------------
PROFIL = {
    'produksi':   dict(skill=["Operator Mesin", "Produksi", "K3", "Forklift", "Quality Control", "Perakitan", "Packing"],
                       edu=["SMA/SMK", "SMA/SMK", "D3", "D1"]),
    'teknik':     dict(skill=["Otomotif", "Mekanik", "Las", "Listrik", "Maintenance", "AutoCAD", "Hidrolik"],
                       edu=["SMA/SMK", "SMA/SMK", "D3", "D4/S1"]),
    'admin':      dict(skill=["Ms Office", "Accurate", "Pembukuan", "Administrasi", "Kearsipan", "Excel", "Surat Menyurat"],
                       edu=["SMA/SMK", "D3", "D3", "D4/S1", "D1"]),
    'sales':      dict(skill=["Penjualan", "Marketing", "Negosiasi", "Customer Service", "Presentasi", "Komunikasi"],
                       edu=["SMA/SMK", "D3", "D4/S1"]),
    'logistik':   dict(skill=["Driver", "SIM B1", "Gudang", "Forklift", "Pengiriman", "Inventori"],
                       edu=["SMP", "SMA/SMK", "SMA/SMK", "SD"]),
    'it':         dict(skill=["Python", "PHP", "MySQL", "HTML CSS", "Jaringan Komputer", "Desain Grafis", "Flask"],
                       edu=["SMA/SMK", "D3", "D4/S1", "D4/S1"]),
    'kesehatan':  dict(skill=["Keperawatan", "Administrasi Klinik", "Pelayanan Pasien", "Farmasi", "Kebidanan"],
                       edu=["D3", "D4/S1", "SMA/SMK"]),
    'pendidikan': dict(skill=["Mengajar", "Kurikulum", "Administrasi Sekolah", "Bimbingan Belajar", "Bahasa Inggris"],
                       edu=["D4/S1", "D4/S1", "S2", "D3"]),
    'perikanan':  dict(skill=["Pengolahan Ikan", "Cold Storage", "Sortir", "K3", "Ekspor", "Quality Control"],
                       edu=["SMP", "SMA/SMK", "SMA/SMK", "D3"]),
    'hospitality': dict(skill=["Front Office", "Bahasa Inggris", "Pelayanan Prima", "Housekeeping", "Kasir", "Food Beverage"],
                        edu=["SMA/SMK", "SMA/SMK", "D1", "D3"]),
    'keuangan':   dict(skill=["Akuntansi", "Perbankan", "Accurate", "Pajak", "Analisis Kredit", "Excel"],
                       edu=["D3", "D4/S1", "D4/S1", "S2"]),
    'konstruksi': dict(skill=["AutoCAD", "Pengawasan Proyek", "RAB", "Survey", "Alat Berat", "K3"],
                       edu=["SMA/SMK", "D3", "D4/S1"]),
}

# (posisi, kategori, pendidikan diterima, gaji juta (min, max), kebutuhan (min, max), tugas utama)
J = [
    ("Operator Produksi", 'produksi', ["SMA/SMK"], (2.9, 3.6), (3, 15), "mengoperasikan mesin produksi sesuai SOP dan target harian"),
    ("Operator Mesin 100% Shift Malam", 'produksi', ["SMA/SMK"], (3.2, 3.9), (2, 6), "mengoperasikan mesin pada shift malam dan melaporkan hasil produksi"),
    ("Helper Produksi", 'produksi', ["SD", "SMP", "SMA/SMK"], (2.7, 3.1), (3, 12), "membantu proses produksi dan merapikan area kerja"),
    ("Operator Packing", 'produksi', ["SMP", "SMA/SMK"], (2.7, 3.2), (4, 15), "melakukan packing dan pelabelan produk jadi"),
    ("Quality Control", 'produksi', ["SMA/SMK", "D3", "D4/S1"], (3.2, 4.6), (1, 4), "memeriksa kualitas produk dan mencatat temuan ketidaksesuaian"),
    ("Supervisor Produksi", 'produksi', ["D3", "D4/S1"], (4.8, 6.8), (1, 2), "memimpin tim operator dan mengawasi pencapaian target produksi"),
    ("Staff Gudang", 'produksi', ["SMA/SMK"], (2.9, 3.6), (1, 4), "mencatat keluar masuk barang dan menjaga akurasi stok"),
    ("Teknisi Maintenance", 'teknik', ["SMA/SMK", "D3"], (3.4, 4.9), (1, 4), "melakukan perawatan dan perbaikan mesin secara berkala"),
    ("Mekanik Otomotif", 'teknik', ["SMA/SMK", "D3"], (3.0, 4.5), (1, 5), "melakukan servis dan perbaikan kendaraan sesuai standar bengkel"),
    ("Teknisi Listrik", 'teknik', ["SMA/SMK", "D3"], (3.2, 4.6), (1, 3), "memasang dan memelihara instalasi listrik industri"),
    ("Juru Las", 'teknik', ["SMP", "SMA/SMK"], (3.0, 4.2), (2, 6), "mengerjakan pengelasan konstruksi baja sesuai gambar kerja"),
    ("Drafter AutoCAD", 'teknik', ["D3", "D4/S1"], (3.8, 5.5), (1, 2), "membuat dan merevisi gambar teknik menggunakan AutoCAD"),
    ("Staff Administrasi", 'admin', ["SMA/SMK", "D3", "D4/S1"], (3.0, 4.2), (1, 3), "menangani administrasi kantor, surat menyurat, dan kearsipan"),
    ("Admin Gudang", 'admin', ["SMA/SMK", "D3"], (3.0, 3.8), (1, 2), "menginput data stok dan membuat dokumen pengiriman"),
    ("Staff Purchasing", 'admin', ["D3", "D4/S1"], (3.8, 5.2), (1, 2), "membuat pesanan pembelian dan menegosiasikan harga dengan pemasok"),
    ("Resepsionis", 'admin', ["SMA/SMK", "D1", "D3"], (2.9, 3.6), (1, 2), "menerima tamu, mengatur telepon, dan mencatat agenda kantor"),
    ("Staff HRD", 'admin', ["D4/S1"], (4.0, 5.8), (1, 2), "mengelola data karyawan, absensi, dan proses rekrutmen"),
    ("Operator Komputer", 'admin', ["D1", "D2", "SMA/SMK"], (2.8, 3.4), (1, 3), "menginput dan merapikan data dokumen menggunakan Ms Office"),
    ("Manajer Operasional", 'admin', ["D4/S1", "S2"], (6.5, 9.5), (1, 1), "mengawasi seluruh kegiatan operasional dan menyusun laporan bulanan"),
    ("Sales Executive", 'sales', ["SMA/SMK", "D3", "D4/S1"], (3.0, 5.0), (2, 8), "mencari pelanggan baru dan mencapai target penjualan bulanan"),
    ("Marketing Executive", 'sales', ["SMA/SMK", "D3", "D4/S1"], (3.2, 5.2), (1, 4), "menyusun strategi pemasaran dan melakukan presentasi produk"),
    ("Customer Service", 'sales', ["SMA/SMK", "D3", "D4/S1"], (3.0, 4.0), (1, 4), "melayani keluhan dan pertanyaan pelanggan melalui telepon dan chat"),
    ("Sales Counter", 'sales', ["SMA/SMK", "D1"], (2.8, 3.5), (2, 6), "melayani penjualan di toko dan merapikan display produk"),
    ("Telemarketing", 'sales', ["SMA/SMK", "D1", "D3"], (2.9, 3.8), (2, 8), "menawarkan produk melalui telepon dan mencatat prospek"),
    ("Driver Truk", 'logistik', ["SMA/SMK"], (3.2, 4.4), (2, 8), "mengemudikan truk pengiriman dan memastikan barang sampai tepat waktu"),
    ("Kurir", 'logistik', ["SMP", "SMA/SMK"], (2.7, 3.5), (3, 12), "mengantar paket ke alamat tujuan dan mengumpulkan bukti terima"),
    ("Helper Gudang", 'logistik', ["SD", "SMP", "SMA/SMK"], (2.7, 3.2), (3, 10), "memuat dan membongkar barang serta menata gudang"),
    ("Operator Forklift", 'logistik', ["SMA/SMK"], (3.2, 4.0), (1, 4), "mengoperasikan forklift untuk memindahkan palet barang"),
    ("Staff Dispatcher", 'logistik', ["SMA/SMK", "D3"], (3.2, 4.2), (1, 2), "mengatur jadwal armada dan rute pengiriman"),
    ("Web Developer", 'it', ["D3", "D4/S1"], (4.2, 7.5), (1, 3), "membangun dan merawat aplikasi web menggunakan Python atau PHP dan MySQL"),
    ("IT Support", 'it', ["SMA/SMK", "D3", "D4/S1"], (3.2, 4.8), (1, 2), "menangani gangguan komputer dan jaringan komputer kantor"),
    ("Desainer Grafis", 'it', ["SMA/SMK", "D3", "D4/S1"], (3.0, 5.0), (1, 2), "membuat materi desain grafis untuk media cetak dan digital"),
    ("Admin Media Sosial", 'it', ["SMA/SMK", "D3", "D4/S1"], (2.9, 4.0), (1, 2), "mengelola konten media sosial dan membalas pesan pelanggan"),
    ("Teknisi Jaringan", 'it', ["SMA/SMK", "D3"], (3.4, 5.0), (1, 3), "memasang dan memelihara jaringan komputer pelanggan"),
    ("Perawat", 'kesehatan', ["D3", "D4/S1"], (3.5, 5.2), (1, 4), "memberikan asuhan keperawatan dan pelayanan pasien"),
    ("Bidan", 'kesehatan', ["D3", "D4/S1"], (3.6, 5.2), (1, 2), "melayani pemeriksaan ibu dan anak serta mencatat kebidanan pasien"),
    ("Admin Klinik", 'kesehatan', ["SMA/SMK", "D3"], (2.9, 3.8), (1, 2), "mengelola pendaftaran pasien dan administrasi klinik"),
    ("Asisten Apoteker", 'kesehatan', ["SMA/SMK", "D3"], (3.0, 4.0), (1, 2), "menyiapkan obat sesuai resep dan mencatat stok farmasi"),
    ("Guru Matematika", 'pendidikan', ["D4/S1", "S2"], (3.2, 5.0), (1, 2), "mengajar matematika dan menyusun perangkat pembelajaran sesuai kurikulum"),
    ("Guru Bahasa Inggris", 'pendidikan', ["D4/S1", "S2"], (3.2, 5.0), (1, 2), "mengajar bahasa Inggris dan membimbing kegiatan kelas"),
    ("Tutor Bimbingan Belajar", 'pendidikan', ["D3", "D4/S1"], (2.5, 3.8), (2, 6), "memberi bimbingan belajar kelompok kecil di sore hari"),
    ("Staff Tata Usaha Sekolah", 'pendidikan', ["SMA/SMK", "D3"], (2.7, 3.5), (1, 2), "mengurus administrasi sekolah, surat, dan data siswa"),
    ("Instruktur Ahli", 'pendidikan', ["S2", "S3"], (6.0, 9.0), (1, 1), "mengampu pelatihan tingkat lanjut dan menyusun bahan ajar"),
    ("Operator Cold Storage", 'perikanan', ["SMA/SMK"], (3.0, 3.8), (2, 6), "mengatur suhu ruang pendingin dan mengelola penyimpanan hasil laut"),
    ("Staff Pengolahan Ikan", 'perikanan', ["SMP", "SMA/SMK"], (2.8, 3.4), (4, 15), "membersihkan, memfilet, dan mengolah ikan sesuai standar mutu"),
    ("Quality Control Seafood", 'perikanan', ["D3", "D4/S1"], (3.8, 5.2), (1, 3), "memeriksa mutu hasil laut dan mengisi laporan quality control"),
    ("Staff Sortir Ikan", 'perikanan', ["SD", "SMP", "SMA/SMK"], (2.7, 3.2), (4, 12), "menyortir ikan berdasarkan ukuran dan kualitas"),
    ("Staff Ekspor Impor", 'perikanan', ["D3", "D4/S1"], (4.0, 5.8), (1, 2), "menyiapkan dokumen ekspor dan berkoordinasi dengan pihak pengiriman"),
    ("Staff Front Office", 'hospitality', ["SMA/SMK", "D1", "D3"], (2.9, 3.8), (1, 3), "melayani tamu check-in, check-out, dan informasi layanan"),
    ("Housekeeping", 'hospitality', ["SMP", "SMA/SMK"], (2.7, 3.3), (2, 8), "membersihkan kamar dan area umum sesuai standar kebersihan"),
    ("Waiter Waitress", 'hospitality', ["SMA/SMK"], (2.7, 3.4), (2, 8), "melayani pesanan tamu dan menjaga kebersihan area makan"),
    ("Kasir", 'hospitality', ["SMA/SMK", "D1"], (2.7, 3.4), (1, 4), "melayani pembayaran dan membuat laporan kas harian"),
    ("Pemandu Wisata", 'hospitality', ["SMA/SMK", "D3"], (2.8, 3.8), (1, 4), "memandu rombongan wisata dan menjelaskan atraksi dengan bahasa Inggris dasar"),
    ("Staff Akuntansi", 'keuangan', ["D3", "D4/S1"], (3.8, 5.5), (1, 2), "membuat jurnal, laporan keuangan, dan rekonsiliasi dengan Accurate"),
    ("Teller", 'keuangan', ["D3", "D4/S1"], (3.5, 4.8), (1, 3), "melayani transaksi nasabah dan membuat laporan kas teller"),
    ("Account Officer", 'keuangan', ["D4/S1"], (4.0, 6.0), (1, 3), "memasarkan produk pembiayaan dan melakukan analisis kredit awal"),
    ("Analis Kredit", 'keuangan', ["D4/S1", "S2"], (5.0, 7.5), (1, 2), "menganalisis kelayakan kredit dan menyusun rekomendasi pembiayaan"),
    ("Collector", 'keuangan', ["SMA/SMK"], (2.9, 4.0), (2, 6), "melakukan penagihan angsuran dan mencatat hasil kunjungan"),
    ("Pelaksana Lapangan", 'konstruksi', ["D3", "D4/S1"], (4.0, 6.0), (1, 3), "mengawasi pekerjaan proyek di lapangan dan pengawasan proyek harian"),
    ("Surveyor", 'konstruksi', ["SMA/SMK", "D3"], (3.2, 4.8), (1, 3), "melakukan survey pengukuran lahan dan membuat laporan hasil survey"),
    ("Estimator RAB", 'konstruksi', ["D3", "D4/S1"], (4.0, 5.8), (1, 2), "menyusun RAB proyek dan menghitung volume pekerjaan"),
    ("Operator Alat Berat", 'konstruksi', ["SMA/SMK"], (3.5, 5.0), (1, 4), "mengoperasikan alat berat proyek dengan memperhatikan K3"),
    ("Mandor", 'konstruksi', ["SMA/SMK"], (3.5, 4.8), (1, 2), "mengatur tukang dan pekerja harian di lokasi proyek"),
]

# (nama, industri, kecamatan, status verifikasi)
PERUSAHAAN = [
    ("PT Karya Baja Nusantara", 'manufaktur', "Deket", 'terverifikasi'),
    ("PT Sinar Pangan Sejahtera", 'manufaktur', "Babat", 'terverifikasi'),
    ("PT Tirta Samudra Lestari", 'perikanan', "Brondong", 'terverifikasi'),
    ("PT Bahari Cold Chain", 'perikanan', "Paciran", 'terverifikasi'),
    ("CV Mina Makmur", 'perikanan', "Brondong", 'terverifikasi'),
    ("PT Agro Tani Lamongan", 'agro', "Sukodadi", 'terverifikasi'),
    ("UD Padi Emas Jaya", 'agro', "Babat", 'terverifikasi'),
    ("PT Logistik Pantura Express", 'logistik', "Babat", 'terverifikasi'),
    ("CV Bintang Distribusi", 'retail', "Lamongan", 'terverifikasi'),
    ("PT Mekar Sari Retailindo", 'retail', "Lamongan", 'terverifikasi'),
    ("PT Wahana Wisata Bahari", 'pariwisata', "Paciran", 'terverifikasi'),
    ("PT Permai Hospitality", 'pariwisata', "Lamongan", 'terverifikasi'),
    ("PT Sehat Sentosa Medika", 'kesehatan', "Lamongan", 'terverifikasi'),
    ("Yayasan Pendidikan Insan Cendekia", 'pendidikan', "Sukodadi", 'terverifikasi'),
    ("Lembaga Kursus Cakrawala", 'pendidikan', "Babat", 'terverifikasi'),
    ("PT Digital Kreasi Lamongan", 'it', "Lamongan", 'terverifikasi'),
    ("CV Pixel Nusantara", 'it', "Lamongan", 'belum_diverifikasi'),
    ("PT Konstruksi Bumi Persada", 'konstruksi', "Lamongan", 'terverifikasi'),
    ("CV Pilar Teknik Mandiri", 'konstruksi', "Kedungpring", 'terverifikasi'),
    ("KSP Dana Sejahtera", 'keuangan', "Lamongan", 'terverifikasi'),
    ("PT BPR Arta Lamongan Mandiri", 'keuangan', "Lamongan", 'terverifikasi'),
    ("PT Otomotif Sentra Pantura", 'otomotif', "Babat", 'terverifikasi'),
    ("CV Sumber Rejeki Elektrik", 'otomotif', "Sugio", 'terverifikasi'),
    ("PT Prima Packaging Indonesia", 'manufaktur', "Kedungpring", 'terverifikasi'),
    ("PT Garment Cipta Busana", 'manufaktur', "Modo", 'terverifikasi'),
    ("CV Berkah Boga Catering", 'pariwisata', "Lamongan", 'belum_diverifikasi'),
    ("PT Semen Kapur Sentosa", 'manufaktur', "Sukodadi", 'ditolak'),
    ("PT Rejeki Mebel Jaya", 'manufaktur', "Sekaran", 'terverifikasi'),
    ("CV Mitra Properti Lamongan", 'konstruksi', "Lamongan", 'belum_diverifikasi'),
    ("PT Ritel Fashion Kita", 'retail', "Lamongan", 'belum_diverifikasi'),
]
INDUSTRI_KATEGORI = {
    'manufaktur': ['produksi', 'teknik', 'admin', 'logistik'], 'perikanan': ['perikanan', 'produksi', 'logistik', 'admin'],
    'agro': ['produksi', 'logistik', 'admin', 'sales'], 'retail': ['sales', 'logistik', 'admin', 'hospitality'],
    'logistik': ['logistik', 'admin', 'teknik'], 'pariwisata': ['hospitality', 'sales', 'admin', 'teknik'],
    'kesehatan': ['kesehatan', 'admin'], 'pendidikan': ['pendidikan', 'admin'], 'it': ['it', 'admin', 'sales'],
    'konstruksi': ['konstruksi', 'teknik', 'admin', 'logistik'], 'keuangan': ['keuangan', 'admin', 'sales'],
    'otomotif': ['teknik', 'sales', 'admin'],
}
PENGALAMAN_PT = ["PT Mitra Karya Abadi", "CV Sumber Makmur", "PT Kencana Sejati", "UD Berkah Jaya", "PT Tiga Roda Mandiri",
                 "CV Harapan Baru", "PT Surya Lestari", "Toko Sinar Terang", "PT Cahaya Timur", "CV Anugerah Utama"]
PRIA = ["Ahmad", "Budi", "Slamet", "Agus", "Dedi", "Eko", "Fajar", "Hendra", "Imam", "Joko", "Kurniawan", "Lukman", "Mahfud",
        "Nanang", "Rizky", "Samsul", "Teguh", "Wahyu", "Yusuf", "Zainal", "Bagus", "Dimas", "Faisal", "Gilang", "Hari"]
WANITA = ["Siti", "Dewi", "Rina", "Sri", "Fitri", "Ani", "Lestari", "Mega", "Nur", "Putri", "Wulan", "Yuni", "Aisyah", "Bella",
          "Citra", "Dian", "Endah", "Farida", "Indah", "Laila", "Maya", "Novi", "Rahma", "Tika", "Umi"]
BELAKANG = ["Santoso", "Wijaya", "Hidayat", "Pratama", "Saputra", "Setiawan", "Kurniawan", "Nugroho", "Rahmawati", "Utami",
            "Lestari", "Handayani", "Susanto", "Wibowo", "Hakim", "Firmansyah", "Maulana", "Ramadhan", "Purnomo", "Syahputra",
            "Anwar", "Zulkarnain", "Mustofa", "Rohman", "Cahyono", "Prasetyo", "Yulianto", "Amalia", "Safitri", "Permata"]
JALAN = ["Merdeka", "Sudirman", "Pahlawan", "Veteran", "Diponegoro", "Raya Deandels", "Basuki Rahmat", "Kartini", "Mawar", "Melati"]
DESA = ["Sidomukti", "Made", "Tanjung", "Sumberrejo", "Karangrejo", "Wonorejo", "Kebet", "Blimbing", "Banjarwati", "Tlogoanyar"]
INTRO = ["Kami membuka kesempatan bergabung sebagai", "Dibutuhkan segera", "Kami mencari kandidat untuk posisi"]
NOTE_TAMBAHAN = ["Bersedia bekerja dalam tim", "Jujur, disiplin, dan teliti", "Bersedia ditempatkan di area Lamongan",
                 "Diutamakan berdomisili di Lamongan", "Fresh graduate dipersilakan melamar", "Memiliki pengalaman lebih disukai"]


def q(v):
    """Escape string/angka/None ke literal SQL."""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v) if isinstance(v, float) else str(v)
    if isinstance(v, Raw):
        return v.sql
    assert ";" not in v, f"titik koma tidak diizinkan dalam data: {v!r}"
    return "'" + v.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"


class Raw:
    def __init__(self, sql): self.sql = sql


def hari(n):  # n hari ke belakang (n>0) / ke depan (n<0)
    return Raw(f"DATE_SUB(CURDATE(), INTERVAL {n} DAY)" if n >= 0 else f"DATE_ADD(CURDATE(), INTERVAL {-n} DAY)")


def waktu(n):
    return Raw(f"DATE_SUB(NOW(), INTERVAL {n} DAY)")


def slug(t):
    return "".join(c for c in t.lower().replace(" ", "") if c.isalnum())


def pilih_kec():
    return RNG.choices(KECAMATAN, weights=[KEC_BOBOT.get(k, 1) for k in KECAMATAN])[0]


def buat():
    out = {k: [] for k in ('users', 'perusahaan', 'pencari', 'lowongan', 'lamaran', 'penempatan', 'pengalaman', 'notifikasi')}
    uid = BASE['users']
    # ---------------- perusahaan ----------------
    perusahaan = []
    for nama, industri, kec, status in PERUSAHAAN:
        uid += 1
        pid = BASE['perusahaan'] + len(perusahaan) + 1
        email = f"hr@{slug(nama)}.example.com"
        out['users'].append((uid, nama, email, HASH_PASSWORD123, 'perusahaan', waktu(RNG.randint(60, 400))))
        out['perusahaan'].append((pid, uid, nama, f"Jl. {RNG.choice(JALAN)} No {RNG.randint(1, 99)}, Kec. {kec}", kec, email,
                                  "0322" + str(RNG.randint(100000, 999999)), status))
        perusahaan.append(dict(id=pid, uid=uid, nama=nama, industri=industri, kec=kec, status=status))

    # ---------------- lowongan ----------------
    verified = [p for p in perusahaan if p['status'] == 'terverifikasi']
    lowongan = []
    # status + offset deadline: (status, rentang offset hari dari hari ini; negatif = lewat)
    paket = ([('aktif', (3, 120))] * 187 + [('aktif', (-30, -1))] * 16 + [('ditutup', (-60, 30))] * 36 + [('draft', (10, 90))] * 21)
    RNG.shuffle(paket)
    paket = paket[:TARGET_LOWONGAN]
    # kasus batas tenggat agar Uji 3 punya data: deadline hari ini & besok (masih terbuka), kemarin (tutup)
    paket[0:3] = [('aktif', (0, 0)), ('aktif', (0, 0)), ('aktif', (1, 1))]
    paket[3:5] = [('aktif', (-1, -1)), ('aktif', (-1, -1))]
    for status, (lo, hi) in paket:
        p = RNG.choice(verified)
        kat = RNG.choice(INDUSTRI_KATEGORI[p['industri']])
        posisi, _, edu, (g1, g2), (k1, k2), tugas = RNG.choice([j for j in J if j[1] == kat])
        skills = ", ".join(RNG.sample(PROFIL[kat]['skill'], 3))
        lokasi = p['kec'] if RNG.random() < 0.75 else pilih_kec()
        if RNG.random() < 0.10:
            lokasi += ", Kab. Lamongan"
        gaji = round(RNG.uniform(g1, g2), 1) * 1_000_000
        deskripsi = (f"{RNG.choice(INTRO)} {posisi} di {p['nama']}.\n"
                     f"Tanggung jawab: {tugas}.\n"
                     f"Persyaratan:\n- Pendidikan: {', '.join(edu)}\n- Menguasai {skills}\n- {RNG.choice(NOTE_TAMBAHAN)}")
        deadline_offset = RNG.randint(lo, hi)  # hari dari sekarang (negatif = sudah lewat)
        lid = BASE['lowongan'] + len(lowongan) + 1
        row = dict(id=lid, pid=p['id'], posisi=posisi, kat=kat, edu=edu, lokasi=lokasi, status=status,
                   kebutuhan=RNG.randint(k1, k2), dl=deadline_offset, uid=p['uid'], nama_pt=p['nama'])
        lowongan.append(row)
        gaji_v = None if RNG.random() < 0.08 else float(gaji)
        out['lowongan'].append((lid, p['id'], posisi, deskripsi, ",".join(edu), lokasi, gaji_v, row['kebutuhan'], status,
                                hari(-deadline_offset)))

    # ---------------- pencari kerja ----------------
    pencari = []
    kategori_list = list(PROFIL)
    emails = set()
    for i in range(JUMLAH_PENCARI):
        uid += 1
        pria = RNG.random() < 0.55
        nama = f"{RNG.choice(PRIA if pria else WANITA)} {RNG.choice(BELAKANG)}"
        email = f"{slug(nama)}{RNG.randint(1, 99)}@example.com"
        while email in emails:
            email = f"{slug(nama)}{RNG.randint(1, 9999)}@example.com"
        emails.add(email)
        kat = RNG.choice(kategori_list)
        edu = RNG.choice(PROFIL[kat]['edu'])
        skills = ", ".join(RNG.sample(PROFIL[kat]['skill'], RNG.randint(3, 5)))
        kec = pilih_kec()
        tahun = RNG.randint(1980, 2006)
        nid = BASE['pencari'] + i + 1
        out['users'].append((uid, nama, email, HASH_PASSWORD123, 'pencari_kerja', waktu(RNG.randint(1, 300))))
        out['pencari'].append((nid, uid, "0000" + str(RNG.randint(10**11, 10**12 - 1)),
                               Raw(f"'{tahun}-{RNG.randint(1, 12):02d}-{RNG.randint(1, 28):02d}'"),
                               'Laki-laki' if pria else 'Perempuan',
                               f"Jl. {RNG.choice(JALAN)} No {RNG.randint(1, 120)}, Desa {RNG.choice(DESA)}", kec, edu, skills))
        pencari.append(dict(id=nid, uid=uid, nama=nama, kat=kat, edu=edu))

    # ---------------- pengalaman kerja ----------------
    for pc in pencari:
        if RNG.random() < 0.65:
            tahun = RNG.randint(2012, 2021)
            for _ in range(RNG.randint(1, 3)):
                selesai = None if RNG.random() < 0.2 else min(2026, tahun + RNG.randint(1, 4))
                posisi_p = RNG.choice([j[0] for j in J if j[1] == pc['kat']])
                out['pengalaman'].append((BASE['pengalaman'] + len(out['pengalaman']) + 1, pc['id'], RNG.choice(PENGALAMAN_PT),
                                          posisi_p, tahun, selesai, f"Bekerja sebagai {posisi_p} dengan tugas harian sesuai arahan atasan."))
                tahun = min(2025, (selesai or tahun) + RNG.randint(0, 1))

    # ---------------- lamaran, penempatan, notifikasi ----------------
    buka = [l for l in lowongan if l['status'] != 'draft']
    diterima_per = Counter()
    pasangan = set()
    nid_notif = BASE['notifikasi']
    status_pool = ['diajukan'] * 35 + ['diproses'] * 25 + ['diterima'] * 15 + ['ditolak'] * 25
    label = {'diproses': 'sedang diproses', 'diterima': 'DITERIMA', 'ditolak': 'ditolak'}
    for pc in pencari:
        for _ in range(RNG.randint(1, 8)):
            cocok = [l for l in buka if l['kat'] == pc['kat'] and pc['edu'] in l['edu']]
            l = RNG.choice(cocok) if cocok and RNG.random() < 0.7 else RNG.choice(buka)
            if (l['id'], pc['id']) in pasangan:
                continue
            pasangan.add((l['id'], pc['id']))
            status = RNG.choice(status_pool)
            if status == 'diterima' and diterima_per[l['id']] >= l['kebutuhan']:
                status = 'ditolak'
            if status == 'diterima':
                diterima_per[l['id']] += 1
            # tanggal lamaran <= deadline dan <= hari ini
            n_min = max(0, -l['dl'])
            n = RNG.randint(n_min, n_min + 40)
            lamid = len(out['lamaran']) + 1
            out['lamaran'].append((lamid, l['id'], pc['id'], hari(n), status))
            if status == 'diterima':
                m = max(0, n - RNG.randint(1, 7))
                out['penempatan'].append((len(out['penempatan']) + 1, lamid, hari(m), l['posisi'],
                                          'selesai' if RNG.random() < 0.15 else 'aktif'))
            # notifikasi: perusahaan menerima "Pelamar Baru"; pencari menerima status
            nid_notif += 1
            out['notifikasi'].append((nid_notif, l['uid'], 'Pelamar Baru', f"{pc['nama']} melamar posisi {l['posisi']}.",
                                      f"/perusahaan/pelamar/{l['id']}", 'lamaran', RNG.random() < 0.6, waktu(n)))
            if status != 'diajukan':
                nid_notif += 1
                out['notifikasi'].append((nid_notif, pc['uid'], f"Lamaran {label[status]}",
                                          f"Lamaran Anda untuk posisi {l['posisi']} di {l['nama_pt']} {label[status]}.",
                                          '/pencari/lamaran', 'lamaran', RNG.random() < 0.7, waktu(max(0, n - 2))))
    # notifikasi lowongan baru
    for pc in RNG.sample(pencari, 60):
        l = RNG.choice([x for x in lowongan if x['status'] == 'aktif' and x['dl'] >= 0])
        nid_notif += 1
        out['notifikasi'].append((nid_notif, pc['uid'], 'Lowongan Baru', f"{l['nama_pt']} membuka lowongan {l['posisi']} di {l['lokasi']}.",
                                  '/pencari/lowongan', 'lowongan', RNG.random() < 0.5, waktu(RNG.randint(0, 20))))
    for p in perusahaan:
        if p['status'] != 'belum_diverifikasi':
            nid_notif += 1
            ok = p['status'] == 'terverifikasi'
            out['notifikasi'].append((nid_notif, p['uid'], 'Akun Terverifikasi' if ok else 'Verifikasi Ditolak',
                                      'Akun perusahaan Anda telah diverifikasi.' if ok else 'Dokumen perusahaan belum memenuhi syarat verifikasi.',
                                      '/perusahaan/profil', 'verifikasi', True, waktu(RNG.randint(30, 200))))
    return out, lowongan


def cek(out, lowongan):
    emails = [r[2] for r in out['users']]
    assert len(emails) == len(set(emails)), "email duplikat"
    pas = [(r[1], r[2]) for r in out['lamaran']]
    assert len(pas) == len(set(pas)), "lamaran ganda"
    id_low = {l['id']: l for l in lowongan}
    for r in out['lamaran']:
        assert id_low[r[1]]['status'] != 'draft'
    assert all(l['edu'] for l in lowongan)
    ter = Counter(r[1] for r in out['lamaran'] if r[4] == 'diterima')
    assert all(v <= id_low[k]['kebutuhan'] for k, v in ter.items()), "diterima melebihi kebutuhan"
    for l in lowongan:
        pt = next(p for p in out['perusahaan'] if p[0] == l['pid'])
        assert pt[7] == 'terverifikasi', "lowongan dari perusahaan tidak terverifikasi"


KOLOM = {
    'users': "users (id, nama, email, password, role, created_at)",
    'perusahaan': "perusahaan (id, user_id, nama_perusahaan, alamat, kecamatan, email, telepon, status_verifikasi)",
    'pencari': "pencari_kerja (id, user_id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan)",
    'lowongan': "lowongan (id, perusahaan_id, posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline)",
    'lamaran': "lamaran (id, lowongan_id, pencari_kerja_id, tanggal_lamaran, status)",
    'penempatan': "penempatan (id, lamaran_id, tanggal_penempatan, posisi, status)",
    'pengalaman': "pengalaman_kerja (id, pencari_kerja_id, nama_perusahaan, posisi, tahun_mulai, tahun_selesai, deskripsi)",
    'notifikasi': "notifikasi (id, user_id, judul, pesan, link, kategori, dibaca, created_at)",
}


def tulis(out, path):
    baris = ["-- DATA DUMMY SINTETIS SI-PENAKERLA (dibangkitkan oleh database/generate_seed_dummy.py, jangan diedit manual).",
             "-- Semua nama perusahaan/orang fiktif. NIK berawalan 0000. Password semua akun: password123.",
             "-- Jalankan SETELAH schema.sql dan seed.sql. Tanggal relatif terhadap CURDATE().", ""]
    for kunci in ['users', 'perusahaan', 'pencari', 'lowongan', 'lamaran', 'penempatan', 'pengalaman', 'notifikasi']:
        rows = out[kunci]
        for i in range(0, len(rows), 100):
            baris.append(f"INSERT INTO {KOLOM[kunci]} VALUES")
            baris.append(",\n".join("(" + ", ".join(("TRUE" if v is True else "FALSE" if v is False else q(v)) for v in r) + ")"
                                    for r in rows[i:i + 100]) + ";")
            baris.append("")
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(baris))


if __name__ == "__main__":
    data, low = buat()
    cek(data, low)
    tujuan = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_dummy.sql")
    tulis(data, tujuan)
    print("Tulis", tujuan)
    for k, v in data.items():
        print(f"  {k:11s} {len(v):5d}")
    print("  status lowongan :", dict(Counter(l['status'] for l in low)))
    print("  status lamaran  :", dict(Counter(r[4] for r in data['lamaran'])))
    print("  perusahaan      :", dict(Counter(r[7] for r in data['perusahaan'])))
