-- SI-PENAKERLA - skema database (hanya DDL, tanpa data).
-- Tidak menyebut nama database: pilih database lebih dulu, atau jalankan  python database/setup_db.py
-- PERINGATAN: DROP TABLE di bawah menghapus semua data pada database yang dipilih.
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS lowongan_eksternal, portofolio_kerja, keahlian_pencari, notifikasi, pengalaman_kerja, penempatan, lamaran, lowongan, perusahaan, pencari_kerja, users;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nama VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('pencari_kerja', 'perusahaan', 'admin') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pencari_kerja (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    nik VARCHAR(16),
    tanggal_lahir DATE,
    jenis_kelamin ENUM('Laki-laki', 'Perempuan'),
    alamat TEXT,
    kecamatan VARCHAR(50),
    pendidikan VARCHAR(50),
    keterampilan TEXT,
    cv VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE perusahaan (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    nama_perusahaan VARCHAR(200),
    alamat TEXT,
    kecamatan VARCHAR(50),
    email VARCHAR(100),
    telepon VARCHAR(20),
    status_verifikasi ENUM('belum_diverifikasi', 'terverifikasi', 'ditolak') DEFAULT 'belum_diverifikasi',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE lowongan (
    id INT PRIMARY KEY AUTO_INCREMENT,
    perusahaan_id INT NOT NULL,
    posisi VARCHAR(100) NOT NULL,
    deskripsi TEXT NOT NULL,
    pendidikan VARCHAR(50) NOT NULL,
    lokasi VARCHAR(100) NOT NULL,
    gaji DECIMAL(15,2),
    jumlah_kebutuhan INT NOT NULL DEFAULT 1,
    status ENUM('draft', 'aktif', 'ditutup') DEFAULT 'draft',
    deadline DATE NOT NULL,
    INDEX idx_lowongan_status_deadline (status, deadline),
    FOREIGN KEY (perusahaan_id) REFERENCES perusahaan(id) ON DELETE CASCADE
);

CREATE TABLE lamaran (
    id INT PRIMARY KEY AUTO_INCREMENT,
    lowongan_id INT NOT NULL,
    pencari_kerja_id INT NOT NULL,
    tanggal_lamaran DATE NOT NULL DEFAULT (CURRENT_DATE),
    status ENUM('diajukan', 'diproses', 'diterima', 'ditolak') DEFAULT 'diajukan',
    UNIQUE KEY unique_lamaran (lowongan_id, pencari_kerja_id),
    FOREIGN KEY (lowongan_id) REFERENCES lowongan(id) ON DELETE CASCADE,
    FOREIGN KEY (pencari_kerja_id) REFERENCES pencari_kerja(id) ON DELETE CASCADE
);

CREATE TABLE penempatan (
    id INT PRIMARY KEY AUTO_INCREMENT,
    lamaran_id INT NOT NULL UNIQUE,
    tanggal_penempatan DATE NOT NULL DEFAULT (CURRENT_DATE),
    posisi VARCHAR(100) NOT NULL,
    status ENUM('aktif', 'selesai') DEFAULT 'aktif',
    FOREIGN KEY (lamaran_id) REFERENCES lamaran(id) ON DELETE CASCADE
);

CREATE TABLE pengalaman_kerja (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pencari_kerja_id INT NOT NULL,
    nama_perusahaan VARCHAR(200) NOT NULL,
    posisi VARCHAR(100) NOT NULL,
    tahun_mulai INT NOT NULL,
    tahun_selesai INT,
    deskripsi TEXT,
    FOREIGN KEY (pencari_kerja_id) REFERENCES pencari_kerja(id) ON DELETE CASCADE
);

CREATE TABLE notifikasi (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    judul VARCHAR(200) NOT NULL,
    pesan TEXT NOT NULL,
    link VARCHAR(255),
    kategori VARCHAR(50) DEFAULT 'sistem',
    dibaca BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notif_user_dibaca (user_id, dibaca),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Keahlian terstruktur milik pencari kerja (di luar kolom keterampilan bebas yang lama).
CREATE TABLE keahlian_pencari (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pencari_kerja_id INT NOT NULL,
    nama_skill VARCHAR(100) NOT NULL,
    kategori VARCHAR(60),
    tingkat ENUM('Pemula', 'Menengah', 'Mahir', 'Ahli') NOT NULL DEFAULT 'Menengah',
    pengalaman_tahun DECIMAL(4,1) NOT NULL DEFAULT 0,
    UNIQUE KEY unique_skill_pencari (pencari_kerja_id, nama_skill),
    FOREIGN KEY (pencari_kerja_id) REFERENCES pencari_kerja(id) ON DELETE CASCADE
);

-- Portofolio proyek/karya. Tautan bersifat opsional dan diarahkan ke sumber publik.
CREATE TABLE portofolio_kerja (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pencari_kerja_id INT NOT NULL,
    judul VARCHAR(150) NOT NULL,
    deskripsi TEXT,
    tautan VARCHAR(500),
    tahun YEAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pencari_kerja_id) REFERENCES pencari_kerja(id) ON DELETE CASCADE
);

-- Lowongan hasil impor feed eksternal; tidak bercampur dengan lowongan resmi perusahaan lokal.
CREATE TABLE lowongan_eksternal (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sumber VARCHAR(200) NOT NULL,
    source_key VARCHAR(255) NOT NULL,
    source_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    posisi VARCHAR(200) NOT NULL,
    perusahaan VARCHAR(200),
    deskripsi TEXT,
    lokasi VARCHAR(200),
    url_lamaran VARCHAR(1000) NOT NULL,
    tanggal_publikasi DATETIME,
    terakhir_diambil DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_external_hash (source_hash),
    INDEX idx_external_date (tanggal_publikasi, terakhir_diambil)
);

